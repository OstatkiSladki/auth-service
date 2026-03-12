from datetime import datetime, timedelta, timezone
from typing import Any, Union
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from src.core.config import settings

ph = PasswordHasher()


def get_password_hash(password: str) -> str:
  return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
  try:
    return ph.verify(hashed_password, plain_password)
  except VerifyMismatchError:
    return False


def create_access_token(subject: Union[str, Any], role: str) -> str:
  expire = datetime.now(timezone.utc) + timedelta(
    minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
  )
  to_encode = {"exp": expire, "sub": str(subject), "type": "access", "role": role}
  encoded_jwt = jwt.encode(
    to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
  )
  return encoded_jwt


def create_refresh_token(subject: Union[str, Any], role: str) -> str:
  expire = datetime.now(timezone.utc) + timedelta(
    days=settings.REFRESH_TOKEN_EXPIRE_DAYS
  )
  to_encode = {"exp": expire, "sub": str(subject), "type": "refresh", "role": role}
  encoded_jwt = jwt.encode(
    to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
  )
  return encoded_jwt


def create_action_token(
  subject: Union[str, Any], action_type: str, expires_delta: timedelta
) -> str:
  expire = datetime.now(timezone.utc) + expires_delta
  to_encode = {"exp": expire, "sub": str(subject), "type": action_type}
  encoded_jwt = jwt.encode(
    to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
  )
  return encoded_jwt


def decode_token(token: str) -> dict:
  return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
