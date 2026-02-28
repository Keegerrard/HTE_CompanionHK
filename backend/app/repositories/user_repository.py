from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import RoleType
from app.models.user import User, UserPreference, UserProfile


class UserRepository:
    def __init__(self, session: Session):
        self._session = session

    def ensure_user(self, user_id: str) -> User:
        user = self._session.get(User, user_id)
        if user is None:
            user = User(user_id=user_id)
            self._session.add(user)
            self._session.flush()
        return user

    def list_preferences(self, user_id: str, role: RoleType | None = None) -> list[UserPreference]:
        stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        if role is not None:
            stmt = stmt.where((UserPreference.role == role) |
                              (UserPreference.role.is_(None)))
        stmt = stmt.order_by(UserPreference.created_at.desc())
        return list(self._session.scalars(stmt))

    def list_profiles(self, user_id: str) -> list[UserProfile]:
        stmt = (
            select(UserProfile)
            .where(UserProfile.user_id == user_id)
            .order_by(UserProfile.created_at.desc())
        )
        return list(self._session.scalars(stmt))
