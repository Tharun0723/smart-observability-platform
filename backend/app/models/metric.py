from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Index,
    func,
)

from app.db.database import Base


class Metric(Base):
    """Stores infrastructure metrics received from collectors."""

    __tablename__ = "metrics"

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

    metric_name = Column(String(100), nullable=False)

    value = Column(Float, nullable=False)

    unit = Column(String(30), nullable=True)

    # Time when the collector measured the metric.
    recorded_at = Column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Time when the backend received the metric.
    received_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            "ix_metrics_tenant_recorded_at",
            "tenant_id",
            "recorded_at",
        ),
        Index(
            "ix_metrics_collector_recorded_at",
            "collector_id",
            "recorded_at",
        ),
    )