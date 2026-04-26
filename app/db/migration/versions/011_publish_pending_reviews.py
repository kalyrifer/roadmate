"""
Auto-publish existing pending reviews

Revision ID: 011_publish_pending_reviews
Revises: 010_comments
Create Date: 2026-04-26 16:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = '011_publish_pending_reviews'
down_revision: Union[str, None] = '010_comments'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Publish all existing reviews that are stuck in pending state."""
    op.execute("""
        UPDATE reviews
        SET status = 'published',
            updated_at = now()
        WHERE status = 'pending'
    """)


def downgrade() -> None:
    """No-op: we don't revert reviews back to pending."""
    pass
