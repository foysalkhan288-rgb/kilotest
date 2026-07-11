from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.deps import DbSession, require_workspace_id
from app.models import Workflow

router = APIRouter(
    prefix="/api/v1/workflows",
    tags=["workflows"],
    dependencies=[Depends(require_workspace_id)],
)


# --------------------------------------------------------------------------- #
# Local Pydantic schemas (do not edit shared schemas.py)
# --------------------------------------------------------------------------- #
class WorkflowCreate(BaseModel):
    name: str
    trigger: dict[str, Any] = Field(default_factory=dict)
    actions: list[dict[str, Any]] = Field(default_factory=list)
    active: bool = True


class WorkflowUpdate(BaseModel):
    name: str | None = None
    trigger: dict[str, Any] | None = None
    actions: list[dict[str, Any]] | None = None
    active: bool | None = None


class ActionOut(BaseModel):
    type: str | None = None
    # All other action-specific keys are passed through transparently.
    model_config = {"extra": "allow"}


class WorkflowOut(BaseModel):
    id: UUID
    workspace_id: UUID
    name: str
    trigger: dict[str, Any] | None = None
    actions: list[dict[str, Any]] | None = None
    active: bool

    model_config = {"from_attributes": True}


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@router.get("", response_model=list[WorkflowOut])
async def list_workflows(
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> list[Workflow]:
    stmt = (
        select(Workflow)
        .where(Workflow.workspace_id == workspace_id)
        .order_by(Workflow.name.asc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=WorkflowOut, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    payload: WorkflowCreate,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> Workflow:
    workflow = Workflow(
        workspace_id=workspace_id,
        name=payload.name,
        trigger=payload.trigger,
        actions=payload.actions,
        active=payload.active,
    )
    session.add(workflow)
    await session.commit()
    await session.refresh(workflow)
    return workflow


@router.get("/{workflow_id}", response_model=WorkflowOut)
async def get_workflow(
    workflow_id: str,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> Workflow:
    return await _get_owned_workflow(session, workspace_id, workflow_id)


@router.patch("/{workflow_id}", response_model=WorkflowOut)
async def update_workflow(
    workflow_id: str,
    payload: WorkflowUpdate,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> Workflow:
    workflow = await _get_owned_workflow(session, workspace_id, workflow_id)

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(workflow, field, value)

    session.add(workflow)
    await session.commit()
    await session.refresh(workflow)
    return workflow


@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: str,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> None:
    workflow = await _get_owned_workflow(session, workspace_id, workflow_id)
    await session.delete(workflow)
    await session.commit()


@router.post("/{workflow_id}/toggle", response_model=WorkflowOut)
async def toggle_workflow(
    workflow_id: str,
    workspace_id: UUID = Depends(require_workspace_id),
    session: DbSession = None,
) -> Workflow:
    workflow = await _get_owned_workflow(session, workspace_id, workflow_id)
    workflow.active = not workflow.active
    session.add(workflow)
    await session.commit()
    await session.refresh(workflow)
    return workflow


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
async def _get_owned_workflow(
    session: AsyncSession, workspace_id: UUID, workflow_id: str
) -> Workflow:
    try:
        wf_id = UUID(workflow_id)
    except (ValueError, AttributeError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid workflow id"
        )

    stmt = select(Workflow).where(
        Workflow.id == wf_id,
        Workflow.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    workflow = result.scalar_one_or_none()
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found"
        )
    return workflow
