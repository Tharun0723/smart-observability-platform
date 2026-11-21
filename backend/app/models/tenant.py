
from sqlalchemy import Column, Integer, String, DateTime, func

from app.db.database import Base


class Tenant(Base):
    """Represents a customer organization."""

    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String(150), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
