from src.core.config import settings
from fastapi import Response


def _set_cookies(response: Response, access_token: str, refresh_token: str):
  response.set_cookie(
    key="access_token",
    value=access_token,
    httponly=True,
    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    path="/api/v1",
    samesite="lax",
    secure=settings.ENVIRONMENT != "development",
  )
  response.set_cookie(
    key="refresh_token",
    value=refresh_token,
    httponly=True,
    max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    path="/api/v1/auth/refresh",
    samesite="lax",
    secure=settings.ENVIRONMENT != "development",
  )
