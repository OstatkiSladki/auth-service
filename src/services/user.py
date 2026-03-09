from typing import Optional
from fastapi import HTTPException, status
from src.db.repositories.user import UserRepository
from src.schemas.user import UpdateUserProfileRequest
from src.db.models.user import User


class UserService:
  def __init__(self, user_repo: UserRepository):
    self.user_repo = user_repo

  async def get_user_profile(self, user_id: int) -> User:
    user = await self.user_repo.get_user_with_staff_profile(user_id)
    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
      )
    return user

  async def update_user_profile(
    self, user_id: int, update_data: UpdateUserProfileRequest
  ) -> User:
    user = await self.user_repo.get_by_id(user_id)
    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
      )

    update_dict = update_data.model_dump(exclude_unset=True)
    if not update_dict:
      return user

    updated_user = await self.user_repo.update(user, **update_dict)
    return updated_user

  async def search_users(self, email_prefix: str) -> list[User]:
    return await self.user_repo.search_by_email(email_prefix)
