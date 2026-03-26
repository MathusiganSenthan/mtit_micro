from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from app.models.product import Product
from app.schemas.product import (
    ProductCreateRequest,
    ProductUpdateRequest,
    StockAdjustRequest,
    ProductListResponse,
)


def get_all_products(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    category: str | None = None,
    search: str | None = None,
) -> ProductListResponse:
    query = db.query(Product).filter(Product.is_active == True)

    if category:
        query = query.filter(Product.category == category)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Product.title.ilike(pattern),
                Product.author.ilike(pattern),
            )
        )

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return ProductListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items,
    )


def get_product_by_id(product_id: str, db: Session) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


def create_product(data: ProductCreateRequest, db: Session) -> Product:
    if data.isbn:
        existing = db.query(Product).filter(Product.isbn == data.isbn).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A product with this ISBN already exists",
            )

    product = Product(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(product_id: str, data: ProductUpdateRequest, db: Session) -> Product:
    product = get_product_by_id(product_id, db)

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def adjust_stock(product_id: str, data: StockAdjustRequest, db: Session) -> Product:
    product = get_product_by_id(product_id, db)
    new_stock = product.stock + data.quantity

    if new_stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock. Current stock: {product.stock}",
        )

    product.stock = new_stock
    db.commit()
    db.refresh(product)
    return product


def delete_product(product_id: str, db: Session) -> dict:
    product = get_product_by_id(product_id, db)
    # Soft delete — keep the record for order history integrity
    product.is_active = False
    db.commit()
    return {"detail": "Product deactivated"}