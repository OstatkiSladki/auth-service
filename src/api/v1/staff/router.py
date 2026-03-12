from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Query
from src.schemas.staff import (
  StaffMemberResponse,
  AddStaffMemberRequest,
  UpdateStaffProfileRequest,
  StaffListPaginatedResponse,
  StaffFilterParams,
)
from src.db.models.user import User
from src.services.staff import StaffService
from src.api.dependencies import get_current_user, get_staff_service
from src.api.permissions import (
  check_venue_manager_permission,
  get_current_venue_manager,
)

router = APIRouter(tags=["Staff Management"])


@router.post(
  "/venues/{venue_id}/staff",
  response_model=StaffMemberResponse,
  status_code=status.HTTP_201_CREATED,
)
async def add_staff(
  venue_id: int,
  req: AddStaffMemberRequest,
  manager: User = Depends(get_current_venue_manager),
  staff_service: StaffService = Depends(get_staff_service),
):
  return await staff_service.add_staff_member(venue_id, req.user_email, req.role)


@router.get("/venues/{venue_id}/staff", response_model=StaffListPaginatedResponse)
async def list_staff(
  venue_id: int,
  params: Annotated[StaffFilterParams, Query()],
  manager: User = Depends(get_current_venue_manager),
  staff_service: StaffService = Depends(get_staff_service),
):
  return await staff_service.get_staff_by_venue_paginated(venue_id, params)


@router.get("/staff/{profile_id}", response_model=StaffMemberResponse)
async def get_staff_profile(
  profile_id: int,
  user: User = Depends(get_current_user),
  staff_service: StaffService = Depends(get_staff_service),
):
  profile = await staff_service.get_staff_profile(profile_id)

  # Allow if it's the user's own profile, or if user is a manager in the same venue
  if user.staff_profile and user.staff_profile.id == profile_id:
    return profile

  check_venue_manager_permission(user, profile.venue_id)
  return profile


@router.patch("/staff/{profile_id}", response_model=StaffMemberResponse)
async def update_staff_profile(
  profile_id: int,
  req: UpdateStaffProfileRequest,
  user: User = Depends(get_current_user),
  staff_service: StaffService = Depends(get_staff_service),
):
  profile = await staff_service.get_staff_profile(profile_id)
  check_venue_manager_permission(user, profile.venue_id)

  if req.role:
    return await staff_service.update_staff_profile(profile_id, req.role)
  return profile


@router.delete("/staff/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_staff(
  profile_id: int,
  user: User = Depends(get_current_user),
  staff_service: StaffService = Depends(get_staff_service),
):
  profile = await staff_service.get_staff_profile(profile_id)
  check_venue_manager_permission(user, profile.venue_id)
  await staff_service.remove_staff_member(profile_id)
