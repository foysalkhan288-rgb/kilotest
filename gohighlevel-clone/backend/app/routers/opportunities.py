import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import DbSession, require_workspace_id
from app.models import Opportunity, Pipeline, PipelineStage

router = APIRouter(
    prefix="/api/v1/opportunities",
    tags=["opportunities"],
    dependencies=[Depends(require_workspace_id)],
)


# --------------------------------------------------------------------------
# Local Pydantic schemas
# --------------------------------------------------------------------------
class OpportunityCreate(BaseModel):
    name: str
    value: float | None = None
    pipeline_id: str
    stage_id: str
    contact_id: str | None = None
    status: str | None = None


class OpportunityUpdate(BaseModel):
    name: str | None = None
    value: float | None = None
    pipeline_id: str | None = None
    stage_id: str | None = None
    contact_id: str | None = None
    status: str | None = None


class MoveOpportunity(BaseModel):
    stage_id: str


class OpportunityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    contact_id: str | None = None
    pipeline_id: str
    stage_id: str
    name: str
    value: float | None = None
    status: str | None = None
    created_at: datetime | None = None


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
async def _get_opportunity_or_404(
    session: AsyncSession, workspace_id: uuid.UUID, opportunity_id: str
) -> Opportunity:
    try:
        oid = uuid.UUID(opportunity_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )

    opp = await session.get(Opportunity, oid)
    if opp is None or opp.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Opportunity not found"
        )
    return opp


async def _resolve_stage(
    session: AsyncSession, workspace_id: uuid.UUID, pipeline_id: uuid.UUID, stage_id: str
) -> PipelineStage:
    try:
        sid = uuid.UUID(stage_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid stage_id"
        )

    stage = await session.get(PipelineStage, sid)
    if stage is None or stage.pipeline_id != pipeline_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stage does not belong to the given pipeline",
        )
    return stage


# --------------------------------------------------------------------------
# Opportunities
# --------------------------------------------------------------------------
@router.get("", response_model=list[OpportunityOut])
async def list_opportunities(
    session: DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
    pipeline_id: str | None = Query(default=None),
) -> list[Opportunity]:
    stmt = select(Opportunity).where(Opportunity.workspace_id == workspace_id)
    if pipeline_id:
        try:
            pid = uuid.UUID(pipeline_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pipeline_id"
            )
        stmt = stmt.where(Opportunity.pipeline_id == pid)
    stmt = stmt.order_by(Opportunity.created_at.desc())
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=OpportunityOut, status_code=status.HTTP_201_CREATED)
async def create_opportunity(
    payload: OpportunityCreate,
    session: DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> Opportunity:
    try:
        pid = uuid.UUID(payload.pipeline_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pipeline_id"
        )

    # Validate the pipeline belongs to the workspace.
    pipeline = await session.get(Pipeline, pid)
    if pipeline is None or pipeline.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown pipeline"
        )

    await _resolve_stage(session, workspace_id, pid, payload.stage_id)

    contact_id: uuid.UUID | None = None
    if payload.contact_id:
        try:
            contact_id = uuid.UUID(payload.contact_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid contact_id"
            )

    opp = Opportunity(
        workspace_id=workspace_id,
        contact_id=contact_id,
        pipeline_id=pid,
        stage_id=uuid.UUID(payload.stage_id),
        name=payload.name,
        value=payload.value,
        status=payload.status,
    )
    session.add(opp)
    await session.commit()
    await session.refresh(opp)
    return opp


@router.get("/{opportunity_id}", response_model=OpportunityOut)
async def get_opportunity(
    opportunity_id: str,
    session: DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> Opportunity:
    return await _get_opportunity_or_404(session, workspace_id, opportunity_id)


@router.patch("/{opportunity_id}", response_model=OpportunityOut)
async def update_opportunity(
    opportunity_id: str,
    payload: OpportunityUpdate,
    session: DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> Opportunity:
    opp = await _get_opportunity_or_404(session, workspace_id, opportunity_id)
    data = payload.model_dump(exclude_unset=True)

    target_pipeline_id = opp.pipeline_id
    if data.get("pipeline_id") is not None:
        try:
            target_pipeline_id = uuid.UUID(data["pipeline_id"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid pipeline_id"
            )
        pipeline = await session.get(Pipeline, target_pipeline_id)
        if pipeline is None or pipeline.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown pipeline"
            )
        opp.pipeline_id = target_pipeline_id

    if data.get("stage_id") is not None:
        await _resolve_stage(session, workspace_id, target_pipeline_id, data["stage_id"])
        opp.stage_id = uuid.UUID(data["stage_id"])

    if data.get("contact_id") is not None:
        try:
            opp.contact_id = uuid.UUID(data["contact_id"])
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid contact_id"
            )

    for key in ("name", "value", "status"):
        if data.get(key) is not None:
            setattr(opp, key, data[key])

    await session.commit()
    await session.refresh(opp)
    return opp


@router.post("/{opportunity_id}/move", response_model=OpportunityOut)
async def move_opportunity(
    opportunity_id: str,
    payload: MoveOpportunity,
    session: DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> Opportunity:
    opp = await _get_opportunity_or_404(session, workspace_id, opportunity_id)
    await _resolve_stage(session, workspace_id, opp.pipeline_id, payload.stage_id)
    opp.stage_id = uuid.UUID(payload.stage_id)
    await session.commit()
    await session.refresh(opp)
    return opp
