"""
Add chat tables (conversations, conversation_participants, messages)

Revision ID: 002_chat
Revises: 001_trip_requests
Create Date: 2025-04-01 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by alembic.
revision: str = '002_chat'
down_revision: Union[str, None] = '001_trip_requests'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create chat tables."""
    # === conversations ===
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trip_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_message_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ['trip_id'],
            ['trips.id'],
            ondelete='CASCADE',
        ),
        comment='Чат между участниками поездки',
    )
    op.create_index('ix_conversations_trip_id', 'conversations', ['trip_id'])
    op.create_index('ix_conversations_last_message_at', 'conversations', ['last_message_at'])
    op.create_index('ix_conversations_created_at', 'conversations', ['created_at'])

    # === conversation_participants ===
    op.create_table(
        'conversation_participants',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_muted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_read_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['conversation_id'],
            ['conversations.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['user_id'],
            ['users.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['last_read_message_id'],
            ['messages.id'],
            ondelete='SET NULL',
        ),
        comment='Участник чата',
    )
    op.create_index('ix_conversation_participants_conversation_id', 'conversation_participants', ['conversation_id'])
    op.create_index('ix_conversation_participants_user_id', 'conversation_participants', ['user_id'])
    op.create_index('ix_conversation_participants_joined_at', 'conversation_participants', ['joined_at'])
    op.create_index(
        'ix_conversation_participants_unique',
        'conversation_participants',
        ['conversation_id', 'user_id'],
        unique=True,
    )

    # === messages ===
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sender_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ['conversation_id'],
            ['conversations.id'],
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(
            ['sender_id'],
            ['users.id'],
            ondelete='SET NULL',
        ),
        comment='Сообщение в чате',
    )
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_sender_id', 'messages', ['sender_id'])
    op.create_index('ix_messages_created_at', 'messages', ['created_at'])
    op.create_index('ix_messages_is_read', 'messages', ['is_read'])
    op.create_index('ix_messages_conversation_created', 'messages', ['conversation_id', 'created_at'])


def downgrade() -> None:
    """Drop chat tables."""
    # Drop messages
    op.drop_index('ix_messages_conversation_created', table_name='messages')
    op.drop_index('ix_messages_is_read', table_name='messages')
    op.drop_index('ix_messages_created_at', table_name='messages')
    op.drop_index('ix_messages_sender_id', table_name='messages')
    op.drop_index('ix_messages_conversation_id', table_name='messages')
    op.drop_table('messages')

    # Drop conversation_participants
    op.drop_index('ix_conversation_participants_unique', table_name='conversation_participants')
    op.drop_index('ix_conversation_participants_joined_at', table_name='conversation_participants')
    op.drop_index('ix_conversation_participants_user_id', table_name='conversation_participants')
    op.drop_index('ix_conversation_participants_conversation_id', table_name='conversation_participants')
    op.drop_table('conversation_participants')

    # Drop conversations
    op.drop_index('ix_conversations_created_at', table_name='conversations')
    op.drop_index('ix_conversations_last_message_at', table_name='conversations')
    op.drop_index('ix_conversations_trip_id', table_name='conversations')
    op.drop_table('conversations')