from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies import get_current_user_id
from app.schemas.profile import ProfileCreateRequest, ProfileUpdateRequest, ProfileResponse
from app.services.user import get_profile, create_profile, update_profile, delete_profile

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=ProfileResponse)
def read_my_profile(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return get_profile(user_id, db)


@router.post("/me", response_model=ProfileResponse, status_code=201)
def create_my_profile(
    data: ProfileCreateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return create_profile(user_id, data, db)


@router.patch("/me", response_model=ProfileResponse)
def update_my_profile(
    data: ProfileUpdateRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return update_profile(user_id, data, db)


@router.delete("/me", status_code=200)
def delete_my_profile(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    return delete_profile(user_id, db)


# Admin-style route: look up any profile by user_id
@router.get("/{user_id}", response_model=ProfileResponse)
def read_profile_by_id(
    user_id: str,
    db: Session = Depends(get_db),
):
    return get_profile(user_id, db)