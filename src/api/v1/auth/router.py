from fastapi import APIRouter, Depends, Response, Request
from src.schemas.auth import (
  RegisterRequest,
  LoginRequest,
  PasswordResetRequest,
  PasswordResetConfirm,
  EmailVerifyRequest,
)
from src.schemas.common import MessageResponse
from src.schemas.user import UserProfileResponse
from src.services.auth import AuthService
from src.api.dependencies import get_auth_service, get_current_user_token
from src.core.config import settings
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
