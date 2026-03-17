"""add pause tracking to routine runtime state

Revision ID: 4d2a9f31bc10
Revises: 8f4c2d1b7a9e
Create Date: 2026-03-08 18:45:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "4d2a9f31bc10"
down_revision = "8f4c2d1b7a9e"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("routine_runtime_states", schema=None) as batch_op:
        batch_op.add_column(sa.Column("paused_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("pause_duration", sa.Integer(), nullable=False, server_default="0"))

    with op.batch_alter_table("routine_runtime_states", schema=None) as batch_op:
        batch_op.alter_column("pause_duration", server_default=None)


def downgrade():
    with op.batch_alter_table("routine_runtime_states", schema=None) as batch_op:
        batch_op.drop_column("pause_duration")
        batch_op.drop_column("paused_at")
