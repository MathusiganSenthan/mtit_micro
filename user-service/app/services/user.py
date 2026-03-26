from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.profile import UserProfile
from app.schemas.profile import ProfileCreateRequest, ProfileUpdateRequest


def get_profile(user_id: str, db: Session) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


def create_profile(user_id: str, data: ProfileCreateRequest, db: Session) -> UserProfile:
    existing = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Profile already exists for this user",
        )

    profile = UserProfile(user_id=user_id, **data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


def update_profile(user_id: str, data: ProfileUpdateRequest, db: Session) -> UserProfile:
    profile = get_profile(user_id, db)

    # Only update fields that were explicitly provided
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)
    return profile


def delete_profile(user_id: str, db: Session) -> dict:
    profile = get_profile(user_id, db)
    db.delete(profile)
    db.commit()
    return {"detail": "Profile deleted"}