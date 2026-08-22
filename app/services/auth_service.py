from typing import Optional
from sqlalchemy.orm import Session
from app.core.security import hash_password, verify_password
from app.core.exceptions import UnauthorizedError, ConflictError, ValidationError
from app.repositories import UserRepository
from app.models.user import User, UserRole


class AuthService:
    def __init__(self, session: Session):
        self.session = session
        self.user_repo = UserRepository(session)

    def signup(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None,
        language_pref: str = "en",
        role: UserRole = UserRole.USER,
    ) -> User:
        existing = self.user_repo.get_by_email(email.strip().lower())
        if existing:
            raise ConflictError("Email is already registered")

        user = User(
            email=email.strip().lower(),
            password_hash=hash_password(password),
            full_name=full_name.strip() if full_name else None,
            language_pref=language_pref,
            role=role,
        )
        return self.user_repo.create(user)

    def login(self, email: str, password: str) -> User:
        user = self.user_repo.get_by_email(email.strip().lower())
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid email or password")
        return user

    def update_profile(
        self,
        user_id: str,
        full_name: Optional[str] = None,
        language_pref: Optional[str] = None,
        avatar_path: Optional[str] = None,
    ) -> User:
        user = self.user_repo.get(user_id)
        if not user:
            raise ValidationError("User not found")

        if full_name is not None:
            user.full_name = full_name.strip()
        if language_pref is not None:
            user.language_pref = language_pref
        if avatar_path is not None:
            user.avatar_path = avatar_path

        return self.user_repo.update(user)

    def change_password(self, user_id: str, current_password: str, new_password: str) -> None:
        user = self.user_repo.get(user_id)
        if not user or not verify_password(current_password, user.password_hash):
            raise UnauthorizedError("Current password is incorrect")
        if len(new_password) < 6:
            raise ValidationError("New password must be at least 6 characters")
        user.password_hash = hash_password(new_password)
        self.user_repo.update(user)

    def reset_password(self, email: str, new_password: str) -> User:
        user = self.user_repo.get_by_email(email.strip().lower())
        if not user:
            raise ValidationError("User with this email not found")
        if len(new_password) < 6:
            raise ValidationError("New password must be at least 6 characters")
        user.password_hash = hash_password(new_password)
        return self.user_repo.update(user)

    def delete_account(self, user_id: str) -> None:
        user = self.user_repo.get(user_id)
        if not user:
            raise ValidationError("User not found")
        self.user_repo.delete(user)