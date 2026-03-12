from fastapi import Depends, HTTPException, status
from src.db.models.user import User
from src.db.models.enums import StaffRole
from src.api.dependencies import get_current_user


def check_venue_manager_permission(user: User, venue_id: int) -> bool:
  """Check if user has manager/admin permissions for a venue"""
  if user.role in [StaffRole.ADMIN, StaffRole.OWNER]:
    return True
  if not user.staff_profile:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN, detail="No staff profile"
    )
  if user.staff_profile.venue_id != venue_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized for this venue"
    )
  if user.staff_profile.role not in [
    StaffRole.MANAGER,
    StaffRole.ADMIN,
    StaffRole.OWNER,
  ]:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role privileges"
    )
  return True


def get_current_venue_manager(
  venue_id: int, user: User = Depends(get_current_user)
) -> User:
  check_venue_manager_permission(user, venue_id)
  return user
