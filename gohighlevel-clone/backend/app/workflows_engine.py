"""Shared workflow automation engine.

This module is the single entry point other agents call to run automation:

    from app.workflows_engine import handle_event

    await handle_event(
        event_type="contact.created",
        workspace_id=workspace_id,
        context={"contact_id": str(contact.id)},
    )

Design goals
------------
* ``handle_event`` NEVER raises. Per-workflow failures are recorded as an
  ``activity_log`` row of type ``workflow_error``.
* All database access happens through a private session created from
  ``app.db.SessionLocal`` so the engine is usable from anywhere (routers,
  other services) without needing an injected session.
* Imports of optional collaborators (the email sender and the APScheduler
  instance living in ``app.main``) are guarded so the app never crashes if a
  module is absent or not yet fully initialised.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.db import SessionLocal
from app.models import (
    ActivityLog,
    Contact,
    Opportunity,
    Pipeline,
    PipelineStage,
    Task,
    Workflow,
)

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Optional collaborators (guarded imports)
# --------------------------------------------------------------------------- #
def _get_scheduler():
    """Return the module-level APScheduler instance, or None if unavailable.

    Imported lazily (inside functions) to avoid an import cycle:
    ``app.main`` imports the routers, which import this engine, so importing
    ``app.main`` at module load time would fail. By the time any workflow runs
    the application (and therefore ``scheduler``) is fully initialised.
    """
    try:  # pragma: no cover - depends on runtime wiring
        from app.main import scheduler  # type: ignore

        return scheduler
    except Exception as exc:  # noqa: BLE001
        logger.warning("Workflow scheduler unavailable: %s", exc)
        return None


async def _send_email_safe(
    *, workspace_id: UUID, to: str, subject: str, html: str, contact_id: UUID | None
) -> None:
    """Send an email via the shared sender, never raising."""
    try:
        from app.services.email import send_email

        await send_email(
            workspace_id=workspace_id,
            to=to,
            subject=subject,
            html=html,
            contact_id=contact_id,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Workflow send_email failed: %s", exc)


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
async def handle_event(event_type: str, workspace_id: Any, context: dict) -> None:
    """Load and run all active workflows in a workspace for ``event_type``.

    This function is guaranteed not to raise.
    """
    try:
        ws_id = _as_uuid(workspace_id)
    except Exception:  # noqa: BLE001
        logger.warning("handle_event received invalid workspace_id: %r", workspace_id)
        return

    try:
        async with SessionLocal() as session:
            stmt = select(Workflow).where(
                Workflow.workspace_id == ws_id,
                Workflow.active.is_(True),
            )
            result = await session.execute(stmt)
            workflows = result.scalars().all()
    except Exception as exc:  # noqa: BLE001
        logger.exception("handle_event failed loading workflows: %s", exc)
        return

    for workflow in workflows:
        trigger = workflow.trigger or {}
        # Support either a {"event_type": ...} dict or a bare string trigger.
        matches = False
        try:
            if isinstance(trigger, dict):
                matches = trigger.get("event_type") == event_type
            elif isinstance(trigger, str):
                matches = trigger == event_type
        except Exception:  # noqa: BLE001
            matches = False

        if not matches:
            continue

        try:
            await run_workflow(workflow, context)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Workflow %s failed: %s", workflow.id, exc)
            try:
                async with SessionLocal() as err_session:
                    err_session.add(
                        ActivityLog(
                            workspace_id=ws_id,
                            type="workflow_error",
                            message=(
                                f"Workflow '{workflow.name}' (id={workflow.id}) "
                                f"failed on event '{event_type}': {exc}"
                            ),
                        )
                    )
                    await err_session.commit()
            except Exception:  # noqa: BLE001
                logger.exception("Failed to record workflow_error activity log")


async def run_workflow(workflow: Workflow, context: dict) -> None:
    """Execute every action in a single workflow using one DB session."""
    ws_id = _as_uuid(workflow.workspace_id)
    actions = workflow.actions or []
    if not isinstance(actions, list):
        # Defensive: some callers may wrap the list in a dict.
        actions = actions.get("actions", []) if isinstance(actions, dict) else []

    async with SessionLocal() as session:
        await _execute_actions(actions, ws_id, context, session)


async def run_workflow_remaining(
    workspace_id: Any, context: dict, remaining_actions: list
) -> None:
    """Run a delayed (post-``wait``) list of actions in one DB session."""
    ws_id = _as_uuid(workspace_id)
    async with SessionLocal() as session:
        await _execute_actions(remaining_actions or [], ws_id, context, session)


def schedule_workflow_remaining(
    workspace_id: Any, context: dict, remaining_actions: list, minutes: int
) -> None:
    """Synchronous entry point scheduled by APScheduler for ``wait`` actions.

    APScheduler runs jobs in a worker thread, so we drive the coroutine with a
    fresh event loop via ``asyncio.run``.
    """
    try:
        asyncio.run(
            run_workflow_remaining(workspace_id, context, remaining_actions)
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Scheduled workflow remaining actions failed: %s", exc)


# --------------------------------------------------------------------------- #
# Core action dispatcher
# --------------------------------------------------------------------------- #
async def _execute_actions(
    actions: list, workspace_id: UUID, context: dict, session: Any
) -> None:
    """Iterate over a list of action dicts and dispatch each one."""
    if not actions:
        return

    for action in actions:
        if not isinstance(action, dict):
            continue

        action_type = action.get("type")
        try:
            if action_type == "send_email":
                await _action_send_email(action, workspace_id, context, session)
            elif action_type in ("add_tag", "remove_tag"):
                await _action_tag(action_type, action, workspace_id, context, session)
            elif action_type == "create_task":
                await _action_create_task(action, workspace_id, context, session)
            elif action_type == "move_opportunity_stage":
                await _action_move_stage(action, workspace_id, context, session)
            elif action_type == "notify":
                await _action_notify(action, workspace_id, session)
            elif action_type == "wait":
                await _action_wait(action, workspace_id, context)
            elif action_type == "if_else":
                await _action_if_else(action, workspace_id, context, session)
            else:
                logger.warning("Unknown workflow action type: %r", action_type)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Workflow action '%s' failed: %s", action_type, exc)
            # Record the failing action but keep processing subsequent actions.
            session.add(
                ActivityLog(
                    workspace_id=workspace_id,
                    type="workflow_error",
                    message=(
                        f"Action '{action_type}' failed: {exc} "
                        f"(context keys: {list(context.keys())})"
                    ),
                )
            )
            await session.commit()


# --------------------------------------------------------------------------- #
# Individual action handlers
# --------------------------------------------------------------------------- #
async def _action_send_email(
    action: dict, workspace_id: UUID, context: dict, session: Any
) -> None:
    contact_id = _contact_id_from_context(context)
    to = action.get("to")
    subject = action.get("subject") or ""
    html = action.get("html") or ""

    # Resolve the recipient email from the contact when not explicitly given.
    if not to and contact_id is not None:
        contact = await _load_contact(session, workspace_id, contact_id)
        if contact is not None and contact.email:
            to = contact.email

    if not to:
        logger.warning("send_email action skipped: no recipient email available")
        return

    await _send_email_safe(
        workspace_id=workspace_id,
        to=to,
        subject=subject,
        html=html,
        contact_id=contact_id,
    )


async def _action_tag(
    action_type: str, action: dict, workspace_id: UUID, context: dict, session: Any
) -> None:
    contact_id = _contact_id_from_context(context)
    if contact_id is None:
        logger.warning("%s action skipped: no contact_id in context", action_type)
        return

    tag = action.get("tag")
    if not tag:
        return

    contact = await _load_contact(session, workspace_id, contact_id)
    if contact is None:
        return

    tags = list(contact.tags or [])
    if action_type == "add_tag":
        if tag not in tags:
            tags.append(tag)
    else:  # remove_tag
        tags = [t for t in tags if t != tag]

    contact.tags = tags
    session.add(contact)
    await session.commit()


async def _action_create_task(
    action: dict, workspace_id: UUID, context: dict, session: Any
) -> None:
    contact_id = _contact_id_from_context(context)
    if contact_id is None:
        logger.warning("create_task action skipped: no contact_id in context")
        return

    due = None
    raw_due = action.get("due")
    if raw_due:
        try:
            due = _parse_datetime(raw_due)
        except Exception:  # noqa: BLE001
            due = None

    session.add(
        Task(
            workspace_id=workspace_id,
            contact_id=contact_id,
            title=action.get("title") or "Task",
            due=due,
        )
    )
    await session.commit()


async def _action_move_stage(
    action: dict, workspace_id: UUID, context: dict, session: Any
) -> None:
    contact_id = _contact_id_from_context(context)
    if contact_id is None:
        logger.warning("move_opportunity_stage action skipped: no contact_id")
        return

    stage_name = action.get("stage_name") or action.get("stage")
    if not stage_name:
        return

    # Find the target stage within this workspace's pipelines.
    stage_stmt = (
        select(PipelineStage)
        .join(Pipeline, PipelineStage.pipeline_id == Pipeline.id)
        .where(
            Pipeline.workspace_id == workspace_id,
            PipelineStage.name == stage_name,
        )
        .order_by(PipelineStage.position.asc())
    )
    stage_result = await session.execute(stage_stmt)
    target_stage = stage_result.scalars().first()
    if target_stage is None:
        logger.warning("move_opportunity_stage: no stage named %r", stage_name)
        return

    # Update the most recent opportunity for this contact.
    opp_stmt = (
        select(Opportunity)
        .where(
            Opportunity.workspace_id == workspace_id,
            Opportunity.contact_id == contact_id,
        )
        .order_by(Opportunity.created_at.desc())
    )
    opp_result = await session.execute(opp_stmt)
    opportunity = opp_result.scalars().first()
    if opportunity is None:
        logger.warning("move_opportunity_stage: no opportunity for contact")
        return

    opportunity.stage_id = target_stage.id
    session.add(opportunity)
    await session.commit()


async def _action_notify(action: dict, workspace_id: UUID, session: Any) -> None:
    message = action.get("message") or action.get("text") or "Workflow notification"
    session.add(
        ActivityLog(
            workspace_id=workspace_id,
            type="notify",
            message=message,
        )
    )
    await session.commit()


async def _action_wait(action: dict, workspace_id: UUID, context: dict) -> None:
    """Schedule the ``then`` actions to run after ``minutes`` via APScheduler."""
    minutes = int(action.get("minutes", 0) or 0)
    then_actions = action.get("then") or []
    if not then_actions:
        return

    scheduler = _get_scheduler()
    if scheduler is None:
        # Fall back to immediate execution if the scheduler is unavailable.
        logger.warning("wait action: scheduler unavailable, running 'then' now")
        async with SessionLocal() as session:
            await _execute_actions(then_actions, _as_uuid(workspace_id), context, session)
        return

    run_date = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    scheduler.add_job(
        schedule_workflow_remaining,
        trigger="date",
        run_date=run_date,
        args=(workspace_id, context, then_actions),
        id=f"workflow_wait_{uuid4hex()}",
        replace_existing=False,
    )


async def _action_if_else(
    action: dict, workspace_id: UUID, context: dict, session: Any
) -> None:
    """Evaluate ``field`` (contact.<attr>) and recurse into the chosen branch."""
    field = action.get("field", "")
    equals = action.get("equals")
    then_actions = action.get("then") or []
    else_actions = action.get("else") or []

    value = await _resolve_field(field, context, session, workspace_id)

    branch = then_actions if _values_equal(value, equals) else else_actions
    await _execute_actions(branch, workspace_id, context, session)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _as_uuid(value: Any) -> UUID:
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _contact_id_from_context(context: dict) -> UUID | None:
    raw = context.get("contact_id")
    if raw is None:
        return None
    try:
        return _as_uuid(raw)
    except Exception:  # noqa: BLE001
        return None


async def _load_contact(session: Any, workspace_id: UUID, contact_id: UUID) -> Any:
    stmt = select(Contact).where(
        Contact.id == contact_id,
        Contact.workspace_id == workspace_id,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def _resolve_field(
    field: str, context: dict, session: Any, workspace_id: UUID
) -> Any:
    """Resolve a field reference such as ``contact.email`` or ``context.foo``."""
    if not field:
        return None

    if field.startswith("contact."):
        attr = field[len("contact.") :]
        contact_id = _contact_id_from_context(context)
        if contact_id is None:
            return None
        contact = await _load_contact(session, workspace_id, contact_id)
        if contact is None:
            return None
        return getattr(contact, attr, None)

    if field.startswith("context."):
        attr = field[len("context.") :]
        return context.get(attr)

    return context.get(field)


def _values_equal(a: Any, b: Any) -> bool:
    # Treat "true"/"false" strings as booleans for convenience.
    if isinstance(b, str):
        low = b.lower()
        if low == "true":
            b = True
        elif low == "false":
            b = False
    return a == b


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        # Accept ISO strings (with or without timezone).
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt
    raise ValueError(f"Cannot parse datetime from {value!r}")


def uuid4hex() -> str:
    import uuid

    return uuid.uuid4().hex
