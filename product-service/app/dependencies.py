from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError

from app.core.config import settings
from app.core.security import decode_token

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise credentials_error

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise credentials_error

    if payload.get("type") != "access":
        raise credentials_error

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise credentials_error

    return user_id


def get_current_user_or_internal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    x_internal_token: str | None = Header(default=None),
) -> str:
    """
    Accept either a valid user JWT or a trusted internal token.
    Used for service-to-service calls such as order stock updates.
    """
    if x_internal_token and x_internal_token == settings.INTERNAL_API_KEY:
        return "internal-service"

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return get_current_user_id(credentials)