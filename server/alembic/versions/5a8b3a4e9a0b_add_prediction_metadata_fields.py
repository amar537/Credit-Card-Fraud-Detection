"""add prediction metadata fields

Revision ID: 5a8b3a4e9a0b
Revises: 81df314e49c1
Create Date: 2025-11-18 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5a8b3a4e9a0b"
down_revision = "81df314e49c1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "predictions",
        sa.Column("risk_level", sa.String(length=50), nullable=False, server_default="low"),
    )
    op.add_column(
        "predictions",
        sa.Column("feedback_notes", sa.Text(), nullable=True),
    )
    op.alter_column("predictions", "risk_level", server_default=None)


def downgrade() -> None:
    op.drop_column("predictions", "feedback_notes")
    op.drop_column("predictions", "risk_level")

