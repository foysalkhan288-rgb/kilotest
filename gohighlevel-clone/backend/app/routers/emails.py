from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import DbSession, require_workspace_id
from app.models import Contact, Email
from app.services.email import send_email

router = APIRouter(
    prefix="/api/v1/emails",
    tags=["emails"],
    dependencies=[Depends(require_workspace_id)],
)


class SendEmailRequest(BaseModel):
    to_email: str
    subject: str
    html: str
    contact_id: UUID | None = None


class CampaignRequest(BaseModel):
    subject: str
    html: str
    tag: str | None = None


class EmailOut(BaseModel):
    id: UUID
    contact_id: UUID | None
    subject: str | None
    body: str | None
    status: str | None
    sent_at: Any | None

    model_config = {"from_attributes": True}


@router.post("/send")
async def send_email_route(
    payload: SendEmailRequest,
    workspace_id: UUID = Depends(require_workspace_id),
) -> dict[str, Any]:
    return await send_email(
        workspace_id=workspace_id,
        to=payload.to_email,
        subject=payload.subject,
        html=payload.html,
        contact_id=payload.contact_id,
    )


@router.get("")
async def list_emails(
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[EmailOut]:
    stmt = (
        select(Email)
        .where(Email.workspace_id == workspace_id)
        .order_by(Email.sent_at.desc().nullslast(), Email.id.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(stmt)
    emails = result.scalars().all()
    return [EmailOut.model_validate(e) for e in emails]


@router.post("/campaign")
async def send_campaign(
    payload: CampaignRequest,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> dict[str, Any]:
    stmt = select(Contact).where(Contact.workspace_id == workspace_id)
    if payload.tag:
        stmt = stmt.where(Contact.tags.contains([payload.tag]))
    result = await session.execute(stmt)
    contacts = result.scalars().all()

    sent = 0
    failed = 0
    skipped = 0
    for contact in contacts:
        if not contact.email:
            skipped += 1
            continue
        res = await send_email(
            workspace_id=workspace_id,
            to=contact.email,
            subject=payload.subject,
            html=payload.html,
            contact_id=contact.id,
        )
        if res.get("status") == "sent":
            sent += 1
        else:
            failed += 1

    return {
        "total": len(contacts),
        "sent": sent,
        "failed": failed,
        "skipped_no_email": skipped,
    }
