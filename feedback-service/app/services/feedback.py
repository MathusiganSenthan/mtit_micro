import httpx
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status
from app.models.feedback import Review, ReviewReply
from app.schemas.feedback import (
    ReviewCreateRequest,
    ReviewUpdateRequest,
    ReplyCreateRequest,
    ReviewListResponse,
    ProductRatingSummary,
)
from app.core.config import settings


# ── Helpers ───────────────────────────────────────────────────────────────────

def _verify_product_exists(product_id: str) -> None:
    """Confirm the product exists in product-service."""
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
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Product service unavailable",
        )


def _verify_user_purchased(
    order_id: str, user_id: str, product_id: str, access_token: str
) -> None:
    """
    Confirm the order belongs to this user and contains the product.
    Forwards the user's JWT so order-service can authorize the request.
    """
    try:
        r = httpx.get(
            f"{settings.ORDER_SERVICE_URL}/orders/{order_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10.0,
        )
        if r.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found",
            )
        if r.status_code == 403:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This order does not belong to you",
            )
        r.raise_for_status()
        order = r.json()

        if order.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This order does not belong to you",
            )

        ordered_product_ids = [item["product_id"] for item in order.get("items", [])]
        if product_id not in ordered_product_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You can only review products you have purchased",
            )

        if order.get("status") not in ("delivered", "shipped"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You can only review products from delivered or shipped orders",
            )

    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Order service unavailable",
        )


def _get_review_or_404(review_id: str, db: Session) -> Review:
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found",
        )
    return review


# ── Review CRUD ───────────────────────────────────────────────────────────────

def create_review(
    user_id: str, access_token: str, data: ReviewCreateRequest, db: Session
) -> Review:
    # One review per user per product
    existing = (
        db.query(Review)
        .filter(Review.user_id == user_id, Review.product_id == data.product_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this product",
        )

    _verify_product_exists(data.product_id)
    _verify_user_purchased(data.order_id, user_id, data.product_id, access_token)

    review = Review(
        user_id=user_id,
        product_id=data.product_id,
        order_id=data.order_id,
        rating=data.rating,
        title=data.title,
        body=data.body,
        is_verified_purchase=True,
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def get_reviews_for_product(
    product_id: str,
    db: Session,
    page: int = 1,
    page_size: int = 20,
    min_rating: int | None = None,
) -> ReviewListResponse:
    query = (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.is_approved == True)
        .order_by(Review.created_at.desc())
    )

    if min_rating is not None:
        query = query.filter(Review.rating >= min_rating)

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    avg = (
        db.query(func.avg(Review.rating))
        .filter(Review.product_id == product_id, Review.is_approved == True)
        .scalar()
    )
    average_rating = round(float(avg), 2) if avg else None

    return ReviewListResponse(
        total=total,
        page=page,
        page_size=page_size,
        average_rating=average_rating,
        items=items,
    )


def get_my_reviews(
    user_id: str, db: Session, page: int = 1, page_size: int = 20
) -> ReviewListResponse:
    query = (
        db.query(Review)
        .filter(Review.user_id == user_id)
        .order_by(Review.created_at.desc())
    )
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ReviewListResponse(
        total=total, page=page, page_size=page_size, average_rating=None, items=items
    )


def update_review(
    review_id: str, user_id: str, data: ReviewUpdateRequest, db: Session
) -> Review:
    review = _get_review_or_404(review_id, db)
    if review.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own reviews",
        )

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(review, field, value)

    db.commit()
    db.refresh(review)
    return review


def delete_review(review_id: str, user_id: str, db: Session) -> dict:
    review = _get_review_or_404(review_id, db)
    if review.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own reviews",
        )
    db.delete(review)
    db.commit()
    return {"detail": "Review deleted"}


def mark_review_helpful(review_id: str, db: Session) -> Review:
    review = _get_review_or_404(review_id, db)
    review.helpful_count += 1
    db.commit()
    db.refresh(review)
    return review


# ── Rating summary ────────────────────────────────────────────────────────────

def get_product_rating_summary(product_id: str, db: Session) -> ProductRatingSummary:
    rows = (
        db.query(Review.rating, func.count(Review.id))
        .filter(Review.product_id == product_id, Review.is_approved == True)
        .group_by(Review.rating)
        .all()
    )

    breakdown = {star: 0 for star in range(1, 6)}
    total = 0
    weighted = 0

    for rating, count in rows:
        breakdown[rating] = count
        total += count
        weighted += rating * count

    average_rating = round(weighted / total, 2) if total > 0 else None

    return ProductRatingSummary(
        product_id=product_id,
        total_reviews=total,
        average_rating=average_rating,
        rating_breakdown=breakdown,
    )


# ── Replies ───────────────────────────────────────────────────────────────────

def add_reply(
    review_id: str, user_id: str, data: ReplyCreateRequest, db: Session
) -> ReviewReply:
    _get_review_or_404(review_id, db)  # ensure review exists

    reply = ReviewReply(
        review_id=review_id,
        user_id=user_id,
        body=data.body,
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply


def delete_reply(reply_id: str, user_id: str, db: Session) -> dict:
    reply = db.query(ReviewReply).filter(ReviewReply.id == reply_id).first()
    if not reply:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reply not found",
        )
    if reply.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own replies",
        )
    db.delete(reply)
    db.commit()
    return {"detail": "Reply deleted"}