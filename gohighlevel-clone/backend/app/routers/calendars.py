from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import require_workspace_id
from app.models import Calendar

DbSession = Depends(get_db)

# ---------------------------------------------------------------------------
# Local Pydantic schemas (do NOT edit the shared schemas.py)
# ---------------------------------------------------------------------------


class CalendarCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    availability: dict[str, Any] | None = None


class CalendarUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    availability: dict[str, Any] | None = None


class CalendarOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    public_slug: str | None
    availability: dict[str, Any] | None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return s or "calendar"


async def _generate_slug(session: AsyncSession, base: str) -> str:
    for _ in range(5):
        candidate = f"{_slugify(base)}-{uuid.uuid4().hex[:6]}"
        existing = (
            await session.execute(
                select(Calendar).where(Calendar.public_slug == candidate)
            )
        ).scalar_one_or_none()
        if existing is None:
            return candidate
    return f"{_slugify(base)}-{uuid.uuid4().hex}"


# ---------------------------------------------------------------------------
# Protected router (every query filters by workspace_id)
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/calendars",
    tags=["calendars"],
    dependencies=[Depends(require_workspace_id)],
)


@router.get("", response_model=list[CalendarOut])
async def list_calendars(
    session: AsyncSession = DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> list[Calendar]:
    result = await session.execute(
        select(Calendar)
        .where(Calendar.workspace_id == workspace_id)
        .order_by(Calendar.name.asc())
    )
    return list(result.scalars().all())


@router.post("", response_model=CalendarOut, status_code=status.HTTP_201_CREATED)
async def create_calendar(
    payload: CalendarCreate,
    session: AsyncSession = DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> Calendar:
    slug = await _generate_slug(session, payload.name)
    calendar = Calendar(
        workspace_id=workspace_id,
        name=payload.name,
        public_slug=slug,
        availability=payload.availability or {},
    )
    session.add(calendar)
    await session.commit()
    await session.refresh(calendar)
    return calendar


@router.get("/{calendar_id}", response_model=CalendarOut)
async def get_calendar(
    calendar_id: uuid.UUID,
    session: AsyncSession = DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> Calendar:
    calendar = await session.get(Calendar, calendar_id)
    if calendar is None or calendar.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Calendar not found")
    return calendar


@router.patch("/{calendar_id}", response_model=CalendarOut)
async def update_calendar(
    calendar_id: uuid.UUID,
    payload: CalendarUpdate,
    session: AsyncSession = DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> Calendar:
    calendar = await session.get(Calendar, calendar_id)
    if calendar is None or calendar.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Calendar not found")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(calendar, field, value)

    await session.commit()
    await session.refresh(calendar)
    return calendar


@router.delete("/{calendar_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_calendar(
    calendar_id: uuid.UUID,
    session: AsyncSession = DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> None:
    calendar = await session.get(Calendar, calendar_id)
    if calendar is None or calendar.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Calendar not found")

    await session.execute(
        delete(Calendar).where(Calendar.id == calendar_id)
    )
    await session.commit()
