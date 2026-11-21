import pytest

from pydantic import ValidationError

from app.schemas.tenant import TenantCreate
from app.schemas.collector import CollectorProvision


def test_valid_tenant():
    tenant = TenantCreate(name="Company A")

    assert tenant.name == "Company A"


def test_empty_tenant_name_rejected():
    with pytest.raises(ValidationError):
        TenantCreate(name="")


def test_valid_collector():
    collector = CollectorProvision(
        tenant_id=1,
        name="Production Collector"
    )

    assert collector.tenant_id == 1


def test_invalid_collector_tenant_rejected():
    with pytest.raises(ValidationError):
        CollectorProvision(
            tenant_id=0,
            name="Test Collector"
        )