from pydantic import BaseModel
from datetime import datetime


# ── Request schemas ───────────────────────────────────────────────────────────

class ProfileCreateRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    address: str | None = None
    avatar_url: str | None = None


class ProfileUpdateRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    address: str | None = None
    avatar_url: str | None = None


# ── Response schemas ──────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    id: str
    user_id: str
    full_name: str | None
    phone: str | None
    address: str | None
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}