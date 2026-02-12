
import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.jobs.expiry_worker import run_expiry_job
from app.models.commercial import DealerSubscription, DealerPackage
from app.models.dealer import Dealer, DealerApplication
from app.models.billing import Invoice, InvoiceItem
from app.models.core import AuditLog
from app.models.payment import PaymentAttempt, Refund
from app.models.pricing import ListingConsumptionLog
from app.database import AsyncSessionLocal, engine
from sqlalchemy import select, delete
import pytest_asyncio

@pytest_asyncio.fixture(autouse=True)
async def cleanup_engine():
    yield
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        # CLEANUP
        await session.execute(delete(AuditLog).where(AuditLog.action == "SYSTEM_EXPIRE"))
        await session.execute(delete(Refund))
        await session.execute(delete(PaymentAttempt))
        await session.execute(delete(ListingConsumptionLog))
        await session.execute(delete(InvoiceItem))
        await session.execute(delete(DealerSubscription))
        await session.execute(delete(DealerPackage))
        await session.execute(delete(Invoice))
        await session.execute(delete(Dealer))
        await session.execute(delete(DealerApplication))
        await session.commit()
        yield session
        await session.close()

@pytest.mark.asyncio
async def test_expiry_job_logic(db_session):
    # 1. Setup Data
    # Dealer
    app_id = uuid.uuid4()
    dealer_id = uuid.uuid4()
    db_session.add(DealerApplication(id=app_id, country="DE", dealer_type="auto", company_name="Test", contact_name="T", contact_email="t@t.com", status="approved"))
    await db_session.flush()
    db_session.add(Dealer(id=dealer_id, application_id=app_id, country="DE", dealer_type="auto", company_name="Test"))
    await db_session.flush()
    
    # Package
    pkg_id = uuid.uuid4()
    db_session.add(DealerPackage(id=pkg_id, key="TEST", country="DE", name={"en": "T"}, price_net=10, currency="EUR", duration_days=30))
    await db_session.flush()
    
    # Invoice (Required for FK)
    inv_id_1 = uuid.uuid4()
    inv_id_2 = uuid.uuid4()
    db_session.add(Invoice(id=inv_id_1, invoice_no="INV-1", country="DE", currency="EUR", customer_type="dealer", customer_ref_id=dealer_id, customer_name="T", status="paid", gross_total=10, net_total=10, tax_total=0, tax_rate_snapshot=0))
    db_session.add(Invoice(id=inv_id_2, invoice_no="INV-2", country="DE", currency="EUR", customer_type="dealer", customer_ref_id=dealer_id, customer_name="T", status="paid", gross_total=10, net_total=10, tax_total=0, tax_rate_snapshot=0))
    await db_session.flush()
    
    # Sub 1: EXPIRED (Active status, but end_at in past)
    sub_expired_id = uuid.uuid4()
    db_session.add(DealerSubscription(
        id=sub_expired_id,
        dealer_id=dealer_id,
        package_id=pkg_id,
        invoice_id=inv_id_1,
        start_at=datetime.now(timezone.utc) - timedelta(days=60),
        end_at=datetime.now(timezone.utc) - timedelta(days=1), # Yesterday
        status="active", # Should be updated
        included_listing_quota=10
    ))
    
    # Sub 2: VALID (Active status, end_at in future)
    sub_valid_id = uuid.uuid4()
    db_session.add(DealerSubscription(
        id=sub_valid_id,
        dealer_id=dealer_id,
        package_id=pkg_id,
        invoice_id=inv_id_2,
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc) + timedelta(days=30), # Future
        status="active",
        included_listing_quota=10
    ))
    
    await db_session.commit()
    
    # 2. Run Job
    await run_expiry_job()
    
    # 3. Verify
    async with AsyncSessionLocal() as session:
        # Check Sub 1
        s1 = (await session.execute(select(DealerSubscription).where(DealerSubscription.id == sub_expired_id))).scalar_one()
        assert s1.status == "expired", "Expired subscription should be marked as expired"
        
        # Check Sub 2
        s2 = (await session.execute(select(DealerSubscription).where(DealerSubscription.id == sub_valid_id))).scalar_one()
        assert s2.status == "active", "Valid subscription should remain active"
        
        # Check Audit Log
        logs = (await session.execute(select(AuditLog).where(AuditLog.action == "SYSTEM_EXPIRE"))).scalars().all()
        assert len(logs) == 1
        assert logs[0].new_values["count"] == 1
        assert str(sub_expired_id) in logs[0].new_values["ids"]
