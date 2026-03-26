from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ── Request schemas ───────────────────────────────────────────────────────────

class OrderItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(..., ge=1)


class OrderCreateRequest(BaseModel):
    items: list[OrderItemRequest] = Field(..., min_length=1)
    shipping_address: str = Field(..., min_length=5)
    notes: Optional[str] = None


class OrderStatusUpdateRequest(BaseModel):
    status: str = Field(
        ...,
        pattern="^(pending|confirmed|shipped|delivered|cancelled)$",
    )


# ── Response schemas ──────────────────────────────────────────────────────────

class OrderItemResponse(BaseModel):
    id: str
    product_id: str
    product_title: str
    quantity: int
    unit_price: float

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: str
    user_id: str
    status: str
    total_amount: float
    shipping_address: str
    notes: Optional[str]
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[OrderResponse]