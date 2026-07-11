from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db
from app.deps import require_workspace_id
from app.models import Appointment, Calendar, Contact

DbSession = Depends(get_db)


# ---------------------------------------------------------------------------
# Local Pydantic schemas (do NOT edit the shared schemas.py)
# ---------------------------------------------------------------------------


class AppointmentCreate(BaseModel):
    contact_id: uuid.UUID
    start: datetime
    end: datetime | None = None
    status: str | None = "booked"


class AppointmentUpdate(BaseModel):
    start: datetime | None = None
    end: datetime | None = None
    status: str | None = None


class AppointmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    contact_id: uuid.UUID
    start: datetime | None
    end: datetime | None
    status: str | None
    created_at: datetime | None


class BookingRequest(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    email: str = Field(min_length=1, max_length=300)
    phone: str | None = None
    start: datetime


VALID_STATUSES = {
    "booked",
    "confirmed",
    "completed",
    "cancelled",
    "no_show",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    raise ValueError("Invalid datetime")


# ---------------------------------------------------------------------------
# Protected router (every query filters by workspace_id)
# ---------------------------------------------------------------------------

router = APIRouter(
    prefix="/api/v1/appointments",
    tags=["appointments"],
    dependencies=[Depends(require_workspace_id)],
)


@router.get("", response_model=list[AppointmentOut])
async def list_appointments(
    date_filter: str | None = Query(default=None, alias="date"),
    session: AsyncSession = DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> list[Appointment]:
    stmt = (
        select(Appointment)
        .where(Appointment.workspace_id == workspace_id)
        .order_by(Appointment.start.asc())
    )

    if date_filter:
        try:
            d = date.fromisoformat(date_filter)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date (use YYYY-MM-DD)")
        start = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
        end = start + timedelta(days=1)
        stmt = stmt.where(Appointment.start >= start, Appointment.start < end)

    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    payload: AppointmentCreate,
    session: AsyncSession = DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> Appointment:
    contact = await session.get(Contact, payload.contact_id)
    if contact is None or contact.workspace_id != workspace_id:
        raise HTTPException(status_code=400, detail="Invalid contact for workspace")

    appointment = Appointment(
        workspace_id=workspace_id,
        contact_id=payload.contact_id,
        start=payload.start,
        end=payload.end,
        status=payload.status or "booked",
    )
    session.add(appointment)
    await session.commit()
    await session.refresh(appointment)

    if appointment.status == "booked":
        from app.workflows_engine import handle_event

        await handle_event(
            "appointment.booked",
            workspace_id,
            {
                "contact_id": str(appointment.contact_id),
                "appointment_id": str(appointment.id),
            },
        )

    return appointment


@router.patch("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(
    appointment_id: uuid.UUID,
    payload: AppointmentUpdate,
    session: AsyncSession = DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> Appointment:
    appointment = await session.get(Appointment, appointment_id)
    if appointment is None or appointment.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Appointment not found")

    data = payload.model_dump(exclude_unset=True)
    new_status = data.get("status")

    if new_status is not None and new_status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {sorted(VALID_STATUSES)}",
        )

    for field, value in data.items():
        setattr(appointment, field, value)

    await session.commit()
    await session.refresh(appointment)

    if new_status == "no_show":
        from app.workflows_engine import handle_event

        await handle_event(
            "appointment.no_show",
            workspace_id,
            {
                "contact_id": str(appointment.contact_id),
                "appointment_id": str(appointment.id),
            },
        )

    return appointment


# ---------------------------------------------------------------------------
# Public booking router (no workspace auth; derive workspace from calendar)
# ---------------------------------------------------------------------------

public_router = APIRouter(prefix="/api/v1/book", tags=["appointments-public"])


@public_router.get("/{slug}")
async def public_booking_page(
    slug: str,
    session: AsyncSession = DbSession,
) -> dict[str, Any]:
    calendar = (
        await session.execute(
            select(Calendar).where(Calendar.public_slug == slug)
        )
    ).scalar_one_or_none()
    if calendar is None:
        raise HTTPException(status_code=404, detail="Calendar not found")

    return {
        "name": calendar.name,
        "availability": calendar.availability,
        "public_slug": calendar.public_slug,
    }


@public_router.post("/{slug}")
async def public_book(
    slug: str,
    payload: BookingRequest,
    session: AsyncSession = DbSession,
) -> dict[str, Any]:
    calendar = (
        await session.execute(
            select(Calendar).where(Calendar.public_slug == slug)
        )
    ).scalar_one_or_none()
    if calendar is None:
        raise HTTPException(status_code=404, detail="Calendar not found")

    workspace_id = calendar.workspace_id

    contact = (
        await session.execute(
            select(Contact).where(
                Contact.workspace_id == workspace_id,
                Contact.email == payload.email,
            )
        )
    ).scalar_one_or_none()

    if contact is None:
        parts = payload.name.strip().split(None, 1)
        first_name = parts[0] if parts else payload.name
        last_name = parts[1] if len(parts) > 1 else None
        contact = Contact(
            workspace_id=workspace_id,
            email=payload.email,
            firstname=first_name,
            lastname=last_name,
            phone=payload.phone,
        )
        session.add(contact)
        await session.flush()

    start = _parse_dt(payload.start)
    slot_minutes = 30
    availability = calendar.availability
    if isinstance(availability, dict):
        try:
            slot_minutes = int(availability.get("slot_minutes", 30) or 30)
        except (TypeError, ValueError):
            slot_minutes = 30
    end = start + timedelta(minutes=slot_minutes)

    appointment = Appointment(
        workspace_id=workspace_id,
        contact_id=contact.id,
        start=start,
        end=end,
        status="booked",
    )
    session.add(appointment)
    await session.flush()
    await session.commit()
    await session.refresh(appointment)

    display_first_name = contact.firstname or (
        payload.name.strip().split(None, 1)[0] if payload.name.strip() else ""
    )

    # Confirmation email (guarded import of the shared sender).
    try:
        from app.services.email import send_email

        await send_email(
            workspace_id=workspace_id,
            to=payload.email,
            subject="Appointment confirmed",
            html=(
                f"<p>Hi {display_first_name},</p>"
                f"<p>Your appointment for <strong>{calendar.name}</strong> is confirmed "
                f"for <strong>{start.isoformat()}</strong>.</p>"
            ),
            contact_id=contact.id,
        )
    except Exception:  # noqa: BLE001 - never block the booking on email failure
        pass

    # Fire workflow automation (guarded import).
    try:
        from app.workflows_engine import handle_event

        await handle_event(
            "appointment.booked",
            workspace_id,
            {
                "contact_id": str(contact.id),
                "appointment_id": str(appointment.id),
            },
        )
    except Exception:  # noqa: BLE001
        pass

    return {"ok": True, "appointment_id": str(appointment.id)}
