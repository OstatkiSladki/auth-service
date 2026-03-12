from fastapi import APIRouter, Depends
from src.schemas.user import (
  UserProfileResponse,
  UpdateUserProfileRequest,
  UserProfileShort,
)
from src.db.models.user import User
from src.services.user import UserService
from src.api.dependencies import get_current_user, get_user_service
from src.api.v1.staff.router import check_venue_manager_permission

router = APIRouter(prefix="/users", tags=["User Profile"])


@router.get("/me", response_model=UserProfileResponse)
async def get_me(user: User = Depends(get_current_user)):
  return user


@router.patch("/me", response_model=UserProfileResponse)
async def update_me(
  update_data: UpdateUserProfileRequest,
  user: User = Depends(get_current_user),
  user_service: UserService = Depends(get_user_service),
):
  updated_user = await user_service.update_user_profile(user.id, update_data)
  # Reload with staff profile just in case returning response requires it
  return await user_service.get_user_profile(updated_user.id)


@router.get("/search", response_model=list[UserProfileShort])
async def search_users(
  email: str,
  user_service: UserService = Depends(get_user_service),
  user: User = Depends(get_current_user),
):
  return await user_service.search_users(email)
