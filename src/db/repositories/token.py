from typing import Optional
from sqlalchemy import select, update, delete
from src.db.repositories.base import BaseRepository
from src.db.models.token import RefreshToken


class RefreshTokenRepository(BaseRepository[RefreshToken]):
  def __init__(self, session):
    super().__init__(RefreshToken, session)

  async def get_valid_token(self, token_hash: str) -> Optional[RefreshToken]:
    query = select(self.model).where(
      self.model.token_hash == token_hash, self.model.is_revoked == False
    )
    result = await self.session.execute(query)
    return result.scalars().first()

  async def revoke_token(self, token_hash: str) -> None:
    query = (
      update(self.model)
      .where(self.model.token_hash == token_hash)
      .values(is_revoked=True)
    )
    await self.session.execute(query)
    await self.session.commit()

  async def revoke_all_for_user(self, user_id: int) -> None:
    query = (
      update(self.model).where(self.model.user_id == user_id).values(is_revoked=True)
    )
    await self.session.execute(query)
    await self.session.commit()
