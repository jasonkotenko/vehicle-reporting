"""API dependency helpers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User
from app.models.enums import UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def verify_ingest_api_key(x_ingest_key: str = Header(..., alias="X-Ingest-Key")) -> None:
    if x_ingest_key != get_settings().ingest_api_key:
        raise HTTPException(status_code=401, detail="Invalid ingest API key")


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        user_id = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid access token") from exc

    user = db.get(User, user_id)
    if user is None or not user.active:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


def require_admin(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    settings = get_settings()
    if settings.dev_auth_bypass:
        admin = db.scalar(
            select(User).where(User.role == UserRole.ADMIN, User.active.is_(True)).limit(1)
        )
        if admin is None:
            raise HTTPException(status_code=503, detail="No active admin user available")
        return admin

    user = get_current_user(db=db, credentials=credentials)
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


def require_operator(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> User:
    settings = get_settings()
    if settings.dev_auth_bypass:
        user = db.scalar(select(User).where(User.active.is_(True)).limit(1))
        if user is None:
            raise HTTPException(status_code=503, detail="No active user available")
        return user

    user = get_current_user(db=db, credentials=credentials)
    if user.role not in {UserRole.OPERATOR, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Operator access required")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_admin)]
OperatorUser = Annotated[User, Depends(require_operator)]
