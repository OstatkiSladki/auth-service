from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Enum as SQLEnum,
    func,
)
from sqlalchemy.orm import relationship

from src.db.base import Base
from src.db.models.enums import StaffRole

class StaffProfile(Base):
    __tablename__ = "staff_profiles"

    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False, unique=True)
    venue_id = Column(BigInteger, nullable=False)
    role = Column(
        SQLEnum(StaffRole, name="staff_role", schema="auth"),
        nullable=False,
        default=StaffRole.STAFF,
        server_default=StaffRole.STAFF.value,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="staff_profile")

    __table_args__ = (
        Index("staff_profiles_idx_venue", "venue_id"),
        Index("staff_profiles_idx_user", "user_id"),
        {"schema": "auth"}
    )
