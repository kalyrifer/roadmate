"""
Add comments table

Revision ID: 010_comments
Revises: 009_create_enum_types
Create Date: 2026-04-04 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = '010_comments'
down_revision: Union[str, None] = '009_create_enum_types'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create comments table."""
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE comment_status AS ENUM ('draft', 'published', 'deleted');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            author_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            target_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            text TEXT NOT NULL,
            status comment_status NOT NULL DEFAULT 'published',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    
    op.execute("CREATE INDEX IF NOT EXISTS ix_comments_author_id ON comments (author_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_comments_target_id ON comments (target_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_comments_status ON comments (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_comments_created_at ON comments (created_at)")


def downgrade() -> None:
    """Drop comments table."""
    op.execute("DROP TABLE IF EXISTS comments CASCADE")
    op.execute("DROP TYPE IF EXISTS comment_status")