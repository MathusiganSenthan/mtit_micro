from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.dependencies import AuthContext, get_auth_context, get_current_user_id
from app.schemas.feedback import (
    ReviewCreateRequest,
    ReviewUpdateRequest,
    ReplyCreateRequest,
    ReviewResponse,
    ReviewListResponse,
    ProductRatingSummary,
)
from app.services.feedback import (
    create_review,
    get_reviews_for_product,
    get_my_reviews,
    update_review,
    delete_review,
    mark_review_helpful,
    get_product_rating_summary,
    add_reply,
    delete_reply,
)

router = APIRouter(prefix="/feedback", tags=["feedback"])


# ── Reviews ───────────────────────────────────────────────────────────────────

@router.post("/reviews", response_model=ReviewResponse, status_code=201)
def submit_review(
    data: ReviewCreateRequest,
    auth: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
):
    """Submit a product review. User must have purchased the product."""
    return create_review(auth.user_id, auth.access_token, data, db)


@router.get("/reviews/me", response_model=ReviewListResponse)
def my_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """List all reviews written by the current user."""
    return get_my_reviews(user_id, db, page, page_size)


@router.get("/reviews/{review_id}", response_model=ReviewResponse)
def get_review(review_id: str, db: Session = Depends(get_db)):
    """Get a single review by ID (public)."""
    from app.services.feedback import _get_review_or_404
    return _get_review_or_404(review_id, db)


@router.patch("/reviews/{review_id}", response_model=ReviewResponse)
def edit_review(
    review_id: str,
    data: ReviewUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Update your own review."""
    return update_review(review_id, user_id, data, db)


@router.delete("/reviews/{review_id}", status_code=200)
def remove_review(
    review_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete your own review."""
    return delete_review(review_id, user_id, db)


@router.post("/reviews/{review_id}/helpful", response_model=ReviewResponse)
def helpful(
    review_id: str,
    db: Session = Depends(get_db),
    _: str = Depends(get_current_user_id),
):
    """Mark a review as helpful (increments helpful_count)."""
    return mark_review_helpful(review_id, db)


# ── Product-level endpoints ───────────────────────────────────────────────────

@router.get("/products/{product_id}/reviews", response_model=ReviewListResponse)
def product_reviews(
    product_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    min_rating: Optional[int] = Query(None, ge=1, le=5),
    db: Session = Depends(get_db),
):
    """List all approved reviews for a product (public, with optional rating filter)."""
    return get_reviews_for_product(product_id, db, page, page_size, min_rating)


@router.get("/products/{product_id}/summary", response_model=ProductRatingSummary)
def product_rating_summary(
    product_id: str,
    db: Session = Depends(get_db),
):
    """Return star breakdown and average rating for a product (public)."""
    return get_product_rating_summary(product_id, db)


# ── Replies ───────────────────────────────────────────────────────────────────

@router.post(
    "/reviews/{review_id}/replies",
    response_model=ReviewResponse,
    status_code=201,
)
def reply_to_review(
    review_id: str,
    data: ReplyCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Add a reply to a review."""
    add_reply(review_id, user_id, data, db)
    # Return the updated review with replies
    from app.services.feedback import _get_review_or_404
    return _get_review_or_404(review_id, db)


@router.delete("/replies/{reply_id}", status_code=200)
def remove_reply(
    reply_id: str,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """Delete your own reply."""
    return delete_reply(reply_id, user_id, db)