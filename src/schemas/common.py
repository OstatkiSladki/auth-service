from pydantic import BaseModel, ConfigDict
from typing import Optional


class MessageResponse(BaseModel):
  message: str


class ErrorDetail(BaseModel):
  error: str


class TokenPayload(BaseModel):
  sub: str
  type: str
  exp: Optional[int] = None
  role: str
