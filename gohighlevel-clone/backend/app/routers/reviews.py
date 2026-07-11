from datetime import datetime, timezone
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import DbSession, require_workspace_id
from app.models import ActivityLog, Contact, Review
from app.services.email import send_email

router = APIRouter(
    prefix="/api/v1/reviews",
    tags=["reviews"],
    dependencies=[Depends(require_workspace_id)],
)


Platform = Literal["google", "facebook"]

REVIEW_LINKS: dict[str, str] = {
    "google": "https://g.page/yourbiz",
    "facebook": "https://facebook.com/yourbiz/reviews",
}


# --------------------------------------------------------------------------
# Local Pydantic schemas
# --------------------------------------------------------------------------
class ReviewRequestPayload(BaseModel):
    contact_id: UUID
    platform: Platform


class ReviewRespondPayload(BaseModel):
    body: str
    rating: int | None = None


class ReviewCreatePayload(BaseModel):
    contact_id: UUID
    platform: Platform
    rating: int | None = None
    body: str | None = None


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    contact_id: UUID
    contact_name: str | None = None
    contact_email: str | None = None
    platform: str | None = None
    rating: int | None = None
    body: str | None = None
    status: str | None = None
    requested_at: datetime | None = None
    responded_at: datetime | None = None


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _load_review(session: AsyncSession, workspace_id: UUID, review_id: UUID) -> Review:
    stmt = select(Review).where(
        Review.id == review_id,
        Review.workspace_id == workspace_id,
    )
    review = (await session.execute(stmt)).scalar_one_or_none()
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found")
    return review


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------
@router.get("")
async def list_reviews(
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> list[ReviewOut]:
    stmt = (
        select(Review, Contact)
        .join(Contact, Contact.id == Review.contact_id, isouter=True)
        .where(Review.workspace_id == workspace_id)
    )
    if status:
        stmt = stmt.where(Review.status == status)
    stmt = stmt.order_by(
        Review.requested_at.desc().nullslast(),
        Review.id.desc(),
    ).limit(limit).offset(offset)

    result = await session.execute(stmt)
    rows = result.all()

    return [
        ReviewOut(
            **ReviewOut.model_validate(review).model_dump(exclude={"contact_name", "contact_email"}),
            contact_name=_contact_display(contact),
            contact_email=contact.email if contact else None,
        )
        for review, contact in rows
    ]


def _contact_display(contact: Contact | None) -> str | None:
    if contact is None:
        return None
    name = f"{contact.firstname or ''} {contact.lastname or ''}".strip()
    return name or contact.email or None


@router.post("/request")
async def request_review(
    payload: ReviewRequestPayload,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> dict[str, Any]:
    contact = (
        await session.execute(
            select(Contact).where(
                Contact.id == payload.contact_id,
                Contact.workspace_id == workspace_id,
            )
        )
    ).scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    if not contact.email:
        raise HTTPException(status_code=400, detail="Contact has no email address")

    link = REVIEW_LINKS.get(payload.platform, REVIEW_LINKS["google"])
    name = _contact_display(contact) or "there"
    html = (
        f"<p>Hi {name},</p>"
        f"<p>We'd love to hear about your experience. "
        f"Please leave us a review on {payload.platform.title()}:</p>"
        f'<p><a href="{link}">{link}</a></p>'
        f"<p>Thank you!</p>"
    )

    await send_email(
        workspace_id=workspace_id,
        to=contact.email,
        subject="Please leave us a review",
        html=html,
        contact_id=contact.id,
    )

    review = Review(
        workspace_id=workspace_id,
        contact_id=contact.id,
        platform=payload.platform,
        status="requested",
        requested_at=_now(),
    )
    session.add(review)
    await session.commit()
    await session.refresh(review)

    session.add(
        ActivityLog(
            workspace_id=workspace_id,
            type="review_requested",
            message=f"Requested review from {name} on {payload.platform}",
        )
    )
    await session.commit()

    return {"ok": True, "review_id": str(review.id)}


@router.post("/{review_id}/respond")
async def respond_review(
    review_id: UUID,
    payload: ReviewRespondPayload,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> ReviewOut:
    review = await _load_review(session, workspace_id, review_id)

    review.status = "responded"
    review.body = payload.body
    if payload.rating is not None:
        review.rating = payload.rating
    review.responded_at = _now()

    await session.commit()
    await session.refresh(review)

    session.add(
        ActivityLog(
            workspace_id=workspace_id,
            type="review_responded",
            message=f"Responded to review {review_id}",
        )
    )
    await session.commit()

    return await _review_out(session, workspace_id, review)


@router.post("")
async def create_review(
    payload: ReviewCreatePayload,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> ReviewOut:
    contact = (
        await session.execute(
            select(Contact).where(
                Contact.id == payload.contact_id,
                Contact.workspace_id == workspace_id,
            )
        )
    ).scalar_one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    review = Review(
        workspace_id=workspace_id,
        contact_id=contact.id,
        platform=payload.platform,
        rating=payload.rating,
        body=payload.body,
        status="received",
        requested_at=_now(),
    )
    session.add(review)
    await session.commit()
    await session.refresh(review)

    return await _review_out(session, workspace_id, review)


async def _review_out(session: AsyncSession, workspace_id: UUID, review: Review) -> ReviewOut:
    contact = (
        await session.execute(
            select(Contact).where(
                Contact.id == review.contact_id,
                Contact.workspace_id == workspace_id,
            )
        )
    ).scalar_one_or_none()
    return ReviewOut(
        **ReviewOut.model_validate(review).model_dump(exclude={"contact_name", "contact_email"}),
        contact_name=_contact_display(contact),
        contact_email=contact.email if contact else None,
    )
