"""
Add reviews table

Revision ID: 003_reviews
Revises: 002_chat
Create Date: 2025-04-01 15:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by alembic.
revision: str = '003_reviews'
down_revision: Union[str, None] = '002_chat'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create reviews table."""
    # Create enum type for review status if not exists
    op.execute("""
        CREATE TYPE review_status AS ENUM ('pending', 'published', 'rejected')
    """)
    
    # === reviews ===
    op.create_table(
        'reviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trip_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('rating', sa.SmallInteger(), nullable=False),
        sa.Column('text', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'published', 'rejected', name='review_status'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['trip_id'],
            ['trips.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['author_id'],
            ['users.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['target_id'],
            ['users.id'],
            ondelete='CASCADE',
        ),
        sa.UniqueConstraint('trip_id', 'author_id', name='uq_reviews_trip_author'),
        comment='Отзывы участников поездки',
    )
    
    # Create indexes
    op.create_index('ix_reviews_trip_id', 'reviews', ['trip_id'])
    op.create_index('ix_reviews_author_id', 'reviews', ['author_id'])
    op.create_index('ix_reviews_target_id', 'reviews', ['target_id'])
    op.create_index('ix_reviews_status', 'reviews', ['status'])
    op.create_index('ix_reviews_created_at', 'reviews', ['created_at'])


def downgrade() -> None:
    """Drop reviews table."""
    # Drop indexes
    op.drop_index('ix_reviews_created_at', table_name='reviews')
    op.drop_index('ix_reviews_status', table_name='reviews')
    op.drop_index('ix_reviews_target_id', table_name='reviews')
    op.drop_index('ix_reviews_author_id', table_name='reviews')
    op.drop_index('ix_reviews_trip_id', table_name='reviews')
    
    # Drop table
    op.drop_table('reviews')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS review_status')