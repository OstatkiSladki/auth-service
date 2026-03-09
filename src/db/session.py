from asyncio import current_task

from sqlalchemy.ext.asyncio import (
  AsyncSession,
  async_sessionmaker,
  create_async_engine,
  async_scoped_session,
)
from src.core.config import settings

engine = create_async_engine(
  settings.DATABASE_URL,
  echo=settings.ENVIRONMENT == "development",
  future=True,
  pool_size=10,
  max_overflow=10,
)

async_session_factory = async_sessionmaker(
  engine, class_=AsyncSession, expire_on_commit=False
)

AsyncScopedSession = async_scoped_session(async_session_factory, scopefunc=current_task)


async def get_db() -> AsyncSession:
  async with async_session_factory() as session:
    yield session
