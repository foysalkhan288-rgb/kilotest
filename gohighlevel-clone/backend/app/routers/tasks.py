from fastapi import APIRouter, Depends

from app.deps import require_workspace_id

router = APIRouter(
    prefix="/api/v1/tasks",
    tags=["tasks"],
    dependencies=[Depends(require_workspace_id)],
)


@router.get("")
async def list_tasks() -> list:
    return []


@router.post("")
async def create_task() -> tuple[dict, int]:
    return {"detail": "Not implemented"}, 501


@router.put("/{task_id}")
async def update_task(task_id: str) -> tuple[dict, int]:
    return {"detail": "Not implemented"}, 501
