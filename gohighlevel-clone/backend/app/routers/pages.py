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
from app.models import Page

# Protected router: workspace-scoped CRUD lives under /api/v1/pages
protected_router = APIRouter(
    prefix="/api/v1/pages",
    tags=["pages"],
)

# Public router: rendering lives under /api/v1/p (no workspace auth)
public_router = APIRouter(
    prefix="/api/v1/p",
    tags=["pages-public"],
)

# Compose both into a single `router` so main.py's include_router(pages.router)
# registers both the workspace-scoped and the public routes.
router = APIRouter()
router.include_router(protected_router)
router.include_router(public_router)


# --------------------------------------------------------------------------- #
# Local Pydantic schemas (do not edit shared schemas.py)
# --------------------------------------------------------------------------- #
PageBlockType = Literal[
    "heading",
    "text",
    "image",
    "button",
    "spacer",
    "form_embed",
]


class PageBlock(BaseModel):
    type: PageBlockType
    content: str | None = None
    level: int | None = None
    url: str | None = None
    src: str | None = None
    height: int | None = None
    form_slug: str | None = None


class PageDefinition(BaseModel):
    blocks: list[PageBlock] = Field(default_factory=list)
    title: str | None = None


class PageCreate(BaseModel):
    name: str
    definition: PageDefinition = Field(default_factory=PageDefinition)


class PageUpdate(BaseModel):
    name: str | None = None
    definition: PageDefinition | None = None


class PageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    definition: dict[str, Any]
    published_slug: str | None = None


class PublicPageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    definition: dict[str, Any]
    published_slug: str


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _slugify(value: str) -> str:
    value = (value or "page").lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-") or "page"
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


async def _get_owned_page(
    session: AsyncSession, workspace_id: UUID, page_id: str
) -> Page:
    try:
        pid = UUID(page_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid page id"
        )

    stmt = select(Page).where(
        Page.id == pid, Page.workspace_id == workspace_id
    )
    result = await session.execute(stmt)
    page = result.scalar_one_or_none()
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    return page


# --------------------------------------------------------------------------- #
# Protected endpoints
# --------------------------------------------------------------------------- #
@protected_router.get("", response_model=list[PageOut])
async def list_pages(
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> list[Page]:
    stmt = (
        select(Page)
        .where(Page.workspace_id == workspace_id)
        .order_by(Page.id)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


@protected_router.post("", response_model=PageOut, status_code=status.HTTP_201_CREATED)
async def create_page(
    payload: PageCreate,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> Page:
    slug = await _generate_unique_slug(session, payload.name, Page)
    page = Page(
        workspace_id=workspace_id,
        name=payload.name,
        definition=payload.definition.model_dump(),
        published_slug=slug,
    )
    session.add(page)
    await session.commit()
    await session.refresh(page)
    return page


@protected_router.get("/{page_id}", response_model=PageOut)
async def get_page(
    page_id: str,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> Page:
    return await _get_owned_page(session, workspace_id, page_id)


@protected_router.patch("/{page_id}", response_model=PageOut)
async def update_page(
    page_id: str,
    payload: PageUpdate,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> Page:
    page = await _get_owned_page(session, workspace_id, page_id)

    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"] is not None:
        page.name = data["name"]
    if "definition" in data and data["definition"] is not None:
        page.definition = data["definition"].model_dump()

    session.add(page)
    await session.commit()
    await session.refresh(page)
    return page


@protected_router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: str,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> None:
    page = await _get_owned_page(session, workspace_id, page_id)
    await session.delete(page)
    await session.commit()


# --------------------------------------------------------------------------- #
# Public endpoint (NO workspace auth; derive workspace from the page row)
# --------------------------------------------------------------------------- #
@public_router.get("/{slug}", response_model=PublicPageOut)
async def public_page(slug: str, session: DbSession = None) -> Page:
    stmt = select(Page).where(Page.published_slug == slug)
    result = await session.execute(stmt)
    page = result.scalar_one_or_none()
    if page is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Page not found"
        )
    return page
