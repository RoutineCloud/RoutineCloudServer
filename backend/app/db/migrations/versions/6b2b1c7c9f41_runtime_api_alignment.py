"""runtime api alignment

Revision ID: 6b2b1c7c9f41
Revises: e4d4558dd6e8
Create Date: 2026-03-23 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "6b2b1c7c9f41"
down_revision = "e4d4558dd6e8"
branch_labels = None
depends_on = None


old_access_level = sa.Enum("OWNER", "WRITE", "READ", name="accesslevel")
new_access_level = sa.Enum("OWNER", "START", "READ", name="accesslevel")


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Handle Enum update for PostgreSQL
        op.execute("ALTER TYPE accesslevel RENAME TO accesslevel_old")
        new_access_level.create(bind)
        op.execute(
            "ALTER TABLE routine_access ALTER COLUMN access_level TYPE accesslevel "
            "USING CASE WHEN access_level::text = 'WRITE' THEN 'START'::accesslevel "
            "ELSE access_level::text::accesslevel END"
        )
        op.execute("DROP TYPE accesslevel_old")
    else:
        op.execute(sa.text("UPDATE routine_access SET access_level = 'START' WHERE access_level = 'WRITE'"))

        with op.batch_alter_table("routine_access", schema=None) as batch_op:
            batch_op.alter_column(
                "access_level",
                existing_type=old_access_level,
                type_=new_access_level,
                existing_nullable=False,
            )


def downgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Handle Enum update for PostgreSQL
        op.execute("ALTER TYPE accesslevel RENAME TO accesslevel_old")
        old_access_level.create(bind)
        op.execute(
            "ALTER TABLE routine_access ALTER COLUMN access_level TYPE accesslevel "
            "USING CASE WHEN access_level::text = 'START' THEN 'WRITE'::accesslevel "
            "ELSE access_level::text::accesslevel END"
        )
        op.execute("DROP TYPE accesslevel_old")
    else:
        op.execute(sa.text("UPDATE routine_access SET access_level = 'WRITE' WHERE access_level = 'START'"))

        with op.batch_alter_table("routine_access", schema=None) as batch_op:
            batch_op.alter_column(
                "access_level",
                existing_type=new_access_level,
                type_=old_access_level,
                existing_nullable=False,
            )
