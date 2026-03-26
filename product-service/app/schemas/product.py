from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# ── Request schemas ───────────────────────────────────────────────────────────

class ProductCreateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    isbn: Optional[str] = None
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    stock: int = Field(0, ge=0)
    category: str = "other"
    cover_image_url: Optional[str] = None


class ProductUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    isbn: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    category: Optional[str] = None
    cover_image_url: Optional[str] = None
    is_active: Optional[bool] = None


class StockAdjustRequest(BaseModel):
    quantity: int = Field(..., description="Positive to add, negative to deduct")


# ── Response schemas ──────────────────────────────────────────────────────────

class ProductResponse(BaseModel):
    id: str
    title: str
    author: str
    isbn: Optional[str]
    description: Optional[str]
    price: float
    stock: int
    category: str
    cover_image_url: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProductResponse]