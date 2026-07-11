import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    workspace_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    workspace_id: str


# --------------------------------------------------------------------------
# Users / Workspaces
# --------------------------------------------------------------------------
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    created_at: datetime | None = None


class WorkspaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    owner_user_id: uuid.UUID
    created_at: datetime | None = None


# --------------------------------------------------------------------------
# Contacts
# --------------------------------------------------------------------------
class ContactBase(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    tags: list[str] = []
    custom_fields: dict[str, Any] = {}
    notes: str | None = None


class ContactCreate(ContactBase):
    pass


class ContactUpdate(BaseModel):
    firstname: str | None = None
    lastname: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    tags: list[str] | None = None
    custom_fields: dict[str, Any] | None = None
    notes: str | None = None


class ContactOut(ContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    created_at: datetime | None = None


class ContactTagsUpdate(BaseModel):
    tags: list[str]


# --------------------------------------------------------------------------
# Generic placeholder schemas for later feature waves
# --------------------------------------------------------------------------
class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    color: str | None = None


class Message(BaseModel):
    detail: str = "Not implemented"
