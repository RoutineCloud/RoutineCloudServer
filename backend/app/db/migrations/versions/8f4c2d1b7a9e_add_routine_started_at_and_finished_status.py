"""add routine_started_at and finished runtime status

Revision ID: 8f4c2d1b7a9e
Revises: 342b38619e35
Create Date: 2026-03-08 16:45:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "8f4c2d1b7a9e"
down_revision = "342b38619e35"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Handle Enum update for PostgreSQL
        op.execute("ALTER TYPE runtimestatus RENAME TO runtimestatus_old")
        sa.Enum("IDLE", "RUNNING", "PAUSED", "FINISHED", name="runtimestatus").create(bind)
        op.execute(
            "ALTER TABLE routine_runtime_states ALTER COLUMN status TYPE runtimestatus "
            "USING status::text::runtimestatus"
        )
        op.execute("DROP TYPE runtimestatus_old")
    else:
        with op.batch_alter_table("routine_runtime_states", schema=None) as batch_op:
            batch_op.alter_column(
                "status",
                existing_type=sa.Enum("IDLE", "RUNNING", "PAUSED", name="runtimestatus"),
                type_=sa.Enum("IDLE", "RUNNING", "PAUSED", "FINISHED", name="runtimestatus"),
                existing_nullable=False,
            )

    with op.batch_alter_table("routine_runtime_states", schema=None) as batch_op:
        batch_op.add_column(sa.Column("routine_started_at", sa.DateTime(), nullable=True))


def downgrade():
    with op.batch_alter_table("routine_runtime_states", schema=None) as batch_op:
        batch_op.drop_column("routine_started_at")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Handle Enum update for PostgreSQL
        op.execute("ALTER TYPE runtimestatus RENAME TO runtimestatus_old")
        sa.Enum("IDLE", "RUNNING", "PAUSED", name="runtimestatus").create(bind)
        op.execute(
            "ALTER TABLE routine_runtime_states ALTER COLUMN status TYPE runtimestatus "
            "USING CASE WHEN status::text = 'FINISHED' THEN 'IDLE'::runtimestatus "
            "ELSE status::text::runtimestatus END"
        )
        op.execute("DROP TYPE runtimestatus_old")
    else:
        with op.batch_alter_table("routine_runtime_states", schema=None) as batch_op:
            batch_op.alter_column(
                "status",
                existing_type=sa.Enum("IDLE", "RUNNING", "PAUSED", "FINISHED", name="runtimestatus"),
                type_=sa.Enum("IDLE", "RUNNING", "PAUSED", name="runtimestatus"),
                existing_nullable=False,
            )
