from typing import Optional
import math
from fastapi import HTTPException, status
from src.db.repositories.staff import StaffProfileRepository
from src.db.repositories.user import UserRepository
from src.db.models.enums import StaffRole
from src.db.models.staff import StaffProfile
from src.schemas.staff import (
  StaffMemberResponse,
  StaffListPaginatedResponse,
  StaffFilterParams,
)


class StaffService:
  def __init__(self, staff_repo: StaffProfileRepository, user_repo: UserRepository):
    self.staff_repo = staff_repo
    self.user_repo = user_repo

  async def add_staff_member(
    self, venue_id: int, user_email: str, role: StaffRole
  ) -> StaffMemberResponse:
    # TODO: gRPC Call to Venue Service to CheckVenueExists

    user = await self.user_repo.get_by_email(user_email)
    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
      )

    existing_profile = await self.staff_repo.get_by_user_id(user.id)
    if existing_profile:
      raise HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail="User already has a staff profile"
      )

    profile = await self.staff_repo.create(
      user_id=user.id, venue_id=venue_id, role=role
    )

    # update user role if it's currently USER
    if user.role.value == "user":
      await self.user_repo.update(user, role="staff")

    # TODO: Publish auth.staff.assigned to RabbitMQ

    profile.user = user  # Assign memory object to avoid reloading relationship
    return self._format_staff_member(profile)

  async def get_staff_by_venue_paginated(
    self, venue_id: int, params: StaffFilterParams
  ) -> StaffListPaginatedResponse:
    """Get paginated staff list with user data"""
    role_value = params.role.value if params.role else None
    sort_by_value = params.sort_by.value

    profiles, total = await self.staff_repo.get_by_venue_id_paginated(
      venue_id, params.page, params.limit, role_value, sort_by_value
    )

    items = []
    for profile in profiles:
      items.append(self._format_staff_member(profile))

    pages = math.ceil(total / params.limit) if total > 0 else 1

    return StaffListPaginatedResponse(
      items=items, total=total, page=params.page, limit=params.limit, pages=pages
    )

  async def get_staff_profile(self, profile_id: int) -> StaffMemberResponse:
    profile = await self.staff_repo.get_with_user_by_id(profile_id)
    if not profile:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found"
      )
    return self._format_staff_member(profile)

  async def update_staff_profile(
    self, profile_id: int, role: StaffRole
  ) -> StaffMemberResponse:
    profile = await self.staff_repo.get_by_id(profile_id)
    if not profile:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found"
      )
    await self.staff_repo.update(profile, role=role)

    # Refetch with user join
    updated = await self.staff_repo.get_with_user_by_id(profile_id)
    return self._format_staff_member(updated)

  async def remove_staff_member(self, profile_id: int) -> None:
    profile = await self.staff_repo.get_by_id(profile_id)
    if not profile:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found"
      )
    await self.staff_repo.delete(profile.id)

  def _format_staff_member(self, profile: StaffProfile) -> StaffMemberResponse:
    """Helper to format staff profile with user data"""
    user = profile.user
    if not user:
      raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="User data missing (check SQL join)",
      )

    return StaffMemberResponse(
      id=profile.id,
      user_id=profile.user_id,
      venue_id=profile.venue_id,
      role=profile.role,
      created_at=profile.created_at,
      user={
        "id": user.id,
        "email": user.email,
        "phone": user.phone,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "avatar_url": user.avatar_url,
        "role": user.role.value,
      },
    )
