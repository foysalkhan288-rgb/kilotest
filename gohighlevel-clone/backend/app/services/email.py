"""Shared async email sender.

Sends email via Resend and records the attempt in the ``emails`` table so other
features (inbox, campaigns, workflows, calendar reminders) can reuse it.

Importable by other agents:

    from app.services.email import send_email

    result = await send_email(
        workspace_id=ws_id,
        to="customer@example.com",
        subject="Hello",
        html="<p>Hi</p>",
        contact_id=contact_id,
    )
"""
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx

from app.config import RESEND_API_KEY
from app.db import SessionLocal
from app.models import Email

logger = logging.getLogger(__name__)

RESEND_URL = "https://api.resend.com/emails"
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@yourdomain.com")


async def send_email(
    *,
    workspace_id: uuid.UUID,
    to: str,
    subject: str,
    html: str,
    contact_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Send an email via Resend and store a record in the ``emails`` table.

    Returns a dict with ``id``, ``status`` ('sent'/'failed'), ``to`` and an
    optional ``provider_response``. Never raises on missing API key or network
    failure -- the row is stored with status 'failed' instead.
    """
    status = "failed"
    provider_response: dict[str, Any] | None = None

    if RESEND_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    RESEND_URL,
                    headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
                    json={
                        "from": EMAIL_FROM,
                        "to": [to],
                        "subject": subject,
                        "html": html,
                    },
                )
                if resp.content:
                    try:
                        provider_response = resp.json()
                    except ValueError:
                        provider_response = {"text": resp.text}
                if 200 <= resp.status_code < 300:
                    status = "sent"
                else:
                    logger.error("Resend send failed (%s): %s", resp.status_code, provider_response)
        except Exception as exc:  # pragma: no cover - network errors must not crash
            logger.exception("Resend request error: %s", exc)
            provider_response = {"error": str(exc)}
    else:
        logger.warning("RESEND_API_KEY not configured; storing email as 'failed'")

    sent_at = datetime.now(timezone.utc) if status == "sent" else None

    async with SessionLocal() as session:
        row = Email(
            workspace_id=workspace_id,
            contact_id=contact_id,
            subject=subject,
            body=html,
            status=status,
            sent_at=sent_at,
        )
        session.add(row)
        await session.commit()
        await session.refresh(row)
        record_id = str(row.id)

    return {
        "id": record_id,
        "status": status,
        "to": to,
        "provider_response": provider_response,
    }
