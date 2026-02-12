
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
async def test_dealer_package_flow(local_client):
    # Setup Data manually to be safe
    async with AsyncSessionLocal() as session:
        # Create Package
        pkg = DealerPackage(
            key="TEST_PKG",
            country="DE",
            name={"en": "Test Package"},
            price_net=Decimal("100.00"),
            currency="EUR",
            duration_days=30,
            listing_limit=50,
            premium_quota=5,
            is_active=True
        )
        session.add(pkg)
        
        # Create Application First (Required for Dealer FK)
        app_id = uuid.uuid4()
        dealer_app = DealerApplication(
            id=app_id,
            country="DE",
            dealer_type="auto_dealer",
            company_name="Test Dealer App",
            contact_name="Tester",
            contact_email="test@dealer.com",
            status="approved"
        )
        session.add(dealer_app)
        await session.flush()

        # Create Dealer
        dealer = Dealer(
            country="DE",
            dealer_type="auto_dealer",
            company_name="Test Dealer",
            vat_tax_no="DE999",
            is_active=True,
            application_id=app_id
        )
        session.add(dealer)
        await session.commit()
        await session.refresh(pkg)
        await session.refresh(dealer)
        package_id = str(pkg.id)
        dealer_id = str(dealer.id)

    with patch.dict(os.environ, {"STRIPE_API_KEY": "sk_test_mock", "STRIPE_WEBHOOK_SECRET": "whsec_test"}):
        async with local_client as client:
            # 1. List Packages (DE)
            res = await client.get("/api/v1/commercial/packages?country=DE")
            assert res.status_code == 200, f"List packages failed: {res.text}"
            packages = res.json()
            assert len(packages) > 0, "No packages found for DE"
            found = next((p for p in packages if p["id"] == package_id), None)
            assert found is not None
            
            # 3. Buy Package
            with patch("stripe.checkout.Session.create") as mock_create:
                mock_session = MagicMock()
                mock_session.id = f"cs_test_{uuid.uuid4().hex}"
                mock_session.url = "http://stripe.com/checkout"
                mock_session.payment_intent = f"pi_test_{uuid.uuid4().hex}"
                mock_create.return_value = mock_session
                
                res = await client.post(f"/api/v1/commercial/dealers/{dealer_id}/packages/{package_id}/buy", json={
                    "success_url": "http://ok",
                    "cancel_url": "http://cancel"
                })
                
                assert res.status_code == 200, f"Buy package failed: {res.text}"
                data = res.json()
                checkout_url = data["checkout_url"]
                
                # Check args
                args, kwargs = mock_create.call_args
                assert "client_reference_id" in kwargs
                invoice_id = kwargs["client_reference_id"]
            
            # 4. Webhook Activation
            with patch("stripe.Webhook.construct_event") as mock_construct:
                mock_event = MagicMock()
                mock_event.id = f"evt_{uuid.uuid4().hex}"
                mock_event.type = "checkout.session.completed"
                
                mock_sess_obj = MagicMock()
                mock_sess_obj.id = mock_session.id
                mock_sess_obj.payment_intent = mock_session.payment_intent
                mock_sess_obj.client_reference_id = invoice_id
                mock_sess_obj.metadata = {"invoice_id": invoice_id}
                
                mock_event.data.object = mock_sess_obj
                mock_construct.return_value = mock_event
                
                res = await client.post("/api/v1/payments/webhook/stripe", 
                                       content=b"dummy", 
                                       headers={"Stripe-Signature": "dummy"})
                assert res.status_code == 200, f"Webhook failed: {res.text}"
                
            # 5. Verify Subscription
            res = await client.get(f"/api/invoices/{invoice_id}")
            assert res.json()["status"] == "paid"
            
            # Verify Subscription in DB
            async with AsyncSessionLocal() as session:
                sub = await session.execute(select(DealerSubscription).where(DealerSubscription.invoice_id == uuid.UUID(invoice_id)))
                sub = sub.scalar_one_or_none()
                assert sub is not None
                assert sub.status == "active"
                assert sub.remaining_listing_quota == 50
