from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ── Request schemas ───────────────────────────────────────────────────────────

class ReviewCreateRequest(BaseModel):
    product_id: str
    order_id: str
    rating: int = Field(..., ge=1, le=5)
    title: str = Field(..., min_length=3, max_length=150)
    body: str = Field(..., min_length=10)


class ReviewUpdateRequest(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, min_length=3, max_length=150)
    body: Optional[str] = Field(None, min_length=10)


class ReplyCreateRequest(BaseModel):
    body: str = Field(..., min_length=2)


# ── Response schemas ──────────────────────────────────────────────────────────

class ReplyResponse(BaseModel):
    id: str
    review_id: str
    user_id: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewResponse(BaseModel):
    id: str
    user_id: str
    product_id: str
    order_id: str
    rating: int
    title: str
    body: str
    is_verified_purchase: bool
    is_approved: bool
    helpful_count: int
    replies: list[ReplyResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    average_rating: Optional[float]
    items: list[ReviewResponse]


class ProductRatingSummary(BaseModel):
    product_id: str
    total_reviews: int
    average_rating: Optional[float]
    rating_breakdown: dict[int, int]
    # e.g. {5: 40, 4: 20, 3: 10, 2: 5, 1: 2}