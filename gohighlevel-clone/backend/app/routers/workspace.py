import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app import db
from app.deps import DbSession, require_workspace_id
from app.models import Workspace
from app.schemas import WorkspaceOut

router = APIRouter(prefix="/api/v1/workspace", tags=["workspace"])


@router.get("/me", response_model=WorkspaceOut)
async def workspace_me(
    workspace_id: uuid.UUID = Depends(require_workspace_id),
    session: DbSession = Depends(db.get_db),
) -> WorkspaceOut:
    workspace = await session.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found",
        )
    return WorkspaceOut.model_validate(workspace)
