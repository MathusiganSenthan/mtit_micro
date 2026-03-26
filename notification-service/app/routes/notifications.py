from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user_id
from app.schemas.notification import (
    SendNotificationRequest,
    NotificationResponse,
    NotificationListResponse,
)
from app.services.notification import (
    handle_notification,
    get_notifications_for_user,
    get_notification_by_id,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ── Internal endpoint — called by other services, not the public gateway ─────

@router.post("/send", response_model=NotificationResponse, status_code=201)
def send_notification(
    data: SendNotificationRequest,
    db: Session = Depends(get_db),
):
    """
    Internal endpoint called by order-service and other services.
    Not exposed through the API gateway.
    """
    return handle_notification(data, db)


# ── User-facing endpoints ─────────────────────────────────────────────────────

@router.get("/me", response_model=NotificationListResponse)
def list_my_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return get_notifications_for_user(user_id, db, page, page_size)


@router.get("/{notification_id}", response_model=NotificationResponse)
def retrieve_notification(
    notification_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    notification = get_notification_by_id(notification_id, db)
    if notification.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return notification