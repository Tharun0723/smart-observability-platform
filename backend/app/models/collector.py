from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    func
)

from app.db.database import Base


class Collector(Base):
    """Represents a registered local telemetry collector."""

    __tablename__ = "collectors"

    id = Column(Integer, primary_key=True, index=True)

    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id"),
        nullable=False,
        index=True
    )

    name = Column(String(150), nullable=False)

    # Store the hash, never the original collector secret.
    # Nullable allows existing collectors to remain in the database.
    secret_hash = Column(
        String(64),
        nullable=True,
        unique=True,
        index=True
    )

    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    last_seen_at = Column(DateTime(timezone=True), nullable=True)