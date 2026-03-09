from typing import Optional, Any, TYPE_CHECKING
from pydantic import BaseModel, EmailStr, ConfigDict
from src.db.models.enums import UsersRole

if TYPE_CHECKING:
  from src.schemas.staff import StaffProfileResponse


class UserProfileShort(BaseModel):
  id: int
  first_name: str
  last_name: Optional[str] = None
  avatar_url: Optional[str] = None

  model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(UserProfileShort):
  email: str  # Fallback to str if EmailStr fails
  phone: Optional[str] = None
  role: UsersRole
  is_active: bool
  is_verified: bool
  default_address: Optional[str] = None
  preferences_json: dict[str, Any] = {}
  staff_profile: Optional["StaffProfileResponse"] = None

  model_config = ConfigDict(from_attributes=True)


class UpdateUserProfileRequest(BaseModel):
  first_name: Optional[str] = None
  last_name: Optional[str] = None
  avatar_url: Optional[str] = None
  default_address: Optional[str] = None
  preferences_json: Optional[dict[str, Any]] = None
