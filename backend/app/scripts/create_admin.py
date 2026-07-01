"""One-time bootstrap of the first admin user."""

from __future__ import annotations

import os
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import User
from app.models.enums import UserRole


def create_admin() -> None:
    password = os.environ.get("BOOTSTRAP_ADMIN_PASSWORD")
    if not password:
        print("BOOTSTRAP_ADMIN_PASSWORD is required.", file=sys.stderr)
        raise SystemExit(1)

    username = os.environ.get("BOOTSTRAP_ADMIN_USERNAME", "admin")
    display_name = os.environ.get("BOOTSTRAP_ADMIN_DISPLAY_NAME", "Administrator")

    db = SessionLocal()
    try:
        if db.scalar(select(User).limit(1)) is not None:
            print("Users already exist; bootstrap skipped.")
            return

        db.add(
            User(
                username=username,
                password_hash=hash_password(password),
                display_name=display_name,
                role=UserRole.ADMIN,
            )
        )
        db.commit()
        print(f"Admin user '{username}' created.")
    finally:
        db.close()


if __name__ == "__main__":
    create_admin()
