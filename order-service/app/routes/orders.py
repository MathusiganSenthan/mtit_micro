from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user_id
from app.schemas.order import (
    OrderCreateRequest,
    OrderStatusUpdateRequest,
    OrderResponse,
    OrderListResponse,
)
from app.services.order import (
    create_order,
    get_order,
    get_my_orders,
    update_order_status,
)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=201)
def place_order(
    data: OrderCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return create_order(user_id, data, db)


@router.get("", response_model=OrderListResponse)
def list_my_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return get_my_orders(user_id, db, page, page_size)


@router.get("/{order_id}", response_model=OrderResponse)
def retrieve_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return get_order(order_id, user_id, db)


@router.patch("/{order_id}/status", response_model=OrderResponse)
def change_order_status(
    order_id: str,
    data: OrderStatusUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return update_order_status(order_id, user_id, data, db)