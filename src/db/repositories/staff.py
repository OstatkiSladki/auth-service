from typing import Optional, Sequence
from sqlalchemy import delete, select, func, desc, asc
from sqlalchemy.orm import joinedload, contains_eager
from src.db.repositories.base import BaseRepository
from src.db.models.staff import StaffProfile
from src.db.models.user import User


class StaffProfileRepository(BaseRepository[StaffProfile]):
  def __init__(self, session):
    super().__init__(StaffProfile, session)

  async def get_with_user_by_id(self, profile_id: int) -> Optional[StaffProfile]:
    query = (
      select(self.model)
      .options(joinedload(self.model.user))
      .where(self.model.id == profile_id)
    )
    result = await self.session.execute(query)
    return result.scalars().first()

  async def get_by_user_id(self, user_id: int) -> Optional[StaffProfile]:
    query = select(self.model).where(self.model.user_id == user_id)
    result = await self.session.execute(query)
    return result.scalars().first()

  async def get_by_venue_id(self, venue_id: int) -> Sequence[StaffProfile]:
    query = select(self.model).where(self.model.venue_id == venue_id)
    result = await self.session.execute(query)
    return result.scalars().all()

  async def get_by_venue_id_paginated(
    self,
    venue_id: int,
    page: int = 1,
    limit: int = 20,
    role: Optional[str] = None,
    sort_by: str = "-created_at",
  ) -> tuple[Sequence[StaffProfile], int]:
    """Get paginated staff profiles for a venue with optional filtering and sorting"""
    query = (
      select(self.model)
      .join(self.model.user)
      .options(contains_eager(self.model.user))
      .where(self.model.venue_id == venue_id)
    )

    # Apply role filter
    if role:
      query = query.where(self.model.role == role)

    # Get total count for pagination
    count_query = select(func.count(self.model.id)).where(
      self.model.venue_id == venue_id
    )
    if role:
      count_query = count_query.where(self.model.role == role)
    count_result = await self.session.execute(count_query)
    total = count_result.scalar() or 0

    # Apply sorting
    sort_field = sort_by.lstrip("-")
    is_desc = sort_by.startswith("-")

    sort_map = {
      "created_at": self.model.created_at,
      "first_name": User.first_name,
      "last_name": User.last_name,
      "role": self.model.role,
      "email": User.email,
    }

    if sort_field in sort_map and sort_map[sort_field] is not None:
      sort_col = sort_map[sort_field]
      query = query.order_by(desc(sort_col) if is_desc else asc(sort_col))
    else:
      # Default sort by created_at descending
      query = query.order_by(
        desc(self.model.created_at) if is_desc else asc(self.model.created_at)
      )

    # Apply pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    result = await self.session.execute(query)
    return result.scalars().all(), total

  async def delete_by_venue_id(self, venue_id: int) -> int:
    result = await self.session.execute(
      delete(self.model).where(self.model.venue_id == venue_id)
    )
    return int(result.rowcount or 0)
