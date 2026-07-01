"""Admin user management routes."""

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import AdminUser
from app.db.session import get_db
from app.schemas.user import PasswordResetRequest, UserAdminResponse, UserCreate, UserUpdate
from app.services.users import UserService

router = APIRouter(prefix="/users", tags=["admin-users"])


@router.get("", response_model=list[UserAdminResponse])
def list_users(_: AdminUser, db: Session = Depends(get_db)) -> list[UserAdminResponse]:
    return UserService().list_users(db)


@router.post("", response_model=UserAdminResponse, status_code=201)
def create_user(
    payload: UserCreate,
    _: AdminUser,
    db: Session = Depends(get_db),
) -> UserAdminResponse:
    return UserService().create_user(db, payload)


@router.patch("/{user_id}", response_model=UserAdminResponse)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    current_user: AdminUser,
    db: Session = Depends(get_db),
) -> UserAdminResponse:
    return UserService().update_user(
        db,
        user_id,
        payload,
        acting_user_id=current_user.id,
    )


@router.post("/{user_id}/reset-password", response_model=UserAdminResponse)
def reset_user_password(
    user_id: UUID,
    payload: PasswordResetRequest,
    _: AdminUser,
    db: Session = Depends(get_db),
) -> UserAdminResponse:
    return UserService().reset_password(db, user_id, payload.password)
