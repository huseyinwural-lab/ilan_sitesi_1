
import pytest
from unittest.mock import MagicMock, patch
import uuid
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from app.services.pricing_service import PricingService
from app.models.pricing import PriceConfig, FreeQuotaConfig, ListingConsumptionLog
from app.models.commercial import DealerSubscription, DealerPackage
from app.models.dealer import Dealer, DealerApplication
from app.models.billing import Invoice, VatRate
from app.database import AsyncSessionLocal, engine
import pytest_asyncio

@pytest_asyncio.fixture(autouse=True)
async def cleanup_engine():
    yield
    await engine.dispose()

@pytest.mark.asyncio
async def test_waterfall_pricing_flow():
    dealer_id = uuid.uuid4()
    user_id = uuid.uuid4()
    app_id = uuid.uuid4()
    
    async with AsyncSessionLocal() as session:
        # 1. Setup Configs
        # Free Quota: 10 / 30 Days
        session.add(FreeQuotaConfig(country="DE", segment="dealer", quota_amount=10, period_days=30, is_active=True))
        
        # Price Config: 5.00 EUR
        session.add(PriceConfig(country="DE", segment="dealer", pricing_type="pay_per_listing", unit_price_net=5.00, currency="EUR", valid_from=datetime.now(timezone.utc)))
        
        # VAT: 19%
        session.add(VatRate(country="DE", rate=19.00, valid_from=datetime.now(timezone.utc)))
        
        # Dealer Subscription: 50 limit, 0 used
        # Mocking tables directly to avoid dependency hell
        pkg_id = uuid.uuid4()
        session.add(DealerPackage(id=pkg_id, key="TEST", country="DE", name={"en": "T"}, price_net=10, currency="EUR", duration_days=30, listing_limit=50))
        
        # Need Dealer Application record for FK
        session.add(DealerApplication(id=app_id, country="DE", dealer_type="auto", company_name="Test App", contact_name="Tester", contact_email="t@t.com", status="approved"))
        
        # Need Dealer record for FK
        session.add(Dealer(id=dealer_id, country="DE", dealer_type="auto", company_name="Test", application_id=app_id))
        
        # Need Invoice record for FK (subscription -> invoice)
        inv_id = uuid.uuid4()
        session.add(Invoice(id=inv_id, invoice_no="INV-TEST-PRICE", country="DE", currency="EUR", customer_type="dealer", customer_ref_id=dealer_id, customer_name="Test", status="paid", gross_total=10, net_total=10, tax_total=0, tax_rate_snapshot=0))
        
        await session.flush() # Ensure parents exist before child
        
        session.add(DealerSubscription(
            dealer_id=dealer_id,
            package_id=pkg_id,
            invoice_id=inv_id,
            start_at=datetime.now(timezone.utc),
            end_at=datetime.now(timezone.utc) + timedelta(days=30),
            status="active",
            included_listing_quota=50,
            used_listing_quota=0
        ))
        
        await session.commit()
        
        service = PricingService(session)
        
        # === SCENARIO START ===
        
        # 1. Consume Free Quota (10 times)
        for i in range(10):
            result = await service.calculate_listing_fee(str(dealer_id), "DE", str(user_id))
            assert result.is_free == True
            assert result.source == "free_quota"
            assert result.charge_amount == 0
            
            # Commit usage
            await service.commit_usage(result, str(uuid.uuid4()), str(dealer_id), str(user_id))
            
        # 2. Consume Package Quota (50 times)
        for i in range(50):
            result = await service.calculate_listing_fee(str(dealer_id), "DE", str(user_id))
            assert result.is_covered_by_package == True
            assert result.source == "subscription_quota"
            assert result.charge_amount == 0
            
            # Commit usage
            await service.commit_usage(result, str(uuid.uuid4()), str(dealer_id), str(user_id))
            
        # 3. Pay Per Listing (Waterall End)
        result = await service.calculate_listing_fee(str(dealer_id), "DE", str(user_id))
        
        assert result.is_free == False
        assert result.is_covered_by_package == False
        assert result.source == "paid_extra"
        assert result.charge_amount == Decimal("5.00")
        assert result.vat_rate == Decimal("19.00")
        # 5.00 + 19% = 5.95
        assert result.gross_amount == Decimal("5.95")
