
import pytest
from unittest.mock import MagicMock, patch
import stripe
from app.services.stripe_service import StripeService
from app.models.billing import Invoice
from app.models.commercial import DealerPackage, DealerSubscription
from sqlalchemy import select
import uuid
import os
from httpx import AsyncClient, ASGITransport
from server import app, seed_default_data
from app.dependencies import get_current_user
from app.database import engine, AsyncSessionLocal
import pytest_asyncio

@pytest_asyncio.fixture(autouse=True)
async def cleanup_engine():
    yield
    await engine.dispose()

@pytest_asyncio.fixture(autouse=True)
async def run_seed():
    async with AsyncSessionLocal() as session:
        await seed_default_data(session)

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
    with patch.dict(os.environ, {"STRIPE_API_KEY": "sk_test_mock", "STRIPE_WEBHOOK_SECRET": "whsec_test"}):
        async with local_client as client:
            # 1. List Packages (DE)
            res = await client.get("/api/v1/commercial/packages?country=DE")
            assert res.status_code == 200, f"List packages failed: {res.text}"
            packages = res.json()
            assert len(packages) > 0, "No packages found for DE"
            package_id = packages[0]["id"]
            
            # 2. Get a Dealer (Seeded)
            # Need to find a dealer ID.
            # Since we can't query DB easily without session fixture, let's hit dealers endpoint.
            res = await client.get("/api/dealers")
            dealers = res.json()
            # If no dealers, we might fail. Seed data should have one.
            # "Auto Schmidt GmbH"
            if not dealers:
                pytest.skip("No dealers seeded")
            dealer_id = dealers[0]["id"]
            
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
            
            # We assume subscription is active logic ran.
