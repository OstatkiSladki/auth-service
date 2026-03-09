from typing import Optional
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from src.db.models.enums import StaffRole
from src.schemas.user import UserProfileShort


class StaffProfileBase(BaseModel):
  venue_id: int
  role: StaffRole


class StaffProfileResponse(StaffProfileBase):
  id: int
  user_id: int

  model_config = ConfigDict(from_attributes=True)


class StaffMemberResponse(BaseModel):
  """Full staff member response with complete user data"""

  id: int
  user_id: int
  venue_id: int
  role: StaffRole
  created_at: datetime
  user: UserProfileShort

  model_config = ConfigDict(from_attributes=True)


class AddStaffMemberRequest(BaseModel):
  user_email: str
  role: StaffRole


class UpdateStaffProfileRequest(BaseModel):
  role: Optional[StaffRole] = None


class CreateMyStaffRequest(BaseModel):
  venue_id: int


class StaffListResponse(BaseModel):
  items: list[StaffProfileResponse]


class StaffListPaginatedResponse(BaseModel):
  """Paginated staff list with metadata"""

  items: list[StaffMemberResponse]
  total: int
  offset: int
  limit: int


class StaffSortField(str, Enum):
  CREATED_AT = "created_at"
  ID = "id"
  ROLE = "role"


class StaffFilterParams(BaseModel):
  page: int = (Field(1, ge=1, description="Page number"),)
  limit: int = (Field(20, ge=1, le=100, description="Items per page"),)
  role: Optional[StaffRole] = (Field(None, description="Filter by staff role"),)
  sort_by: str = Field(
    "created_at",
    description="Sort field name. Use '-' prefix for descending order (e.g. '-created_at')",
  )
