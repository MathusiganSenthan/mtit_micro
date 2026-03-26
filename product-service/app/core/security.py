from jose import jwt
from app.core.config import settings


def decode_token(token: str) -> dict:
    """Decode and validate a JWT issued by auth-service."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])