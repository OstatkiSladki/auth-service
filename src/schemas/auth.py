from pydantic import BaseModel, Field
from typing import Optional


class RegisterRequest(BaseModel):
  email: str
  password: str = Field(..., min_length=8)
  first_name: str
  last_name: Optional[str] = None
  phone: Optional[str] = None
  privacy_policy_accepted: bool


class LoginRequest(BaseModel):
  email: str
  password: str


class PasswordResetRequest(BaseModel):
  email: str


class PasswordResetConfirm(BaseModel):
  token: str
  new_password: str = Field(..., min_length=8)


class EmailVerifyRequest(BaseModel):
  token: str
