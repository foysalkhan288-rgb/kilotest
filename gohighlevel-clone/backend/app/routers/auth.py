import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.deps import DbSession
from app.models import User, Workspace
from app.schemas import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    Token,
)
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from jose import JWTError

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, session: DbSession) -> Token:
    existing = await session.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(email=payload.email, password_hash=hash_password(payload.password))
    session.add(user)
    await session.flush()

    workspace = Workspace(name=payload.workspace_name, owner_user_id=user.id)
    session.add(workspace)
    await session.commit()
    await session.refresh(user)
    await session.refresh(workspace)

    workspace_id = str(workspace.id)
    return Token(
        access_token=create_access_token(str(user.id), workspace_id),
        refresh_token=create_refresh_token(str(user.id), workspace_id),
        workspace_id=workspace_id,
    )


@router.post("/login", response_model=Token)
async def login(payload: LoginRequest, session: DbSession) -> Token:
    user = await session.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    workspace = await session.scalar(
        select(Workspace).where(Workspace.owner_user_id == user.id)
    )
    workspace_id = str(workspace.id) if workspace is not None else ""
    return Token(
        access_token=create_access_token(str(user.id), workspace_id),
        refresh_token=create_refresh_token(str(user.id), workspace_id),
        workspace_id=workspace_id,
    )


@router.post("/refresh", response_model=Token)
async def refresh(payload: RefreshRequest, session: DbSession) -> Token:
    try:
        data = decode_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if data.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Provided token is not a refresh token",
        )

    subject = data.get("sub")
    workspace_id = data.get("workspace_id", "")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    try:
        user = await session.get(User, uuid.UUID(subject))
    except (ValueError, AttributeError):
        user = None

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return Token(
        access_token=create_access_token(str(user.id), workspace_id),
        refresh_token=create_refresh_token(str(user.id), workspace_id),
        workspace_id=workspace_id,
    )
