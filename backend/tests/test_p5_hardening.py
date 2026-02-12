
import pytest
from unittest.mock import MagicMock, patch
import stripe
from app.services.stripe_service import StripeService
from app.models.billing import Invoice
from app.models.commercial import DealerPackage, DealerSubscription
from app.models.dealer import Dealer, DealerApplication
from sqlalchemy import select
import uuid
import os
from httpx import AsyncClient, ASGITransport
from server import app
from app.dependencies import get_current_user
from app.database import engine, AsyncSessionLocal
import pytest_asyncio
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import asyncio

@pytest_asyncio.fixture(autouse=True)
async def cleanup_engine():
    yield
    await engine.dispose()

async def mock_get_current_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "admin@platform.com"
    user.role = "super_admin"
    return user

@pytest.fixture
def local_client():
    app.dependency_overrides[get_current_user] = mock_get_current_user
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

@pytest.mark.asyncio
async def test_quota_concurrency_stress(local_client):
    # Setup Dealer & Subscription with 10 Quota
    async with AsyncSessionLocal() as session:
        # Create Dealer App
        app_id = uuid.uuid4()
        session.add(DealerApplication(id=app_id, country="DE", dealer_type="auto", company_name="Stress", contact_name="T", contact_email="t@t.com", status="approved"))
        await session.flush()
        
        # Dealer
        dealer = Dealer(country="DE", dealer_type="auto", company_name="Stress", application_id=app_id, is_active=True)
        session.add(dealer)
        await session.flush()
        
        # Package
        pkg = DealerPackage(key="STRESS", country="DE", name={"en": "Stress"}, price_net=10, currency="EUR", duration_days=30, listing_limit=10, premium_quota=0, is_active=True)
        session.add(pkg)
        await session.flush()
        
        # Invoice
        inv = Invoice(invoice_no=f"INV-{uuid.uuid4().hex[:6]}", country="DE", currency="EUR", customer_type="dealer", customer_ref_id=dealer.id, customer_name="Stress", status="paid", gross_total=10, net_total=10, tax_total=0, tax_rate_snapshot=0)
        session.add(inv)
        await session.flush()
        
        # Subscription (Quota = 10)
        sub = DealerSubscription(dealer_id=dealer.id, package_id=pkg.id, invoice_id=inv.id, start_at=datetime.now(timezone.utc), end_at=datetime.now(timezone.utc)+timedelta(days=30), status="active", remaining_listing_quota=10)
        session.add(sub)
        await session.commit()
        dealer_id = str(dealer.id)

    # Fire 50 concurrent requests
    async with local_client as client:
        tasks = []
        for i in range(50):
            tasks.append(client.post(f"/api/v1/commercial/dealers/{dealer_id}/listings", json={
                "title": f"Car {i}", "description": "D", "module": "vehicle", "price": 1000, "currency": "EUR"
            }))
            
        responses = await asyncio.gather(*tasks)
        
        success_count = sum(1 for r in responses if r.status_code == 200)
        fail_count = sum(1 for r in responses if r.status_code == 403)
        
        print(f"Concurrency Result: Success={success_count}, Fail={fail_count}")
        
        # Verify
        assert success_count == 10
        assert fail_count == 40
        
        # Verify DB State
        async with AsyncSessionLocal() as session:
            sub = (await session.execute(select(DealerSubscription).where(DealerSubscription.dealer_id == uuid.UUID(dealer_id)))).scalar_one()
            assert sub.remaining_listing_quota == 0
            assert sub.remaining_listing_quota >= 0 # Should never be negative
