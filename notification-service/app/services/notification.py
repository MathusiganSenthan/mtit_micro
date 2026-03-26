from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.schemas.notification import SendNotificationRequest, NotificationListResponse
from app.core.mailer import send_email


# ── Email templates per event ─────────────────────────────────────────────────

def _build_email(event: str, payload: dict) -> tuple[str, str]:
    """Return (subject, html_body) for a given event."""

    if event == "order_created":
        order_id = str(payload.get("order_id", "N/A"))
        total = payload.get("total_amount", 0)
        short_id = (order_id[:8] if len(order_id) >= 8 else order_id).upper()
        subject = f"Order Confirmed – #{short_id}"
        body = f"""
        <h2>Your order has been placed!</h2>
        <p>Order ID: <strong>{order_id}</strong></p>
        <p>Total: <strong>${total:.2f}</strong></p>
        <p>We'll notify you when it ships.</p>
        """

    elif event == "order_status_changed":
        order_id = str(payload.get("order_id", "N/A"))
        new_status = payload.get("new_status", "updated").replace("_", " ").title()
        short_id = (order_id[:8] if len(order_id) >= 8 else order_id).upper()
        subject = f"Order Update – #{short_id} is now {new_status}"
        body = f"""
        <h2>Your order status has changed</h2>
        <p>Order ID: <strong>{order_id}</strong></p>
        <p>New status: <strong>{new_status}</strong></p>
        """

    elif event == "welcome":
        subject = "Welcome to Bookstore!"
        body = """
        <h2>Welcome! 📚</h2>
        <p>Your account has been created successfully.</p>
        <p>Start exploring thousands of books today.</p>
        """

    else:
        subject = f"Notification: {event}"
        body = f"<p>Event: {event}</p><pre>{payload}</pre>"

    return subject, body


# ── Service functions ─────────────────────────────────────────────────────────

def handle_notification(
    data: SendNotificationRequest, db: Session
) -> Notification:
    user_id = str(data.payload.get("user_id", "system"))
    subject, body = _build_email(data.event, data.payload)

    notification = Notification(
        user_id=user_id,
        event=data.event,
        channel="email",
        subject=subject,
        body=body,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    # Try to send — record the outcome either way
    recipient = data.payload.get("email") or f"{user_id}@placeholder.com"
    try:
        send_email(to=recipient, subject=subject, body_html=body)
        notification.is_sent = True
        notification.sent_at = datetime.now(timezone.utc)
    except Exception as exc:
        notification.is_sent = False
        notification.error = str(exc)

    db.commit()
    db.refresh(notification)
    return notification


def get_notifications_for_user(
    user_id: str,
    db: Session,
    page: int = 1,
    page_size: int = 20,
) -> NotificationListResponse:
    query = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return NotificationListResponse(
        total=total, page=page, page_size=page_size, items=items
    )


def get_notification_by_id(notification_id: str, db: Session) -> Notification:
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )
    return notification