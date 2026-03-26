from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional


# ── Request schemas ───────────────────────────────────────────────────────────

class SendNotificationRequest(BaseModel):
    """
    Received from other services (e.g. order-service).
    `payload` is event-specific — kept as a free dict for flexibility.
    """
    event: str
    payload: dict[str, Any]


# ── Response schemas ──────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    event: str
    channel: str
    subject: str
    is_sent: bool
    error: Optional[str]
    created_at: datetime
    sent_at: Optional[datetime]

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[NotificationResponse]