from typing import Any
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import declarative_base, DeclarativeMeta


class CustomBase:
  @declared_attr
  def __table_args__(cls) -> dict[str, Any]:
    return {"schema": "auth"}


Base: DeclarativeMeta = declarative_base(cls=CustomBase)
