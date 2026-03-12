from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.session import get_db
from src.core.security import decode_token
from src.schemas.common import TokenPayload
from src.db.repositories.user import UserRepository
from src.db.repositories.token import RefreshTokenRepository
from src.db.repositories.staff import StaffProfileRepository
from src.services.auth import AuthService
from src.services.user import UserService
from src.services.staff import StaffService
import jwt


async def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
  return UserRepository(db)


async def get_token_repo(db: AsyncSession = Depends(get_db)) -> RefreshTokenRepository:
  return RefreshTokenRepository(db)


async def get_staff_repo(db: AsyncSession = Depends(get_db)) -> StaffProfileRepository:
  return StaffProfileRepository(db)


async def get_auth_service(
  user_repo: UserRepository = Depends(get_user_repo),
  token_repo: RefreshTokenRepository = Depends(get_token_repo),
) -> AuthService:
  return AuthService(user_repo, token_repo)


async def get_user_service(
  user_repo: UserRepository = Depends(get_user_repo),
) -> UserService:
  return UserService(user_repo)


async def get_staff_service(
  staff_repo: StaffProfileRepository = Depends(get_staff_repo),
  user_repo: UserRepository = Depends(get_user_repo),
) -> StaffService:
  return StaffService(staff_repo, user_repo)


def get_current_user_token(request: Request) -> TokenPayload:
  token = request.cookies.get("access_token")
  if not token:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
    )
  try:
    payload = decode_token(token)
    if payload.get("type") != "access":
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
      )
    return TokenPayload(**payload)
  except jwt.ExpiredSignatureError:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
    )
  except jwt.InvalidTokenError:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
    )


async def get_current_user(
  token: TokenPayload = Depends(get_current_user_token),
  user_service: UserService = Depends(get_user_service),
):
  user = await user_service.get_user_profile(int(token.sub))
  return user
