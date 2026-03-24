from pydantic import BaseModel, Field, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
  email: EmailStr
  password: str = Field(..., min_length=8)
  first_name: str
  last_name: Optional[str] = None
  phone: Optional[str] = None
  privacy_policy_accepted: bool


class LoginRequest(BaseModel):
  email: EmailStr
  password: str


class PasswordResetRequest(BaseModel):
  email: EmailStr


class PasswordResetConfirm(BaseModel):
  token: str
  new_password: str = Field(..., min_length=8)


class EmailVerifyRequest(BaseModel):
  token: str
