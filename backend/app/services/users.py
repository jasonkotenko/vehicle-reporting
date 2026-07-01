"""Application user management."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User
from app.models.enums import UserRole
from app.schemas.user import UserAdminResponse, UserCreate, UserUpdate
from app.services.admin_errors import AdminError


class UserService:
    def list_users(self, db: Session) -> list[UserAdminResponse]:
        users = db.scalars(select(User).order_by(User.username)).all()
        return [UserAdminResponse.model_validate(user) for user in users]

    def create_user(self, db: Session, payload: UserCreate) -> UserAdminResponse:
        existing = db.scalar(select(User).where(User.username == payload.username))
        if existing is not None:
            raise AdminError(
                f"Username already exists: {payload.username}",
                code="duplicate_username",
                status_code=409,
            )

        user = User(
            username=payload.username,
            password_hash=hash_password(payload.password),
            display_name=payload.display_name,
            role=payload.role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return UserAdminResponse.model_validate(user)

    def update_user(
        self,
        db: Session,
        user_id: UUID,
        payload: UserUpdate,
        *,
        acting_user_id: UUID,
    ) -> UserAdminResponse:
        user = self._get_user(db, user_id)
        updates = payload.model_dump(exclude_unset=True)
        if not updates:
            return UserAdminResponse.model_validate(user)

        if updates.get("active") is False and user_id == acting_user_id:
            raise AdminError("Cannot deactivate your own account", code="self_deactivate")

        if updates.get("role") == UserRole.OPERATOR and user.role == UserRole.ADMIN:
            self._ensure_another_active_admin(db, excluding_user_id=user_id)

        for field, value in updates.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)
        return UserAdminResponse.model_validate(user)

    def reset_password(
        self,
        db: Session,
        user_id: UUID,
        password: str,
    ) -> UserAdminResponse:
        user = self._get_user(db, user_id)
        user.password_hash = hash_password(password)
        db.commit()
        db.refresh(user)
        return UserAdminResponse.model_validate(user)

    def _get_user(self, db: Session, user_id: UUID) -> User:
        user = db.get(User, user_id)
        if user is None:
            raise AdminError("User not found", code="user_not_found", status_code=404)
        return user

    def _ensure_another_active_admin(self, db: Session, *, excluding_user_id: UUID) -> None:
        count = db.scalar(
            select(func.count())
            .select_from(User)
            .where(
                User.role == UserRole.ADMIN,
                User.active.is_(True),
                User.id != excluding_user_id,
            )
        ) or 0
        if count == 0:
            raise AdminError(
                "At least one active admin is required",
                code="last_admin",
            )
