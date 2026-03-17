"""add routine_started_at and finished runtime status

Revision ID: 8f4c2d1b7a9e
Revises: 342b38619e35
Create Date: 2026-03-08 16:45:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8f4c2d1b7a9e"
down_revision = "342b38619e35"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("routine_runtime_states", schema=None) as batch_op:
        batch_op.add_column(sa.Column("routine_started_at", sa.DateTime(), nullable=True))
        batch_op.alter_column(
            "status",
            existing_type=sa.Enum("IDLE", "RUNNING", "PAUSED", name="runtimestatus"),
            type_=sa.Enum("IDLE", "RUNNING", "PAUSED", "FINISHED", name="runtimestatus"),
            existing_nullable=False,
        )


def downgrade():
    with op.batch_alter_table("routine_runtime_states", schema=None) as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.Enum("IDLE", "RUNNING", "PAUSED", "FINISHED", name="runtimestatus"),
            type_=sa.Enum("IDLE", "RUNNING", "PAUSED", name="runtimestatus"),
            existing_nullable=False,
        )
        batch_op.drop_column("routine_started_at")
