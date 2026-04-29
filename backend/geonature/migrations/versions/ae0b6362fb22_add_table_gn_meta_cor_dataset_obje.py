"""add table gn_meta.cor_dataset_objectif

Revision ID: ae0b6362fb22
Revises: cb663f039774
Create Date: 2026-04-27 12:58:35.383337

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ae0b6362fb22"
down_revision = "cb663f039774"
branch_labels = None
depends_on = None


def upgrade():
    # Create "new" table
    op.create_table(
        "cor_dataset_objectif",
        sa.Column("id_dataset", sa.Integer, primary_key=True),
        sa.Column("id_nomenclature_objectif", sa.Integer, primary_key=True),
        schema="gn_meta",
    )
    op.create_foreign_key(
        "fk_cor_dataset_objectif_id_dataset",
        source_schema="gn_meta",
        source_table="cor_dataset_objectif",
        local_cols=["id_dataset"],
        referent_schema="gn_meta",
        referent_table="t_datasets",
        remote_cols=["id_dataset"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_cor_dataset_objectif_id_nomenclature_objectif",
        source_schema="gn_meta",
        source_table="cor_dataset_objectif",
        local_cols=["id_nomenclature_objectif"],
        referent_schema="ref_nomenclatures",
        referent_table="t_nomenclatures",
        remote_cols=["id_nomenclature"],
        onupdate="CASCADE",
        ondelete="NO ACTION",
    )

    # Add constraint to ensure nomenclature type is "JDD_OBJECTIFS"
    op.execute(
        """
        ALTER TABLE gn_meta.cor_dataset_objectif 
            ADD CONSTRAINT check_cor_dataset_objectif
            CHECK (ref_nomenclatures.check_nomenclature_type_by_mnemonique(id_nomenclature_objectif, 'JDD_OBJECTIFS')) NOT VALID;
        """
    )

    # Insert data from "old" field - i.e. `gn_meta.t_datasets.id_nomenclature_dataset_objectif` - to "new" table
    op.execute(
        """
        INSERT INTO gn_meta.cor_dataset_objectif (id_dataset, id_nomenclature_objectif)
        SELECT id_dataset, id_nomenclature_dataset_objectif FROM gn_meta.t_datasets;
        """
    )

    # If gn_meta.cor_dataset_objectif_archive exists, copy it to gn_meta.cor_dataset_objectif
    from sqlalchemy.engine.reflection import Inspector

    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names(schema="gn_meta")
    if "cor_dataset_objectif_archive" in tables:
        op.execute(
            """
            INSERT INTO gn_meta.cor_dataset_objectif (id_dataset, id_nomenclature_objectif)
            SELECT id_dataset, id_nomenclature_objectif
            FROM gn_meta.cor_dataset_objectif_archive
            WHERE NOT EXISTS (
                SELECT 1
                FROM gn_meta.cor_dataset_objectif
                WHERE id_dataset = gn_meta.cor_dataset_objectif_archive.id_dataset
                    AND id_nomenclature_objectif = gn_meta.cor_dataset_objectif_archive.id_nomenclature_objectif
            );
        """
        )

    # Remove the archive table possibly created through downgrade
    #   `if_exists=True` to avoid error if table actually does not exist, notably through first upgrade
    op.drop_table("cor_dataset_objectif_archive", schema="gn_meta", if_exists=True)


def downgrade():
    # Make an archive of the "new" table
    op.execute(
        """
        CREATE TABLE gn_meta.cor_dataset_objectif_archive AS TABLE gn_meta.cor_dataset_objectif;
    """
    )

    # Repopulate by arbitrarily picking the first objectif
    op.execute(
        """
        UPDATE gn_meta.t_datasets
        SET id_nomenclature_dataset_objectif = (
            SELECT id_nomenclature_objectif
            FROM gn_meta.cor_dataset_objectif
            WHERE id_dataset = gn_meta.t_datasets.id_dataset
            LIMIT 1
        );
    """
    )

    # Remove the "new" table
    op.drop_table("cor_dataset_objectif", schema="gn_meta")
