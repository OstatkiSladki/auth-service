from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from src.schemas.auth import RegisterRequest, LoginRequest
from src.db.repositories.user import UserRepository
from src.db.repositories.token import RefreshTokenRepository
from src.core.security import (
  get_password_hash,
  verify_password,
  create_access_token,
  create_refresh_token,
  decode_token,
)
from src.core.config import settings
from src.db.models.user import User


class AuthService:
  def __init__(self, user_repo: UserRepository, token_repo: RefreshTokenRepository):
    self.user_repo = user_repo
    self.token_repo = token_repo

  async def register(self, req: RegisterRequest) -> tuple[User, str, str]:
    if await self.user_repo.get_by_email(req.email):
      raise HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
      )
    if req.phone and await self.user_repo.get_by_phone(req.phone):
      raise HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail="Phone already registered"
      )

    hashed_password = get_password_hash(req.password)

    user = await self.user_repo.create(
      email=req.email,
      password_hash=hashed_password,
      first_name=req.first_name,
      last_name=req.last_name,
      phone=req.phone,
      privacy_policy_accepted_at=datetime.now(timezone.utc)
      if req.privacy_policy_accepted
      else None,
    )
    
    user.staff_profile = None

    return await self._create_tokens(user)

  async def login(self, req: LoginRequest) -> tuple[User, str, str]:
    user = await self.user_repo.get_by_email(req.email)
    if not user or not verify_password(req.password, user.password_hash):
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
      )

    if not user.is_active:
      raise HTTPException(
        status_code=status.HTTP_423_LOCKED, detail="User is not active"
      )

    return await self._create_tokens(user)

  async def refresh_tokens(self, refresh_token_hash: str) -> str:
    token_record = await self.token_repo.get_valid_token(refresh_token_hash)
    if not token_record or token_record.expires_at < datetime.now(timezone.utc):
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalid or expired"
      )

    user = await self.user_repo.get_by_id(token_record.user_id)
    if not user or not user.is_active:
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN, detail="User not active"
      )

    await self.token_repo.update(token_record, last_used_at=datetime.now(timezone.utc))
    return create_access_token(user.id, user.role.value)

  async def logout(self, refresh_token_hash: str):
    if refresh_token_hash:
      await self.token_repo.revoke_token(refresh_token_hash)

  async def _create_tokens(self, user: User) -> tuple[User, str, str]:
    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id, user.role.value)

    expires_at = datetime.now(timezone.utc) + timedelta(
      days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    await self.token_repo.create(
      user_id=user.id,
      token_hash=refresh_token,
      expires_at=expires_at,
    )

    return user, access_token, refresh_token
