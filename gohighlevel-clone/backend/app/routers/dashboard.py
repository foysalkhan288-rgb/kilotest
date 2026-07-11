from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import DbSession, require_workspace_id
from app.models import ActivityLog, Appointment, Contact, Opportunity

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["dashboard"],
)

WorkspaceId = Annotated[uuid.UUID, Depends(require_workspace_id)]


class ActivityItem(BaseModel):
    id: str
    type: str | None = None
    message: str | None = None
    created_at: str | None = None


@router.get("/summary")
async def dashboard_summary(
    session: DbSession,
    workspace_id: WorkspaceId,
) -> dict[str, Any]:
    # Total contacts
    total_stmt = (
        select(func.count())
        .select_from(Contact)
        .where(Contact.workspace_id == workspace_id)
    )
    total_contacts = (await session.execute(total_stmt)).scalar_one()

    # Open pipeline value: exclude won / lost (include NULL status as open)
    open_stmt = (
        select(func.coalesce(func.sum(Opportunity.value), 0))
        .select_from(Opportunity)
        .where(
            Opportunity.workspace_id == workspace_id,
            or_(
                Opportunity.status.is_(None),
                Opportunity.status.notin_(["won", "lost"]),
            ),
        )
    )
    open_value = (await session.execute(open_stmt)).scalar_one()

    # Appointments starting today (UTC day)
    today = datetime.now(timezone.utc).date()
    start_of_day = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    end_of_day = start_of_day + timedelta(days=1)
    appt_stmt = (
        select(func.count())
        .select_from(Appointment)
        .where(
            Appointment.workspace_id == workspace_id,
            Appointment.start >= start_of_day,
            Appointment.start < end_of_day,
        )
    )
    appointments_today = (await session.execute(appt_stmt)).scalar_one()

    # Recent activity (last 10)
    activity_stmt = (
        select(ActivityLog)
        .where(ActivityLog.workspace_id == workspace_id)
        .order_by(ActivityLog.created_at.desc())
        .limit(10)
    )
    activities = (await session.execute(activity_stmt)).scalars().all()
    recent_activity = [
        ActivityItem(
            id=str(a.id),
            type=a.type,
            message=a.message,
            created_at=a.created_at.isoformat() if a.created_at else None,
        )
        for a in activities
    ]

    return {
        "total_contacts": int(total_contacts),
        "open_pipeline_value": float(open_value),
        "appointments_today": int(appointments_today),
        "recent_activity": [a.model_dump() for a in recent_activity],
    }
