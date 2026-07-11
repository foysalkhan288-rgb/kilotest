from __future__ import annotations

import uuid
from datetime import datetime
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import DbSession, require_workspace_id
from app.models import Contact, Opportunity, Task

# Shared workflow engine is imported guarded so a missing/broken engine never
# breaks a contacts request.
try:  # pragma: no cover - depends on runtime wiring
    from app.workflows_engine import handle_event
except Exception:  # noqa: BLE001
    handle_event = None

router = APIRouter(
    prefix="/api/v1/contacts",
    tags=["contacts"],
)

WorkspaceId = Annotated[uuid.UUID, Depends(require_workspace_id)]


# ---------------------------------------------------------------------------
# Local Pydantic schemas (do not import from shared schemas.py)
# ---------------------------------------------------------------------------
class ContactCreate(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    tags: list[str] = []
    custom_fields: dict[str, Any] = {}
    notes: str | None = None


class ContactUpdate(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None
    notes: str | None = None


class ContactOut(ContactCreate):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    created_at: datetime | None = None


class ContactTagRequest(BaseModel):
    tag: str
    action: Literal["add", "remove"] = "add"


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contact_id: uuid.UUID
    title: str | None = None
    due: datetime | None = None
    done: bool = False


class OpportunityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    contact_id: uuid.UUID | None = None
    pipeline_id: uuid.UUID
    stage_id: uuid.UUID
    name: str
    value: float | None = None
    status: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _get_contact(
    session: AsyncSession, workspace_id: uuid.UUID, contact_id: str
) -> Contact | None:
    try:
        cid = uuid.UUID(contact_id)
    except ValueError:
        return None
    stmt = select(Contact).where(
        Contact.id == cid, Contact.workspace_id == workspace_id
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _require_contact(contact: Contact | None) -> Contact:
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found"
        )
    return contact


async def _fire_created(workspace_id: uuid.UUID, contact_id: uuid.UUID) -> None:
    if handle_event is None:
        return
    try:
        await handle_event(
            "contact.created", workspace_id, {"contact_id": str(contact_id)}
        )
    except Exception:  # noqa: BLE001 - never break the request
        pass


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@router.get("")
async def list_contacts(
    session: DbSession,
    workspace_id: WorkspaceId,
    search: str | None = Query(None),
    tag: str | None = Query(None),
) -> list[ContactOut]:
    stmt = select(Contact).where(Contact.workspace_id == workspace_id)

    if search:
        like = f"%{search}%"
        stmt = stmt.where(
            or_(
                Contact.firstname.ilike(like),
                Contact.lastname.ilike(like),
                Contact.email.ilike(like),
                Contact.company.ilike(like),
                Contact.phone.ilike(like),
            )
        )

    if tag:
        stmt = stmt.where(Contact.tags.contains([tag]))

    stmt = stmt.order_by(Contact.created_at.desc())
    result = await session.execute(stmt)
    contacts = result.scalars().all()
    return [ContactOut.model_validate(c) for c in contacts]


@router.post("")
async def create_contact(
    payload: ContactCreate,
    session: DbSession,
    workspace_id: WorkspaceId,
) -> ContactOut:
    contact = Contact(workspace_id=workspace_id, **payload.model_dump())
    session.add(contact)
    await session.commit()
    await session.refresh(contact)

    await _fire_created(workspace_id, contact.id)

    return ContactOut.model_validate(contact)


@router.get("/{contact_id}")
async def get_contact(
    contact_id: str,
    session: DbSession,
    workspace_id: WorkspaceId,
) -> ContactOut:
    contact = _require_contact(await _get_contact(session, workspace_id, contact_id))
    return ContactOut.model_validate(contact)


@router.patch("/{contact_id}")
async def update_contact(
    contact_id: str,
    payload: ContactUpdate,
    session: DbSession,
    workspace_id: WorkspaceId,
) -> ContactOut:
    contact = _require_contact(await _get_contact(session, workspace_id, contact_id))

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(contact, key, value)

    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return ContactOut.model_validate(contact)


@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: str,
    session: DbSession,
    workspace_id: WorkspaceId,
) -> dict[str, str]:
    contact = _require_contact(await _get_contact(session, workspace_id, contact_id))
    await session.delete(contact)
    await session.commit()
    return {"detail": "deleted"}


@router.post("/{contact_id}/tags")
async def update_contact_tags(
    contact_id: str,
    body: ContactTagRequest,
    session: DbSession,
    workspace_id: WorkspaceId,
) -> ContactOut:
    contact = _require_contact(await _get_contact(session, workspace_id, contact_id))

    tags = list(contact.tags or [])
    if body.action == "add":
        if body.tag not in tags:
            tags.append(body.tag)
    else:
        tags = [t for t in tags if t != body.tag]

    contact.tags = tags
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return ContactOut.model_validate(contact)


@router.get("/{contact_id}/tasks")
async def list_contact_tasks(
    contact_id: str,
    session: DbSession,
    workspace_id: WorkspaceId,
) -> list[TaskOut]:
    _require_contact(await _get_contact(session, workspace_id, contact_id))
    stmt = (
        select(Task)
        .where(Task.workspace_id == workspace_id, Task.contact_id == uuid.UUID(contact_id))
        .order_by(Task.created_at.desc())
    )
    result = await session.execute(stmt)
    tasks = result.scalars().all()
    return [TaskOut.model_validate(t) for t in tasks]


@router.get("/{contact_id}/opportunities")
async def list_contact_opportunities(
    contact_id: str,
    session: DbSession,
    workspace_id: WorkspaceId,
) -> list[OpportunityOut]:
    _require_contact(await _get_contact(session, workspace_id, contact_id))
    try:
        cid = uuid.UUID(contact_id)
    except ValueError:
        return []
    stmt = (
        select(Opportunity)
        .where(Opportunity.workspace_id == workspace_id, Opportunity.contact_id == cid)
        .order_by(Opportunity.created_at.desc())
    )
    result = await session.execute(stmt)
    opportunities = result.scalars().all()
    return [OpportunityOut.model_validate(o) for o in opportunities]
