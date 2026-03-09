from typing import Optional, Sequence
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from src.db.repositories.base import BaseRepository
from src.db.models.user import User


class UserRepository(BaseRepository[User]):
  def __init__(self, session):
    super().__init__(User, session)

  async def get_by_email(self, email: str) -> Optional[User]:
    query = select(self.model).options(selectinload(self.model.staff_profile)).where(self.model.email == email)
    result = await self.session.execute(query)
    return result.scalars().first()

  async def get_by_phone(self, phone: str) -> Optional[User]:
    query = select(self.model).options(selectinload(self.model.staff_profile)).where(self.model.phone == phone)
    result = await self.session.execute(query)
    return result.scalars().first()

  async def get_user_with_staff_profile(self, user_id: int) -> Optional[User]:
    query = (
      select(self.model)
      .options(selectinload(self.model.staff_profile))
      .where(self.model.id == user_id)
    )
    result = await self.session.execute(query)
    return result.scalars().first()

  async def search_by_email(self, email_prefix: str, limit: int = 10) -> Sequence[User]:
    query = (
      select(self.model).where(self.model.email.ilike(f"{email_prefix}%")).limit(limit)
    )
    result = await self.session.execute(query)
    return result.scalars().all()
