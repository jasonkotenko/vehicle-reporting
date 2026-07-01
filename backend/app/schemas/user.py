"""User administration schemas."""

from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import UserRole


class UserAdminResponse(BaseModel):
    id: UUID
    username: str
    display_name: str
    role: UserRole
    active: bool

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=255)
    role: UserRole = UserRole.OPERATOR


class UserUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=255)
    role: UserRole | None = None
    active: bool | None = None


class PasswordResetRequest(BaseModel):
    password: str = Field(min_length=8)
