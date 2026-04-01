"""
Add notifications table

Revision ID: 004_notifications
Revises: 003_reviews
Create Date: 2025-04-01 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by alembic.
revision: str = '004_notifications'
down_revision: Union[str, None] = '003_reviews'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create notifications table."""
    # Create enum type for notification type
    op.execute("""
        CREATE TYPE notification_type AS ENUM (
            'request_new',
            'request_confirmed',
            'request_rejected',
            'request_cancelled',
            'trip_cancelled',
            'trip_completed',
            'message_new',
            'system'
        )
    """)
    
    # === notifications ===
    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.Enum(
            'request_new',
            'request_confirmed',
            'request_rejected',
            'request_cancelled',
            'trip_cancelled',
            'trip_completed',
            'message_new',
            'system',
            name='notification_type'
        ), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('related_trip_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_request_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['related_trip_id'],
            ['trips.id'],
            ondelete='SET NULL',
        ),
        sa.ForeignKeyConstraint(
            ['related_request_id'],
            ['trip_requests.id'],
            ondelete='SET NULL',
        ),
        comment='Уведомления пользователей',
    )
    
    # Create indexes
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
    op.create_index('ix_notifications_type', 'notifications', ['type'])
    op.create_index('ix_notifications_related_trip_id', 'notifications', ['related_trip_id'])
    op.create_index('ix_notifications_related_request_id', 'notifications', ['related_request_id'])
    # Composite index for main query (user + unread)
    op.create_index('ix_notifications_user_unread', 'notifications', ['user_id', 'is_read'])


def downgrade() -> None:
    """Drop notifications table."""
    # Drop indexes
    op.drop_index('ix_notifications_user_unread', table_name='notifications')
    op.drop_index('ix_notifications_related_request_id', table_name='notifications')
    op.drop_index('ix_notifications_related_trip_id', table_name='notifications')
    op.drop_index('ix_notifications_type', table_name='notifications')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_index('ix_notifications_is_read', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    
    # Drop table
    op.drop_table('notifications')
    
    # Drop enum type
    op.execute('DROP TYPE IF EXISTS notification_type')
