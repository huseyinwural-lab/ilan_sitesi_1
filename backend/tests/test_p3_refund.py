
import pytest
from unittest.mock import MagicMock, patch
import stripe
from app.services.stripe_service import StripeService
from app.models.billing import Invoice
from sqlalchemy import select
import uuid
import os
from httpx import AsyncClient, ASGITransport
from server import app
from app.dependencies import get_current_user
from app.database import engine

# Fix for "attached to a different loop" error with global engine
import pytest_asyncio
@pytest_asyncio.fixture(autouse=True)
async def cleanup_engine():
    yield
    await engine.dispose()

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
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

@pytest.mark.asyncio
async def test_full_refund_flow(local_client):
    with patch.dict(os.environ, {"STRIPE_API_KEY": "sk_test_mock"}):
        async with local_client as client:
            # 1. Create Invoice & Mark as Paid (Mock)
            res = await client.post("/api/invoices", json={
                "country": "DE",
                "customer_type": "B2C",
                "customer_name": "Refund Test",
                "customer_email": "ref@test.com",
                "items": [{"description": {"en": "Item"}, "quantity": 1, "unit_price": 100.0}]
            })
            invoice_id = res.json()["id"]
            
            # Manually update to Paid (Backend hack for test setup)
            # In real flow, webhook does this. 
            # We assume it's paid and has a payment_intent
            # Since we can't easily reach DB in test without service, we'll assume the REFUND endpoint validates this.
            # Wait, `create_refund` checks status="paid". So we MUST update status.
            # We can use the webhook to mark it paid!
            
            with patch("stripe.Webhook.construct_event") as mock_construct:
                mock_event = MagicMock()
                mock_event.id = f"evt_test_{uuid.uuid4().hex}" # Unique ID
                mock_event.type = "checkout.session.completed"
                mock_session = MagicMock()
                mock_session.id = f"cs_test_{uuid.uuid4().hex}"
                mock_session.metadata = {"invoice_id": invoice_id}
                mock_session.payment_intent = "pi_test_refund"
                mock_session.client_reference_id = invoice_id # Add this
                
                mock_event.data.object = mock_session
                mock_construct.return_value = mock_event
                
                with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "whsec_test"}):
                    wh_res = await client.post("/api/v1/payments/webhook/stripe", 
                                     content=b"dummy", 
                                     headers={"Stripe-Signature": "dummy"})
                    assert wh_res.status_code == 200, f"Webhook failed: {wh_res.text}"
                    assert wh_res.json()["status"] == "success"
                    
                    # Verify it is paid
                    inv_res = await client.get(f"/api/invoices/{invoice_id}")
                    assert inv_res.json()["status"] == "paid", "Invoice status not updated to paid"
            
            # 2. Refund Call
            with patch("stripe.Refund.create") as mock_refund:
                mock_refund_obj = MagicMock()
                mock_refund_obj.id = "re_test_123"
                mock_refund_obj.status = "succeeded"
                mock_refund.return_value = mock_refund_obj
                
                # Full amount: 100 * 1.19 (DE Tax) = 119.0
                res = await client.post(f"/api/v1/payments/invoices/{invoice_id}/refund", json={
                    "amount": 119.0,
                    "reason": "requested_by_customer"
                })
                
                assert res.status_code == 200
                assert res.json()["status"] == "succeeded"
                
                # Verify Stripe Call
                mock_refund.assert_called_once()
                args, kwargs = mock_refund.call_args
                assert kwargs["payment_intent"] == "pi_test_refund"
                assert kwargs["amount"] == 11900 # cents
                
                # Verify Invoice Status
                res = await client.get(f"/api/invoices/{invoice_id}")
                invoice = res.json()
                assert invoice["status"] == "refunded"
                assert invoice["net_total"] == 119.0 # Refunded amount logic: Wait, net_total is gross here? 
                # Invoice serialized 'net_total' is line net sum. 'gross_total' is what matters.
                # 'refunded_total' is new field.
                # But our serializer doesn't return 'refunded_total' yet in p1_routes.get_invoice_detail?
                # Ah, we updated the model but did we update serializer?
                # Let's check serializer in p1_routes.py... 
                # I see I updated `get_invoice_detail` in p1_routes.py but did I include `refunded_total`?
                # Let's check.

@pytest.mark.asyncio
async def test_over_refund_protection(local_client):
    with patch.dict(os.environ, {"STRIPE_API_KEY": "sk_test_mock"}):
        async with local_client as client:
            # Create & Pay Invoice
            res = await client.post("/api/invoices", json={
                "country": "DE",
                "customer_type": "B2C",
                "customer_name": "Over Refund",
                "customer_email": "over@test.com",
                "items": [{"description": {"en": "Item"}, "quantity": 1, "unit_price": 100.0}]
            })
            invoice_id = res.json()["id"]
            
            # Mark Paid
            with patch("stripe.Webhook.construct_event") as mock_construct:
                mock_event = MagicMock()
                mock_event.id = f"evt_test_{uuid.uuid4().hex}" # Unique ID
                mock_event.type = "checkout.session.completed"
                mock_session = MagicMock()
                mock_session.metadata = {"invoice_id": invoice_id}
                mock_session.payment_intent = "pi_test_over"
                mock_session.client_reference_id = invoice_id # Add this
                
                mock_event.data.object = mock_session
                mock_construct.return_value = mock_event
                with patch.dict(os.environ, {"STRIPE_WEBHOOK_SECRET": "whsec_test"}):
                    wh_res = await client.post("/api/v1/payments/webhook/stripe", content=b"dummy", headers={"Stripe-Signature": "dummy"})
                    assert wh_res.status_code == 200, f"Webhook failed: {wh_res.text}"
                    
                    inv_res = await client.get(f"/api/invoices/{invoice_id}")
                    assert inv_res.json()["status"] == "paid"

            # Attempt Refund > 119.0
            with patch("stripe.Refund.create"):
                res = await client.post(f"/api/v1/payments/invoices/{invoice_id}/refund", json={
                    "amount": 200.0, # Gross is 119.0
                    "reason": "requested_by_customer"
                })
                
                assert res.status_code == 400
                assert "exceeds" in res.json()["detail"]
