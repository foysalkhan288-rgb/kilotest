from contextlib import asynccontextmanager
from typing import AsyncIterator

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import FRONTEND_URL
from app.routers import (
    appointments,
    auth,
    calendars,
    contacts,
    dashboard,
    emails,
    forms,
    inbox,
    opportunities,
    pages,
    pipelines,
    reviews,
    tags,
    tasks,
    workflows,
    workspace,
)


# Module-level APScheduler instance shared with the workflow engine. Only this
# module is permitted to create/start/stop the scheduler.
scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Start the background scheduler so deferred workflow actions ("wait") run.
    if not scheduler.running:
        scheduler.start()
    try:
        yield
    finally:
        if scheduler.running:
            scheduler.shutdown(wait=False)


app = FastAPI(
    title="GoHighLevel Clone API",
    description="Backend foundation (Wave 1) for a lean CRM / marketing automation MVP.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(workspace.router)
app.include_router(contacts.router)
app.include_router(tags.router)
app.include_router(pipelines.router)
app.include_router(opportunities.router)
app.include_router(forms.router)
app.include_router(pages.router)
app.include_router(emails.router)
app.include_router(inbox.router)
app.include_router(calendars.router)
app.include_router(appointments.router)
app.include_router(appointments.public_router)
app.include_router(workflows.router)
app.include_router(dashboard.router)
app.include_router(tasks.router)
app.include_router(reviews.router)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", tags=["health"])
async def root() -> dict[str, str]:
    return {"name": "gohighlevel-clone-backend", "version": "0.1.0"}
