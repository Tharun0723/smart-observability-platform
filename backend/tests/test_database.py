from app.models import Tenant, Collector


def test_create_tenant(db_session):
    tenant = Tenant(name="Company A")

    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    assert tenant.id is not None
    assert tenant.name == "Company A"


def test_create_collector(db_session):
    tenant = Tenant(name="Company B")

    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    collector = Collector(
        tenant_id=tenant.id,
        name="Production Collector"
    )

    db_session.add(collector)
    db_session.commit()
    db_session.refresh(collector)

    assert collector.id is not None
    assert collector.tenant_id == tenant.id
    assert collector.is_active is True