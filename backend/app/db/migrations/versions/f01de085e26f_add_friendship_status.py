"""Add friendship status

Revision ID: f01de085e26f
Revises: e8c1c3539c16
Create Date: 2026-03-20 23:31:41.479515
"""

import uuid

import sqlalchemy as sa
from alembic import op

revision = "f01de085e26f"
down_revision = "e8c1c3539c16"
branch_labels = None
depends_on = None

friendship_status = sa.Enum("PENDING", "ACCEPTED", name="friendshipstatus")


def generate_friend_code() -> str:
    return uuid.uuid4().hex[:8].upper()


def generate_unique_friend_code(existing_codes: set[str]) -> str:
    while True:
        code = generate_friend_code()
        if code not in existing_codes:
            existing_codes.add(code)
            return code


def upgrade():
    bind = op.get_bind()

    if bind.dialect.name == "postgresql":
        friendship_status.create(bind, checkfirst=True)

    with op.batch_alter_table("friendships") as batch_op:
        batch_op.add_column(
            sa.Column("status", friendship_status, nullable=True)
        )

    bind.execute(sa.text("UPDATE friendships SET status = 'PENDING' WHERE status IS NULL"))

    with op.batch_alter_table("friendships") as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=friendship_status,
            nullable=False,
        )

    existing_codes = {
        row[0]
        for row in bind.execute(
            sa.text("SELECT friend_code FROM users WHERE friend_code IS NOT NULL")
        )
    }

    user_ids = [
        row[0]
        for row in bind.execute(
            sa.text("SELECT id FROM users WHERE friend_code IS NULL")
        )
    ]

    for user_id in user_ids:
        bind.execute(
            sa.text("UPDATE users SET friend_code = :code WHERE id = :id"),
            {
                "id": user_id,
                "code": generate_unique_friend_code(existing_codes),
            },
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "friend_code",
            existing_type=sa.VARCHAR(),
            nullable=False,
        )


def downgrade():
    bind = op.get_bind()

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "friend_code",
            existing_type=sa.VARCHAR(),
            nullable=True,
        )

    with op.batch_alter_table("friendships") as batch_op:
        batch_op.drop_column("status")

    if bind.dialect.name == "postgresql":
        friendship_status.drop(bind, checkfirst=True)