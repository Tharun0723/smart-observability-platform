from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Index,
    func,
)

from app.db.database import Base


class Event(Base):
    """Stores approved security and application event metadata."""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    collector_id = Column(
        Integer,
        ForeignKey("collectors.id"),
        nullable=False,
        index=True,
    )

    event_type = Column(String(60), nullable=False, index=True)

    severity = Column(String(20), nullable=False, index=True)

    source = Column(String(120), nullable=True)

    title = Column(String(200), nullable=False)

    summary = Column(String(500), nullable=True)

    # Time when the event occurred at the customer environment.
    occurred_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Time when the backend received the event.
    received_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_events_tenant_occurred_at",
            "tenant_id",
            "occurred_at",
        ),
        Index(
            "ix_events_tenant_severity",
            "tenant_id",
            "severity",
        ),
        Index(
            "ix_events_collector_occurred_at",
            "collector_id",
            "occurred_at",
        ),
    )