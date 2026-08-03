import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import DbSession, require_workspace_id
from app.models import Contact, Task
from app.schemas import TaskCreate, TaskOut, TaskUpdate

router = APIRouter(
    prefix="/api/v1/tasks",
    tags=["tasks"],
    dependencies=[Depends(require_workspace_id)],
)


@router.get("", response_model=list[TaskOut])
async def list_tasks(
    session: AsyncSession = DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
    done: bool | None = Query(None, description="Filter by completion status"),
    contact_id: uuid.UUID | None = Query(None, description="Filter by contact ID"),
) -> list[Task]:
    stmt = select(Task).where(Task.workspace_id == workspace_id)

    if done is not None:
        stmt = stmt.where(Task.done == done)

    if contact_id is not None:
        stmt = stmt.where(Task.contact_id == contact_id)

    stmt = stmt.order_by(Task.due.asc().nullslast())

    result = await session.execute(stmt)
    tasks = result.scalars().all()
    return tasks


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: TaskCreate,
    session: AsyncSession = DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> Task:
    if payload.contact_id is not None:
        contact = (
            await session.execute(
                select(Contact).where(
                    Contact.id == payload.contact_id,
                    Contact.workspace_id == workspace_id,
                )
            )
        ).scalar_one_or_none()
        if contact is None:
            raise HTTPException(status_code=400, detail="Invalid contact for workspace")

    task = Task(
        workspace_id=workspace_id,
        contact_id=payload.contact_id,
        title=payload.title,
        due=payload.due,
        done=payload.done,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    session: AsyncSession = DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> Task:
    task = (
        await session.execute(
            select(Task).where(Task.id == task_id, Task.workspace_id == workspace_id)
        )
    ).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(task, field, value)

    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: uuid.UUID,
    session: AsyncSession = DbSession,
    workspace_id: uuid.UUID = Depends(require_workspace_id),
) -> dict[str, str]:
    task = (
        await session.execute(
            select(Task).where(Task.id == task_id, Task.workspace_id == workspace_id)
        )
    ).scalar_one_or_none()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    await session.delete(task)
    await session.commit()
    return {"detail": "deleted"}
