import jwt
from fastapi import APIRouter, Depends, Response, Request
from src.schemas.auth import (
  RegisterRequest,
  LoginRequest,
  PasswordResetRequest,
  PasswordResetConfirm,
  EmailVerifyRequest,
  IntrospectResponse,
)
from src.schemas.common import MessageResponse
from src.schemas.user import UserProfileResponse
from src.services.auth import AuthService
from src.api.dependencies import (
  get_auth_service,
  get_bearer_token,
  get_current_user_token,
  get_user_repo,
)
from src.core.config import settings
from src.core.security import decode_token
from src.db.repositories.user import UserRepository
from src.api.v1.auth.utils import _set_cookies

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserProfileResponse, status_code=201)
async def register(
  req: RegisterRequest,
  response: Response,
  auth_service: AuthService = Depends(get_auth_service),
):
  user, access_token, refresh_token = await auth_service.register(req)
  _set_cookies(response, access_token, refresh_token)
  return user


@router.post("/login", response_model=UserProfileResponse, status_code=200)
async def login(
  req: LoginRequest,
  response: Response,
  auth_service: AuthService = Depends(get_auth_service),
):
  user, access_token, refresh_token = await auth_service.login(req)
  _set_cookies(response, access_token, refresh_token)
  return user


@router.post("/refresh", response_model=MessageResponse, status_code=200)
async def refresh(
  request: Request,
  response: Response,
  auth_service: AuthService = Depends(get_auth_service),
):
  refresh_token = request.cookies.get("refresh_token")
  if not refresh_token:
    # Fallback for when frontend sends it wrong, though specification says cookie only
    return Response(status_code=401)

  new_access_token = await auth_service.refresh_tokens(refresh_token)

  response.set_cookie(
    key="access_token",
    value=new_access_token,
    httponly=True,
    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    path="/api/v1",
    samesite="lax",
    secure=settings.ENVIRONMENT != "development",
  )
  return MessageResponse(message="Token refreshed")


@router.post("/logout", response_model=MessageResponse, status_code=200)
async def logout(
  request: Request,
  response: Response,
  auth_service: AuthService = Depends(get_auth_service),
  current=Depends(get_current_user_token),
):
  refresh_token = request.cookies.get("refresh_token")
  await auth_service.logout(refresh_token)
  response.delete_cookie(key="access_token", path="/api/v1")
  response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")
  return MessageResponse(message="Logged out")


@router.post("/introspect", response_model=IntrospectResponse, status_code=200)
async def introspect(
  token: str = Depends(get_bearer_token),
  user_repo: UserRepository = Depends(get_user_repo),
):
  try:
    payload = decode_token(token)
  except jwt.ExpiredSignatureError:
    return IntrospectResponse(valid=False, error_code="expired")
  except jwt.InvalidTokenError:
    return IntrospectResponse(valid=False, error_code="invalid")

  if payload.get("type") != "access":
    return IntrospectResponse(valid=False, error_code="wrong_type")

  sub = payload.get("sub")
  if not sub:
    return IntrospectResponse(valid=False, error_code="invalid")

  try:
    user_id = int(sub)
  except (TypeError, ValueError):
    return IntrospectResponse(valid=False, error_code="invalid")

  user = await user_repo.get_user_with_staff_profile(user_id)
  if user is None or user.deleted_at is not None:
    return IntrospectResponse(valid=False, error_code="user_not_found")

  if not user.is_active:
    return IntrospectResponse(valid=False, error_code="inactive")

  venue_id = user.staff_profile.venue_id if user.staff_profile else None

  return IntrospectResponse(
    valid=True,
    user_id=user.id,
    email=user.email,
    role=user.role.value if hasattr(user.role, "value") else user.role,
    is_active=user.is_active,
    is_verified=user.is_verified,
    venue_id=venue_id,
    exp=payload.get("exp"),
  )


@router.post("/password/reset-request", response_model=MessageResponse)
async def password_reset_request(req: PasswordResetRequest):
  # TODO: Implement email sending logic
  return MessageResponse(message="Instructions sent if email exists")


@router.post("/password/reset", response_model=MessageResponse)
async def password_reset(req: PasswordResetConfirm):
  # TODO: Implement complete token verification and password reset logic in AuthService
  return MessageResponse(message="Password reset successfully")


@router.post("/email/verify", response_model=MessageResponse)
async def email_verify(req: EmailVerifyRequest):
  # TODO: Implement email verification logic
  return MessageResponse(message="Email verified successfully")
