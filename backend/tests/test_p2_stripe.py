
import pytest
from unittest.mock import MagicMock, patch
import stripe
from app.services.stripe_service import StripeService
from app.models.billing import Invoice
from sqlalchemy import select
import uuid
import os
from httpx import AsyncClient
from app.backend.server import app
from app.dependencies import get_current_user

# Mock auth to bypass login for these unit tests
async def mock_get_current_user():
    user = MagicMock()
    user.id = uuid.uuid4()
    user.email = "admin@platform.com"
    user.role = "super_admin"
    user.country_scope = ["*"]
    return user

@pytest.fixture
def local_client():
    # Override auth dependency
    app.dependency_overrides[get_current_user] = mock_get_current_user
    return AsyncClient(app=app, base_url="http://test")

@pytest.mark.asyncio
async def test_create_checkout_session_flow(local_client):
    # Set Env for Stripe Key (Mock) - NOW this works because app runs in process
    with patch.dict(os.environ, {"STRIPE_API_KEY": "sk_test_mock"}):
        async with local_client as client:
            # 1. Create Draft Invoice
            res = await client.post("/api/v1/invoices", json={
                "country": "DE",
                "customer_type": "B2C",
                "customer_name": "Stripe Test",
                "customer_email": "stripe@test.com",
                "items": [{"description": "Service", "quantity": 1, "unit_price": 50.0}]
            })
            assert res.status_code == 200
            invoice_id = res.json()["id"]
            
            # 2. Mock Stripe
            with patch("stripe.checkout.Session.create") as mock_create:
                mock_session = MagicMock()
                mock_session.id = "cs_test_123"
                mock_session.url = "https://checkout.stripe.com/test"
                mock_create.return_value = mock_session
                
                # 3. Call Checkout Endpoint
                res = await client.post(f"/api/v1/payments/invoices/{invoice_id}/checkout", json={
                    "success_url": "http://localhost/success",
                    "cancel_url": "http://localhost/cancel"
                })
                
                assert res.status_code == 200
                data = res.json()
                assert data["checkout_url"] == "https://checkout.stripe.com/test"
                
                # Verify Mock Call
                mock_create.assert_called_once()
                args, kwargs = mock_create.call_args
                assert kwargs["mode"] == "payment"
                assert kwargs["client_reference_id"] == invoice_id
                # Check amount (50.0 * 100 = 5000 cents)
                line_items = kwargs["line_items"]
                assert line_items[0]["price_data"]["unit_amount"] == 5000
                assert line_items[0]["price_data"]["currency"] == "eur"

@pytest.mark.asyncio
async def test_stripe_webhook_processing(local_client):
    # Set Env for Webhook Secret
    with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "whsec_test"}):
        async with local_client as client:
            # 1. Create Invoice
            res = await client.post("/api/v1/invoices", json={
                "country": "DE",
                "customer_type": "B2C",
                "customer_name": "Webhook Test",
                "customer_email": "web@test.com",
                "items": [{"description": "Item", "quantity": 1, "unit_price": 100.0}]
            })
            invoice_id = res.json()["id"]
            
            # 2. Mock Webhook Construction
            with patch("stripe.Webhook.construct_event") as mock_construct:
                # Mock Event Object
                mock_event = MagicMock()
                mock_event.id = "evt_test_123"
                mock_event.type = "checkout.session.completed"
                
                mock_session = MagicMock()
                mock_session.client_reference_id = invoice_id
                mock_session.id = "cs_test_completed"
                mock_session.payment_intent = "pi_test_123"
                
                mock_event.data.object = mock_session
                mock_construct.return_value = mock_event
                
                # 3. Call Webhook Endpoint
                res = await client.post("/api/v1/payments/webhook/stripe", 
                                       content=b"dummy_payload", 
                                       headers={"Stripe-Signature": "dummy_sig"})
                
                assert res.status_code == 200
                assert res.json()["status"] == "success"
                
                # 4. Verify Invoice Status
                res = await client.get(f"/api/v1/invoices/{invoice_id}")
                invoice = res.json()
                assert invoice["status"] == "paid"
                assert invoice["stripe_payment_intent_id"] == "pi_test_123"

@pytest.mark.asyncio
async def test_webhook_idempotency(local_client):
    # Set Env for Webhook Secret
    with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "whsec_test"}):
        async with local_client as client:
            # Same event ID
            with patch("stripe.Webhook.construct_event") as mock_construct:
                mock_event = MagicMock()
                mock_event.id = "evt_test_idempotent" # Fixed ID
                mock_event.type = "checkout.session.completed"
                mock_event.data.object.client_reference_id = None # Shouldn't matter for idempotency check
                mock_construct.return_value = mock_event
        
                # First Call
                res = await client.post("/api/v1/payments/webhook/stripe", content=b"1", headers={"Stripe-Signature": "1"})
                assert res.status_code == 200
                
                # Second Call
                res = await client.post("/api/v1/payments/webhook/stripe", content=b"1", headers={"Stripe-Signature": "1"})
                assert res.status_code == 200
                assert res.json()["status"] == "already_processed"
