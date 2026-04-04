"""
Repository слой для работы с комментариями (Comment).
"""
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comments.model import Comment, CommentStatus


class CommentRepository:
    """Repository для работы с комментариями."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        author_id: UUID,
        target_id: UUID,
        text: str,
    ) -> Comment:
        """Создание нового комментария."""
        comment = Comment(
            author_id=author_id,
            target_id=target_id,
            text=text,
            status=CommentStatus.PUBLISHED,
        )
        self.session.add(comment)
        await self.session.flush()
        await self.session.refresh(comment)
        return comment

    async def get_by_id(self, comment_id: UUID) -> Optional[Comment]:
        """Получение комментария по ID."""
        result = await self.session.execute(
            select(Comment)
            .where(Comment.id == comment_id)
        )
        return result.scalar_one_or_none()

    async def list_by_target(
        self,
        target_id: UUID,
        status: Optional[CommentStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Comment], int]:
        """Получение списка комментариев для пользователя."""
        conditions = [Comment.target_id == target_id]
        if status:
            conditions.append(Comment.status == status)

        count_result = await self.session.execute(
            select(func.count(Comment.id))
            .where(and_(*conditions))
        )
        total = count_result.scalar()

        result = await self.session.execute(
            select(Comment)
            .where(and_(*conditions))
            .order_by(Comment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        comments = list(result.scalars().all())

        return comments, total

    async def list_by_author(
        self,
        author_id: UUID,
        status: Optional[CommentStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Comment], int]:
        """Получение списка комментариев от пользователя."""
        conditions = [Comment.author_id == author_id]
        if status:
            conditions.append(Comment.status == status)

        count_result = await self.session.execute(
            select(func.count(Comment.id))
            .where(and_(*conditions))
        )
        total = count_result.scalar()

        result = await self.session.execute(
            select(Comment)
            .where(and_(*conditions))
            .order_by(Comment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        comments = list(result.scalars().all())

        return comments, total

    async def update_status(self, comment_id: UUID, status: CommentStatus) -> Optional[Comment]:
        """Обновление статуса комментария."""
        comment = await self.get_by_id(comment_id)
        if not comment:
            return None

        comment.status = status
        await self.session.flush()
        await self.session.refresh(comment)
        return comment

    async def delete(self, comment_id: UUID) -> bool:
        """Удаление комментария."""
        comment = await self.get_by_id(comment_id)
        if not comment:
            return False

        await self.session.delete(comment)
        await self.session.flush()
        return True