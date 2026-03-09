from sqlalchemy import (
  BigInteger,
  Boolean,
  Column,
  DateTime,
  String,
  Text,
  Enum as SQLEnum,
  func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.models.enums import UsersRole


class User(Base):
  __tablename__ = "users"

  id = Column(BigInteger, primary_key=True, index=True)
  email = Column(String(255), nullable=False, unique=True)
  phone = Column(String(20), unique=True, nullable=True)
  password_hash = Column(String(255), nullable=False)
  first_name = Column(String(100), nullable=False)
  last_name = Column(String(100), nullable=True)
  avatar_url = Column(Text, nullable=True)

  role = Column(
    SQLEnum(
      UsersRole,
      name="users_role",
      schema="auth",
      values_callable=lambda obj: [e.value for e in obj],
    ),
    nullable=False,
    default=UsersRole.USER,
    server_default=UsersRole.USER.value,
  )

  is_active = Column(Boolean, default=True, server_default="true")
  is_verified = Column(Boolean, default=False, server_default="false")

  privacy_policy_accepted_at = Column(DateTime(timezone=True), nullable=True)
  default_address = Column(Text, nullable=True)
  preferences_json = Column(JSONB, default={}, server_default="{}")

  created_at = Column(DateTime(timezone=True), server_default=func.now())
  updated_at = Column(
    DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
  )
  deleted_at = Column(DateTime(timezone=True), nullable=True)

  refresh_tokens = relationship(
    "RefreshToken", back_populates="user", cascade="all, delete-orphan"
  )
  staff_profile = relationship(
    "StaffProfile", back_populates="user", uselist=False, cascade="all, delete-orphan"
  )
