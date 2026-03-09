from typing import Generic, TypeVar, Type, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from src.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
  def __init__(self, model: Type[ModelType], session: AsyncSession):
    self.model = model
    self.session = session

  async def get_by_id(self, id: Any) -> Optional[ModelType]:
    query = select(self.model).where(self.model.id == id)
    result = await self.session.execute(query)
    return result.scalars().first()

  async def create(self, **kwargs) -> ModelType:
    db_obj = self.model(**kwargs)
    self.session.add(db_obj)
    await self.session.commit()
    await self.session.refresh(db_obj)
    return db_obj

  async def update(self, db_obj: ModelType, **kwargs) -> ModelType:
    for key, value in kwargs.items():
      setattr(db_obj, key, value)
    self.session.add(db_obj)
    await self.session.commit()
    await self.session.refresh(db_obj)
    return db_obj

  async def delete(self, id: Any) -> None:
    query = delete(self.model).where(self.model.id == id)
    await self.session.execute(query)
    await self.session.commit()
