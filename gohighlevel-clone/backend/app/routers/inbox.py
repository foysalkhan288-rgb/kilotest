from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import DbSession, require_workspace_id
from app.models import Contact, Email, FormSubmission

router = APIRouter(
    prefix="/api/v1",
    tags=["inbox"],
    dependencies=[Depends(require_workspace_id)],
)

_MIN_DT = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _contact_display_name(contact: Contact) -> str:
    name = f"{contact.firstname or ''} {contact.lastname or ''}".strip()
    return name or contact.email or "Unknown"


def _format_submission(data: dict | None) -> str:
    if not data:
        return "(form submission)"
    parts = [f"{k}: {v}" for k, v in data.items() if k != "form_id"]
    return "\n".join(parts) if parts else "(form submission)"


@router.get("/conversations")
async def list_conversations(
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> list[dict[str, Any]]:
    contacts = (
        await session.execute(
            select(Contact).where(Contact.workspace_id == workspace_id)
        )
    ).scalars().all()
    if not contacts:
        return []

    contact_ids = [c.id for c in contacts]
    emails = (
        await session.execute(
            select(Email).where(
                Email.workspace_id == workspace_id,
                Email.contact_id.in_(contact_ids),
            )
        )
    ).scalars().all()
    submissions = (
        await session.execute(
            select(FormSubmission).where(FormSubmission.contact_id.in_(contact_ids))
        )
    ).scalars().all()

    emails_by_contact: dict[UUID, list[Email]] = {}
    for e in emails:
        emails_by_contact.setdefault(e.contact_id, []).append(e)
    subs_by_contact: dict[UUID, list[FormSubmission]] = {}
    for s in submissions:
        subs_by_contact.setdefault(s.contact_id, []).append(s)

    conversations: list[dict[str, Any]] = []
    for c in contacts:
        ces = emails_by_contact.get(c.id, [])
        css = subs_by_contact.get(c.id, [])
        channel = "email" if ces else ("form" if css else "email")

        last_message: str | None = None
        if ces:
            latest = max(ces, key=lambda e: e.sent_at or _MIN_DT)
            last_message = latest.subject or latest.body
        if css:
            latest_sub = max(css, key=lambda s: s.created_at or _MIN_DT)
            sub_text = _format_submission(latest_sub.data)
            if last_message is None:
                last_message = sub_text

        conversations.append(
            {
                "id": str(c.id),
                "contact_id": str(c.id),
                "contact_name": _contact_display_name(c),
                "contact_email": c.email,
                "channel": channel,
                "last_message": (last_message or "")[:200],
                "has_email": bool(ces),
                "has_form": bool(css),
            }
        )
    return conversations


@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: UUID,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> dict[str, Any]:
    contact = await session.get(Contact, conversation_id)
    if contact is None or contact.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    emails = (
        await session.execute(
            select(Email).where(
                Email.workspace_id == workspace_id,
                Email.contact_id == conversation_id,
            )
        )
    ).scalars().all()
    submissions = (
        await session.execute(
            select(FormSubmission).where(FormSubmission.contact_id == conversation_id)
        )
    ).scalars().all()

    messages: list[dict[str, Any]] = []
    for e in emails:
        messages.append(
            {
                "id": str(e.id),
                "direction": "out",
                "body": e.body or "",
                "subject": e.subject,
                "created_at": e.sent_at,
            }
        )
    for s in submissions:
        messages.append(
            {
                "id": str(s.id),
                "direction": "in",
                "body": _format_submission(s.data),
                "subject": None,
                "created_at": s.created_at,
            }
        )
    messages.sort(key=lambda m: m["created_at"] or _MIN_DT)

    return {
        "id": str(conversation_id),
        "contact_id": str(contact.id),
        "contact_name": _contact_display_name(contact),
        "contact_email": contact.email,
        "messages": messages,
    }
