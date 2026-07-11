import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import DbSession, require_workspace_id
from app.models import Opportunity, Pipeline, PipelineStage

router = APIRouter(
    prefix="/api/v1/pipelines",
    tags=["pipelines"],
    dependencies=[Depends(require_workspace_id)],
)


# --------------------------------------------------------------------------
# Local Pydantic schemas
# --------------------------------------------------------------------------
class PipelineStageBase(BaseModel):
    name: str
    position: int = 0


class PipelineStageCreate(PipelineStageBase):
    pass


class PipelineStageUpdate(BaseModel):
    name: str | None = None
    position: int | None = None


class PipelineStageOut(PipelineStageBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    pipeline_id: str


class PipelineCreate(BaseModel):
    name: str


class PipelineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    name: str

    stages: list[PipelineStageOut] = []


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
async def _get_pipeline_or_404(
    session: AsyncSession, workspace_id: uuid.UUID, pipeline_id: str
) -> Pipeline:
    try:
        pid = uuid.UUID(pipeline_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")

    pipeline = await session.get(Pipeline, pid)
    if pipeline is None or pipeline.workspace_id != workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")
    return pipeline


async def _get_stage_or_404(
    session: AsyncSession, pipeline_id: str, stage_id: str
) -> PipelineStage:
    try:
        sid = uuid.UUID(stage_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")

    stage = await session.get(PipelineStage, sid)
    if stage is None or str(stage.pipeline_id) != str(pipeline_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stage not found")
    return stage


# --------------------------------------------------------------------------
# Pipelines
# --------------------------------------------------------------------------
@router.get("", response_model=list[PipelineOut])
async def list_pipelines(
    session: DbSession, workspace_id: uuid.UUID = Depends(require_workspace_id)
) -> list[Pipeline]:
    result = await session.execute(
        select(Pipeline)
        .where(Pipeline.workspace_id == workspace_id)
        .order_by(Pipeline.name)
    )
    pipelines = result.scalars().all()

    out: list[Pipeline] = []
    for pipeline in pipelines:
        stages_result = await session.execute(
            select(PipelineStage)
            .where(PipelineStage.pipeline_id == pipeline.id)
            .order_by(PipelineStage.position)
        )
        pipeline.stages = list(stages_result.scalars().all())  # type: ignore[attr-defined]
        out.append(pipeline)
    return out


@router.post("", response_model=PipelineOut, status_code=status.HTTP_201_CREATED)
async def create_pipeline(
    payload: PipelineCreate,
    session: DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> Pipeline:
    pipeline = Pipeline(workspace_id=workspace_id, name=payload.name)
    session.add(pipeline)
    await session.commit()
    await session.refresh(pipeline)
    pipeline.stages = []  # type: ignore[attr-defined]
    return pipeline


@router.get("/{pipeline_id}", response_model=PipelineOut)
async def get_pipeline(
    pipeline_id: str,
    session: DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> Pipeline:
    pipeline = await _get_pipeline_or_404(session, workspace_id, pipeline_id)
    stages_result = await session.execute(
        select(PipelineStage)
        .where(PipelineStage.pipeline_id == pipeline.id)
        .order_by(PipelineStage.position)
    )
    pipeline.stages = list(stages_result.scalars().all())  # type: ignore[attr-defined]
    return pipeline


# --------------------------------------------------------------------------
# Stages
# --------------------------------------------------------------------------
@router.get("/{pipeline_id}/stages", response_model=list[PipelineStageOut])
async def list_stages(
    pipeline_id: str,
    session: DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> list[PipelineStage]:
    await _get_pipeline_or_404(session, workspace_id, pipeline_id)
    result = await session.execute(
        select(PipelineStage)
        .where(PipelineStage.pipeline_id == pipeline_id)
        .order_by(PipelineStage.position)
    )
    return list(result.scalars().all())


@router.post(
    "/{pipeline_id}/stages",
    response_model=PipelineStageOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_stage(
    pipeline_id: str,
    payload: PipelineStageCreate,
    session: DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> PipelineStage:
    await _get_pipeline_or_404(session, workspace_id, pipeline_id)
    try:
        pid = uuid.UUID(pipeline_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found")

    stage = PipelineStage(
        pipeline_id=pid, name=payload.name, position=payload.position
    )
    session.add(stage)
    await session.commit()
    await session.refresh(stage)
    return stage


@router.patch("/{pipeline_id}/stages/{stage_id}", response_model=PipelineStageOut)
async def update_stage(
    pipeline_id: str,
    stage_id: str,
    payload: PipelineStageUpdate,
    session: DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> PipelineStage:
    await _get_pipeline_or_404(session, workspace_id, pipeline_id)
    stage = await _get_stage_or_404(session, pipeline_id, stage_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(stage, key, value)
    await session.commit()
    await session.refresh(stage)
    return stage


@router.delete(
    "/{pipeline_id}/stages/{stage_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_stage(
    pipeline_id: str,
    stage_id: str,
    session: DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> None:
    await _get_pipeline_or_404(session, workspace_id, pipeline_id)
    stage = await _get_stage_or_404(session, pipeline_id, stage_id)

    opp_result = await session.execute(
        select(Opportunity).where(Opportunity.stage_id == stage.id).limit(1)
    )
    if opp_result.scalars().first() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a stage that still has opportunities. Move them first.",
        )

    await session.delete(stage)
    await session.commit()
