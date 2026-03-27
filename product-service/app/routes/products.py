from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.dependencies import get_current_user_id, get_current_user_or_internal
from app.schemas.product import (
    ProductCreateRequest,
    ProductUpdateRequest,
    StockAdjustRequest,
    ProductResponse,
    ProductListResponse,
)
from app.services.product import (
    get_all_products,
    get_product_by_id,
    create_product,
    update_product,
    adjust_stock,
    delete_product,
)

router = APIRouter(prefix="/products", tags=["products"])


# ── Public endpoints (no auth required) ──────────────────────────────────────

@router.get("", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return get_all_products(db, page, page_size, category, search)


@router.get("/{product_id}", response_model=ProductResponse)
def retrieve_product(product_id: str, db: Session = Depends(get_db)):
    return get_product_by_id(product_id, db)


# ── Protected endpoints (auth required) ──────────────────────────────────────

@router.post("", response_model=ProductResponse, status_code=201)
def add_product(
    data: ProductCreateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user_id),   # auth guard
):
    return create_product(data, db)


@router.patch("/{product_id}", response_model=ProductResponse)
def edit_product(
    product_id: str,
    data: ProductUpdateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user_id),
):
    return update_product(product_id, data, db)


@router.patch("/{product_id}/stock", response_model=ProductResponse)
def update_stock(
    product_id: str,
    data: StockAdjustRequest,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user_or_internal),
):
    return adjust_stock(product_id, data, db)


@router.delete("/{product_id}", status_code=200)
def remove_product(
    product_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user_id),
):
    return delete_product(product_id, db)