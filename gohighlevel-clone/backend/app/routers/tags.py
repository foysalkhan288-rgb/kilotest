from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import DbSession, require_workspace_id
from app.models import Tag

router = APIRouter(
    prefix="/api/v1/tags",
    tags=["tags"],
)

WorkspaceId = Annotated[uuid.UUID, Depends(require_workspace_id)]


class TagCreate(BaseModel):
    name: str
    color: str | None = None


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    color: str | None = None


async def _get_tag(
    session: AsyncSession, workspace_id: uuid.UUID, tag_id: str
) -> Tag | None:
    try:
        tid = uuid.UUID(tag_id)
    except ValueError:
        return None
    stmt = select(Tag).where(Tag.id == tid, Tag.workspace_id == workspace_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


@router.get("")
async def list_tags(
    session: DbSession,
    workspace_id: WorkspaceId,
) -> list[TagOut]:
    stmt = select(Tag).where(Tag.workspace_id == workspace_id).order_by(Tag.name.asc())
    result = await session.execute(stmt)
    tags = result.scalars().all()
    return [TagOut.model_validate(t) for t in tags]


@router.post("")
async def create_tag(
    payload: TagCreate,
    session: DbSession,
    workspace_id: WorkspaceId,
) -> TagOut:
    tag = Tag(workspace_id=workspace_id, **payload.model_dump())
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return TagOut.model_validate(tag)


@router.delete("/{tag_id}")
async def delete_tag(
    tag_id: str,
    session: DbSession,
    workspace_id: WorkspaceId,
) -> dict[str, str]:
    tag = await _get_tag(session, workspace_id, tag_id)
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
        )
    await session.delete(tag)
    await session.commit()
    return {"detail": "deleted"}
