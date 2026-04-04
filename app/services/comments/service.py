"""
Service слой для работы с комментариями (Comment).
"""
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.comments.model import CommentStatus
from app.repositories.comments.repository import CommentRepository
from app.schemas.comments import CommentCreate, CommentList


class CommentServiceError(Exception):
    """Базовый класс для ошибок сервиса комментариев."""
    pass


class CommentNotFoundError(CommentServiceError):
    """Комментарий не найден."""
    pass


class CannotCommentSelfError(CommentServiceError):
    """Нельзя оставить комментарий о себе."""
    pass


class ForbiddenError(CommentServiceError):
    """Нет прав доступа."""
    pass


class CommentService:
    """Service для работы с комментариями."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = CommentRepository(session)

    async def create_comment(
        self,
        author_id: UUID,
        data: CommentCreate,
    ) -> Comment:
        """Создание комментария."""
        if author_id == data.target_id:
            raise CannotCommentSelfError("Нельзя оставить комментарий о себе")

        comment = await self.repository.create(
            author_id=author_id,
            target_id=data.target_id,
            text=data.text,
        )

        return comment

    async def get_comment(self, comment_id: UUID):
        """Получение комментария по ID."""
        comment = await self.repository.get_by_id(comment_id)
        if not comment:
            raise CommentNotFoundError("Комментарий не найден")
        return comment

    async def get_user_comments(
        self,
        user_id: UUID,
        status_filter: Optional[CommentStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CommentList:
        """Получение списка комментариев о пользователе."""
        offset = (page - 1) * page_size
        comments, total = await self.repository.list_by_target(
            target_id=user_id,
            status=status_filter,
            limit=page_size,
            offset=offset,
        )
        
        pages = (total + page_size - 1) // page_size
        
        return CommentList(
            items=comments,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
        )

    async def update_comment_status(
        self,
        comment_id: UUID,
        new_status: CommentStatus,
    ) -> Comment:
        """Обновление статуса комментария."""
        comment = await self.repository.get_by_id(comment_id)
        if not comment:
            raise CommentNotFoundError("Комментарий не найден")

        updated_comment = await self.repository.update_status(comment_id, new_status)
        if not updated_comment:
            raise CommentNotFoundError("Комментарий не найден")

        return updated_comment

    async def delete_comment(
        self,
        comment_id: UUID,
        user_id: UUID,
    ) -> bool:
        """Удаление комментария (автор может удалить только свой комментарий)."""
        comment = await self.repository.get_by_id(comment_id)
        if not comment:
            raise CommentNotFoundError("Комментарий не найден")

        if comment.author_id != user_id:
            raise ForbiddenError("Вы можете удалить только свой комментарий")

        return await self.repository.delete(comment_id)