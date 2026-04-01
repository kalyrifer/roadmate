"""Create trip_requests table

Revision ID: 001
Revises: 
Create Date: 2026-04-01 17:59:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Создаем enum тип для статусов заявок
    op.execute("""
        CREATE TYPE trip_request_status AS ENUM (
            'pending',
            'confirmed',
            'rejected',
            'cancelled'
        )
    """)
    
    # Создаем таблицу trip_requests
    op.create_table(
        'trip_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('trip_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('passenger_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('seats_requested', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'confirmed', 'rejected', 'cancelled', name='trip_request_status'), nullable=False, server_default='pending'),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_reason', sa.Text(), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_by', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Создаем индексы
    op.create_index('ix_trip_requests_id', 'trip_requests', ['id'])
    op.create_index('ix_trip_requests_trip_id', 'trip_requests', ['trip_id'])
    op.create_index('ix_trip_requests_passenger_id', 'trip_requests', ['passenger_id'])
    op.create_index('ix_trip_requests_status', 'trip_requests', ['status'])
    op.create_index('ix_trip_requests_deleted_at', 'trip_requests', ['deleted_at'])
    op.create_index('ix_trip_requests_created_at', 'trip_requests', ['created_at'])
    
    # Уникальный индекс: один пассажир - одна активная заявка на поездку
    op.create_index(
        'ix_trip_requests_unique_active',
        'trip_requests',
        ['trip_id', 'passenger_id'],
        unique=True,
        postgresql_where=sa.text("status = 'pending'")
    )
    
    # Внешние ключи
    op.create_foreign_key(
        'fk_trip_requests_trip_id',
        'trip_requests', 'trips',
        ['trip_id'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_foreign_key(
        'fk_trip_requests_passenger_id',
        'trip_requests', 'users',
        ['passenger_id'], ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Удаляем внешние ключи
    op.drop_constraint('fk_trip_requests_passenger_id', 'trip_requests', type_='foreignkey')
    op.drop_constraint('fk_trip_requests_trip_id', 'trip_requests', type_='foreignkey')
    
    # Удаляем индексы
    op.drop_index('ix_trip_requests_unique_active', 'trip_requests')
    op.drop_index('ix_trip_requests_created_at', 'trip_requests')
    op.drop_index('ix_trip_requests_deleted_at', 'trip_requests')
    op.drop_index('ix_trip_requests_status', 'trip_requests')
    op.drop_index('ix_trip_requests_passenger_id', 'trip_requests')
    op.drop_index('ix_trip_requests_trip_id', 'trip_requests')
    op.drop_index('ix_trip_requests_id', 'trip_requests')
    
    # Удаляем таблицу
    op.drop_table('trip_requests')
    
    # Удаляем enum тип
    op.execute("DROP TYPE IF EXISTS trip_request_status")