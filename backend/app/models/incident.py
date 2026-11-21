from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
    func,
)

from app.db.database import Base


class Incident(Base):
    """Stores AIOps-generated infrastructure incidents."""

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)

    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id"),
        nullable=False,
        index=True,
    )

    # Stable fingerprint helps identify repeated incidents.
    fingerprint = Column(
        String(128),
        nullable=False,
    )

    title = Column(String(200), nullable=False)

    description = Column(Text, nullable=True)

    source = Column(String(100), nullable=True)

    # info, low, medium, high, critical
    severity = Column(String(20), nullable=False, index=True)

    # low, medium, high, critical
    priority = Column(String(20), nullable=False)

    # open, acknowledged, investigating, resolved, closed
    status = Column(
        String(30),
        nullable=False,
        default="open",
    )

    affected_resource = Column(String(200), nullable=True)

    correlation_key = Column(String(128), nullable=True, index=True)

    recommendation = Column(Text, nullable=True)

    first_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    last_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    occurrence_count = Column(
        Integer,
        nullable=False,
        default=1,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "fingerprint",
            name="uq_incident_tenant_fingerprint",
        ),
        Index(
            "ix_incidents_tenant_status",
            "tenant_id",
            "status",
        ),
        Index(
            "ix_incidents_tenant_severity",
            "tenant_id",
            "severity",
        ),
    )