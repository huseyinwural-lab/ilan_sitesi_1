
import pytest
from unittest.mock import MagicMock, patch
import uuid
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from app.services.pricing_service import PricingService, PricingConfigError
from app.models.pricing import PriceConfig, FreeQuotaConfig, ListingConsumptionLog, CountryCurrencyMap
from app.models.commercial import DealerSubscription, DealerPackage
from app.models.dealer import Dealer, DealerApplication
from app.models.billing import Invoice, VatRate, InvoiceItem
from app.database import AsyncSessionLocal, engine
import pytest_asyncio
from sqlalchemy import select, delete

@pytest_asyncio.fixture(autouse=True)
async def cleanup_engine():
    yield
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session():
    async with AsyncSessionLocal() as session:
        # CLEANUP BEFORE TEST
        await session.execute(delete(ListingConsumptionLog))
        await session.execute(delete(InvoiceItem))
        await session.execute(delete(DealerSubscription))
        await session.execute(delete(DealerPackage))
        await session.execute(delete(Invoice))
        await session.execute(delete(Dealer))
        await session.execute(delete(DealerApplication))
        await session.execute(delete(PriceConfig))
        await session.execute(delete(FreeQuotaConfig))
        await session.execute(delete(VatRate))
        await session.execute(delete(CountryCurrencyMap))
        await session.commit()
        
        yield session
        # No rollback needed if we assume dirty DB is fine for next run's cleanup, 
        # but good practice to close.
        await session.close()

