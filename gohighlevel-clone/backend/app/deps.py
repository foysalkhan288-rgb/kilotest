import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app import db
from app.models import User
from app.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbSession = Annotated[AsyncSession, Depends(db.get_db)]

_credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: DbSession,
) -> User:
    try:
        payload = decode_token(token)
    except JWTError:
        raise _credentials_exception

    if payload.get("type") != "access":
        raise _credentials_exception

    subject = payload.get("sub")
    if subject is None:
        raise _credentials_exception

    try:
        user_id = uuid.UUID(subject)
    except (ValueError, AttributeError):
        raise _credentials_exception

    user = await session.get(User, user_id)
    if user is None:
        raise _credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_workspace_id(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> uuid.UUID:
    try:
        payload = decode_token(token)
    except JWTError:
        raise _credentials_exception

    raw = payload.get("workspace_id")
    if not raw:
        raise _credentials_exception
    try:
        return uuid.UUID(raw)
    except (ValueError, AttributeError):
        raise _credentials_exception
