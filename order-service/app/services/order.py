import httpx
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.order import Order, OrderItem
from app.schemas.order import (
    OrderCreateRequest,
    OrderStatusUpdateRequest,
    OrderListResponse,
)
from app.core.config import settings

VALID_TRANSITIONS = {
    "pending":   {"confirmed", "cancelled"},
    "confirmed": {"shipped",   "cancelled"},
    "shipped":   {"delivered"},
    "delivered": set(),
    "cancelled": set(),
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch_product(product_id: str) -> dict:
    """Call product-service to validate product and get price."""
    try:
        r = httpx.get(
            f"{settings.PRODUCT_SERVICE_URL}/products/{product_id}",
            timeout=10.0,
        )
        if r.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found",
            )
        r.raise_for_status()
        return r.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Product service unavailable",
        )


def _deduct_stock(product_id: str, quantity: int) -> None:
    """Tell product-service to deduct stock."""
    try:
        r = httpx.patch(
            f"{settings.PRODUCT_SERVICE_URL}/products/{product_id}/stock",
            json={"quantity": -quantity},
            headers={"x-internal-token": settings.INTERNAL_API_KEY},
            timeout=10.0,
        )
        r.raise_for_status()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Product service unavailable",
        )


def _restore_stock(product_id: str, quantity: int) -> None:
    """Restore stock when an order is cancelled."""
    try:
        httpx.patch(
            f"{settings.PRODUCT_SERVICE_URL}/products/{product_id}/stock",
            json={"quantity": quantity},
            headers={"x-internal-token": settings.INTERNAL_API_KEY},
            timeout=10.0,
        )
    except Exception:
        pass  # Best-effort; log in production


def _send_notification(event: str, payload: dict) -> None:
    """Fire-and-forget notification to notification-service."""
    try:
        httpx.post(
            f"{settings.NOTIFICATION_SERVICE_URL}/notifications/send",
            json={"event": event, "payload": payload},
            timeout=5.0,
        )
    except Exception:
        pass  # Notifications are non-blocking


# ── Service functions ─────────────────────────────────────────────────────────

def create_order(user_id: str, data: OrderCreateRequest, db: Session) -> Order:
    order_items: list[OrderItem] = []
    total = 0.0
    deducted: list[tuple[str, int]] = []

    try:
        for item_req in data.items:
            product = _fetch_product(item_req.product_id)

            if not product.get("is_active"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product '{product['title']}' is no longer available",
                )
            if product["stock"] < item_req.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for '{product['title']}'. Available: {product['stock']}",
                )

            unit_price = float(product["price"])
            total += unit_price * item_req.quantity
            order_items.append(
                OrderItem(
                    product_id=item_req.product_id,
                    product_title=product["title"],
                    quantity=item_req.quantity,
                    unit_price=unit_price,
                )
            )

        for item_req in data.items:
            _deduct_stock(item_req.product_id, item_req.quantity)
            deducted.append((item_req.product_id, item_req.quantity))

        order = Order(
            user_id=user_id,
            total_amount=round(total, 2),
            shipping_address=data.shipping_address,
            notes=data.notes,
            items=order_items,
        )
        db.add(order)
        try:
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(order)

    except HTTPException:
        for product_id, quantity in reversed(deducted):
            _restore_stock(product_id, quantity)
        raise
    except Exception:
        db.rollback()
        for product_id, quantity in reversed(deducted):
            _restore_stock(product_id, quantity)
        raise

    _send_notification(
        "order_created",
        {
            "user_id": user_id,
            "order_id": order.id,
            "total_amount": order.total_amount,
        },
    )

    return order


def get_order(order_id: str, user_id: str, db: Session) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return order


def get_my_orders(
    user_id: str, db: Session, page: int = 1, page_size: int = 20
) -> OrderListResponse:
    query = db.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return OrderListResponse(total=total, page=page, page_size=page_size, items=items)


def update_order_status(
    order_id: str, user_id: str, data: OrderStatusUpdateRequest, db: Session
) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    allowed = VALID_TRANSITIONS.get(order.status, set())
    if data.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{order.status}' to '{data.status}'",
        )

    # Restore stock when cancelling a non-delivered order
    if data.status == "cancelled":
        for item in order.items:
            _restore_stock(item.product_id, item.quantity)

    order.status = data.status
    db.commit()
    db.refresh(order)

    _send_notification("order_status_changed", {
        "user_id": order.user_id,
        "order_id": order.id,
        "new_status": order.status,
    })

    return order