@pytest.mark.asyncio
async def test_waterfall_pricing_flow(db_session):
    dealer_id = uuid.uuid4()
    user_id = uuid.uuid4()
    app_id = uuid.uuid4()
    
    # 1. Setup Configs
    # Country Map
    db_session.add(CountryCurrencyMap(country="DE", currency="EUR"))
    
    # Free Quota: 2 (Small number for testing) / 30 Days
    db_session.add(FreeQuotaConfig(country="DE", segment="dealer", quota_amount=2, period_days=30, is_active=True))
    
    # Price Config: 5.00 EUR
    db_session.add(PriceConfig(country="DE", segment="dealer", pricing_type="pay_per_listing", unit_price_net=Decimal("5.00"), currency="EUR", valid_from=datetime.now(timezone.utc)))
    
    # VAT: 19%
    db_session.add(VatRate(country="DE", rate=Decimal("19.00"), valid_from=datetime.now(timezone.utc)))
    
    # Dealer Subscription: 2 limit
    pkg_id = uuid.uuid4()
    db_session.add(DealerPackage(id=pkg_id, key="TEST", country="DE", name={"en": "T"}, price_net=10, currency="EUR", duration_days=30, listing_limit=2))
    
    # Need Dealer Application record for FK
    db_session.add(DealerApplication(id=app_id, country="DE", dealer_type="auto", company_name="Test App", contact_name="Tester", contact_email="t@t.com", status="approved"))
    await db_session.flush() # Flush application first
    
    # Need Dealer record for FK
    db_session.add(Dealer(id=dealer_id, country="DE", dealer_type="auto", company_name="Test", application_id=app_id))
    await db_session.flush() # Flush dealer
    
    # Need Invoice record for Subscription
    sub_inv_id = uuid.uuid4()
    db_session.add(Invoice(id=sub_inv_id, invoice_no=f"INV-SUB-{uuid.uuid4()}", country="DE", currency="EUR", customer_type="dealer", customer_ref_id=dealer_id, customer_name="Test", status="paid", gross_total=10, net_total=10, tax_total=0, tax_rate_snapshot=0))
    await db_session.flush() # Flush invoice
    
    db_session.add(DealerSubscription(
        dealer_id=dealer_id,
        package_id=pkg_id,
        invoice_id=sub_inv_id,
        start_at=datetime.now(timezone.utc),
        end_at=datetime.now(timezone.utc) + timedelta(days=30),
        status="active",
        included_listing_quota=2,
        used_listing_quota=0
    ))
    
    # Need Invoice for Overage (Draft)
    overage_inv_id = uuid.uuid4()
    db_session.add(Invoice(id=overage_inv_id, invoice_no=f"INV-OV-{uuid.uuid4()}", country="DE", currency="EUR", customer_type="dealer", customer_ref_id=dealer_id, customer_name="Test", status="draft", gross_total=0, net_total=0, tax_total=0, tax_rate_snapshot=0))
    
    await db_session.commit()
    
    service = PricingService(db_session)
    
    # === SCENARIO START ===
    
    # 1. Consume Free Quota (2 times)
    for i in range(2):
        listing_id = str(uuid.uuid4())
        result = await service.calculate_listing_fee(str(dealer_id), "DE", listing_id)
        assert result.is_free == True
        assert result.source == "free_quota"
        assert result.charge_amount == 0
        
        # Commit usage
        await service.commit_usage(result, listing_id, str(dealer_id), str(user_id))
        
    # 2. Consume Package Quota (2 times)
    for i in range(2):
        listing_id = str(uuid.uuid4())
        result = await service.calculate_listing_fee(str(dealer_id), "DE", listing_id)
        assert result.is_covered_by_package == True
        assert result.source == "subscription_quota"
        assert result.charge_amount == 0
        
        # Commit usage
        await service.commit_usage(result, listing_id, str(dealer_id), str(user_id))
        
    # Verify Subscription usage is 2
    # New session for verification as commit_usage might have committed
    async with AsyncSessionLocal() as verify_session:
        sub = (await verify_session.execute(select(DealerSubscription).where(DealerSubscription.dealer_id == dealer_id))).scalar_one()
        assert sub.used_listing_quota == 2
        
    # 3. Pay Per Listing (Waterall End)
    listing_id = str(uuid.uuid4())
    result = await service.calculate_listing_fee(str(dealer_id), "DE", listing_id)
    
    assert result.is_free == False
    assert result.is_covered_by_package == False
    assert result.source == "paid_extra"
    assert result.charge_amount == Decimal("5.00")
    assert result.vat_rate == Decimal("19.00")
    # 5.00 + 19% = 5.95
    assert result.gross_amount == Decimal("5.95")
    
    # Commit usage with invoice
    await service.commit_usage(result, listing_id, str(dealer_id), str(user_id), invoice_id=str(overage_inv_id))
    
    # Verify Invoice Item created
    async with AsyncSessionLocal() as verify_session:
        inv_item = (await verify_session.execute(select(InvoiceItem).where(InvoiceItem.invoice_id == overage_inv_id))).scalar_one()
        assert inv_item.unit_price_net == Decimal("5.00")
        assert inv_item.price_source == "paid_extra"
    
@pytest.mark.asyncio
async def test_missing_config_fails(db_session):
    """Fail-fast test"""
    dealer_id = uuid.uuid4()
    # Ensure no FR config exists (cleaned up by fixture)
    service = PricingService(db_session)
    
    # 1. Missing VAT check
    # We expect 'No active VAT' because get_active_vat is called first
    try:
        await service.calculate_listing_fee(str(dealer_id), "FR", str(uuid.uuid4()))
        pytest.fail("Should have raised PricingConfigError for VAT")
    except PricingConfigError as e:
        assert "VAT" in str(e) or "configuration found for country FR" in str(e)

    # 2. Add VAT, Missing Price
    db_session.add(CountryCurrencyMap(country="FR", currency="EUR"))
    db_session.add(VatRate(country="FR", rate=Decimal("20.00"), valid_from=datetime.now(timezone.utc)))
    await db_session.commit()
    
    try:
        await service.calculate_listing_fee(str(dealer_id), "FR", str(uuid.uuid4()))
        pytest.fail("Should have raised PricingConfigError for Price")
    except PricingConfigError as e:
        assert "price configuration" in str(e)
