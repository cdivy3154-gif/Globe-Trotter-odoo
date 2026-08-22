from argon2 import PasswordHasher

ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2id."""
    return ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against an Argon2 hash."""
    try:
        ph.verify(password_hash, password)
        return True
    except Exception:
        return False