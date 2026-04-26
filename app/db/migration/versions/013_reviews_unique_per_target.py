"""
Allow each user to leave one review per target on a trip
(replace uq_reviews_trip_author with uq_reviews_trip_author_target)

Revision ID: 013_reviews_unique_per_target
Revises: 012_recalc_user_ratings
Create Date: 2026-04-26 17:50:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = '013_reviews_unique_per_target'
down_revision: Union[str, None] = '012_recalc_user_ratings'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE reviews DROP CONSTRAINT IF EXISTS uq_reviews_trip_author")
    op.execute(
        "ALTER TABLE reviews ADD CONSTRAINT uq_reviews_trip_author_target "
        "UNIQUE (trip_id, author_id, target_id)"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE reviews DROP CONSTRAINT IF EXISTS uq_reviews_trip_author_target"
    )
    op.execute(
        "ALTER TABLE reviews ADD CONSTRAINT uq_reviews_trip_author "
        "UNIQUE (trip_id, author_id)"
    )
