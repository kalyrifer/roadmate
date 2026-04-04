"""
Роутер домена Comments.
Эндпоинты:
- POST / — создание комментария
- GET /user/{user_id} — комментарии о пользователе
- PUT /{id} — обновление статуса комментария
- DELETE /{id} — удаление комментария
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.dependencies import get_current_user
from app.models.comments.model import CommentStatus
from app.models.users.model import User
from app.schemas.comments import (
    CommentCreate,
    CommentCreateResponse,
    CommentList,
    CommentStatusUpdate,
)
from app.services.comments.service import (
    CommentService,
    CommentNotFoundError,
    CannotCommentSelfError,
    ForbiddenError,
)

router = APIRouter(prefix="/comments", tags=["Comments"])


@router.post("/", response_model=CommentCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    data: CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentCreateResponse:
    """Создание комментария пользователю.
    
    Требования:
    - Нельзя оставить комментарий о себе
    """
    service = CommentService(db)
    
    try:
        comment = await service.create_comment(
            author_id=current_user.id,
            data=data,
        )
        return CommentCreateResponse.model_validate(comment)
    except CannotCommentSelfError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/user/{user_id}", response_model=CommentList)
async def get_user_comments(
    user_id: UUID,
    status_filter: Optional[CommentStatus] = Query(None, description="Фильтр по статусу"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Размер страницы"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentList:
    """Получение комментариев о пользователе.
    
    Поддерживается фильтрация по статусу:
    - published (опубликованные)
    - draft (черновик)
    - deleted (удалённые)
    """
    service = CommentService(db)
    
    return await service.get_user_comments(
        user_id=user_id,
        status_filter=status_filter,
        page=page,
        page_size=page_size,
    )


@router.put("/{comment_id}", response_model=CommentCreateResponse)
async def update_comment_status(
    comment_id: UUID,
    data: CommentStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CommentCreateResponse:
    """Обновление статуса комментария.
    
    Только автор комментария может изменить статус.
    """
    service = CommentService(db)
    
    try:
        comment = await service.update_comment_status(
            comment_id=comment_id,
            new_status=data.status,
        )
        return CommentCreateResponse.model_validate(comment)
    except CommentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Удаление комментария.
    
    Только автор комментария может удалить свой комментарий.
    """
    service = CommentService(db)
    
    try:
        await service.delete_comment(
            comment_id=comment_id,
            user_id=current_user.id,
        )
    except CommentNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ForbiddenError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )