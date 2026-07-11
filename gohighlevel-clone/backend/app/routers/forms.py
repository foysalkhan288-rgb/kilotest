from __future__ import annotations

import re
import secrets
import uuid
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import DbSession, require_workspace_id
from app.models import ActivityLog, Contact, Form, FormSubmission
from app.workflows_engine import handle_event

router = APIRouter(prefix="/api/v1/forms", tags=["forms"])

# --------------------------------------------------------------------------- #
# Local Pydantic schemas (do not edit shared schemas.py)
# --------------------------------------------------------------------------- #
BlockType = Literal[
    "short_text",
    "long_text",
    "email",
    "phone",
    "dropdown",
    "checkbox",
    "submit",
]


class Block(BaseModel):
    type: BlockType
    label: str = ""
    required: bool = False
    options: list[str] | None = None
    placeholder: str | None = None


class FormDefinition(BaseModel):
    blocks: list[Block] = Field(default_factory=list)
    title: str | None = None
    submit_label: str | None = None


class FormCreate(BaseModel):
    name: str
    definition: FormDefinition = Field(default_factory=FormDefinition)


class FormUpdate(BaseModel):
    name: str | None = None
    definition: FormDefinition | None = None


class PublicSubmit(BaseModel):
    data: dict[str, Any] = Field(default_factory=dict)


class FormOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    definition: dict[str, Any]
    published_slug: str | None = None
    created_at: Any = None


class PublicFormOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    definition: dict[str, Any]
    published_slug: str


class SubmissionOut(BaseModel):
    id: UUID
    form_id: UUID
    contact_id: UUID | None = None
    data: dict[str, Any]
    created_at: Any = None


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _slugify(value: str) -> str:
    value = (value or "form").lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-") or "form"
    return value


async def _generate_unique_slug(
    session: AsyncSession, base: str, table
) -> str:
    for _ in range(5):
        slug = f"{_slugify(base)}-{secrets.token_hex(3)}"
        existing = await session.execute(
            select(table).where(table.published_slug == slug)
        )
        if existing.scalar_one_or_none() is None:
            return slug
    return f"{base}-{uuid.uuid4().hex[:8]}"


def _block_key(block: Block) -> str:
    return block.label.strip().lower()


def _map_contact_fields(data: dict[str, Any]) -> dict[str, Any]:
    """Extract known contact columns from a submitted field-value map."""
    mapping = {
        "email": "email",
        "firstname": "firstname",
        "first name": "firstname",
        "lastname": "lastname",
        "last name": "lastname",
        "phone": "phone",
        "company": "company",
    }
    contact_fields: dict[str, Any] = {}
    for key, value in data.items():
        norm = str(key).strip().lower()
        col = mapping.get(norm)
        if col and value not in (None, ""):
            contact_fields[col] = value
    return contact_fields


async def _get_owned_form(
    session: AsyncSession, workspace_id: UUID, form_id: str
) -> Form:
    try:
        fid = UUID(form_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid form id"
        )

    stmt = select(Form).where(
        Form.id == fid, Form.workspace_id == workspace_id
    )
    result = await session.execute(stmt)
    form = result.scalar_one_or_none()
    if form is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Form not found"
        )
    return form


# --------------------------------------------------------------------------- #
# Protected endpoints
# --------------------------------------------------------------------------- #
@router.get("", response_model=list[FormOut])
async def list_forms(
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> list[Form]:
    stmt = (
        select(Form)
        .where(Form.workspace_id == workspace_id)
        .order_by(Form.created_at.desc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=FormOut, status_code=status.HTTP_201_CREATED)
async def create_form(
    payload: FormCreate,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> Form:
    slug = await _generate_unique_slug(session, payload.name, Form)
    form = Form(
        workspace_id=workspace_id,
        name=payload.name,
        definition=payload.definition.model_dump(),
        published_slug=slug,
    )
    session.add(form)
    await session.commit()
    await session.refresh(form)
    return form


@router.get("/{form_id}", response_model=FormOut)
async def get_form(
    form_id: str,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> Form:
    return await _get_owned_form(session, workspace_id, form_id)


@router.patch("/{form_id}", response_model=FormOut)
async def update_form(
    form_id: str,
    payload: FormUpdate,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> Form:
    form = await _get_owned_form(session, workspace_id, form_id)

    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        form.name = data["name"]
    if "definition" in data and data["definition"] is not None:
        form.definition = data["definition"].model_dump()

    session.add(form)
    await session.commit()
    await session.refresh(form)
    return form


@router.delete("/{form_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_form(
    form_id: str,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> None:
    form = await _get_owned_form(session, workspace_id, form_id)
    await session.delete(form)
    await session.commit()


# --------------------------------------------------------------------------- #
# Public endpoints (NO workspace auth; derive workspace from the form row)
# --------------------------------------------------------------------------- #
@router.get("/{slug}/public", response_model=PublicFormOut)
async def public_form(slug: str, session: DbSession = None) -> Form:
    stmt = select(Form).where(Form.published_slug == slug)
    result = await session.execute(stmt)
    form = result.scalar_one_or_none()
    if form is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Form not found"
        )
    return form


@router.post("/{slug}/submit")
async def submit_form(
    slug: str, payload: PublicSubmit, session: DbSession = None
) -> dict[str, Any]:
    stmt = select(Form).where(Form.published_slug == slug)
    result = await session.execute(stmt)
    form = result.scalar_one_or_none()
    if form is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Form not found"
        )

    definition = form.definition or {}
    blocks = definition.get("blocks", [])

    # Minimal required-block validation.
    errors: dict[str, str] = {}
    for block in blocks:
        if block.get("type") == "submit":
            continue
        if block.get("required"):
            key = str(block.get("label", "")).strip().lower()
            value = payload.data.get(key)
            if value in (None, "", []):
                errors[key] = f"{block.get('label') or key} is required"
    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": errors},
        )

    contact_fields = _map_contact_fields(payload.data)
    email = contact_fields.get("email")

    contact: Contact | None = None
    if email:
        existing = await session.execute(
            select(Contact).where(
                Contact.workspace_id == form.workspace_id,
                Contact.email == email,
            )
        )
        contact = existing.scalar_one_or_none()

    if contact is None:
        contact = Contact(workspace_id=form.workspace_id, **contact_fields)
        session.add(contact)
        await session.flush()
        session.add(
            ActivityLog(
                workspace_id=form.workspace_id,
                type="contact.created",
                message=f"Contact created via form '{form.name}'",
            )
        )
    else:
        changed = False
        for col, value in contact_fields.items():
            if not getattr(contact, col, None):
                setattr(contact, col, value)
                changed = True
        if changed:
            session.add(contact)

    submission = FormSubmission(
        form_id=form.id,
        contact_id=contact.id,
        data=payload.data,
    )
    session.add(submission)
    session.add(
        ActivityLog(
            workspace_id=form.workspace_id,
            type="form.submitted",
            message=f"Form '{form.name}' submitted by {email or 'anonymous'}",
        )
    )
    await session.commit()

    # Fire automation (never raises).
    await handle_event(
        "form.submitted",
        form.workspace_id,
        {"contact_id": str(contact.id), "data": payload.data},
    )

    return {"ok": True, "submission_id": str(submission.id)}
