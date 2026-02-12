
import pytest
from unittest.mock import MagicMock, patch
import stripe
from app.services.stripe_service import StripeService
from app.models.billing import Invoice
from sqlalchemy import select
import uuid

@pytest.mark.asyncio
async def test_create_checkout_session_flow(client, admin_headers):
    # 1. Create Draft Invoice
    res = await client.post("/invoices", headers=admin_headers, json={
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
        res = await client.post(f"/v1/payments/invoices/{invoice_id}/checkout", headers=admin_headers, json={
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
async def test_stripe_webhook_processing(client, admin_headers):
    # 1. Create Invoice
    res = await client.post("/invoices", headers=admin_headers, json={
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
        res = await client.post("/v1/payments/webhook/stripe", 
                               content=b"dummy_payload", 
                               headers={"Stripe-Signature": "dummy_sig"})
        
        assert res.status_code == 200
        assert res.json()["status"] == "success"
        
        # 4. Verify Invoice Status
        res = await client.get(f"/invoices/{invoice_id}", headers=admin_headers)
        invoice = res.json()
        assert invoice["status"] == "paid"
        assert invoice["stripe_payment_intent_id"] == "pi_test_123"

@pytest.mark.asyncio
async def test_webhook_idempotency(client, admin_headers):
    # Same event ID
    with patch("stripe.Webhook.construct_event") as mock_construct:
        mock_event = MagicMock()
        mock_event.id = "evt_test_idempotent" # Fixed ID
        mock_event.type = "checkout.session.completed"
        mock_event.data.object.client_reference_id = None # Shouldn't matter for idempotency check
        mock_construct.return_value = mock_event
        
        # First Call
        res = await client.post("/v1/payments/webhook/stripe", content=b"1", headers={"Stripe-Signature": "1"})
        assert res.status_code == 200
        
        # Second Call
        res = await client.post("/v1/payments/webhook/stripe", content=b"1", headers={"Stripe-Signature": "1"})
        assert res.status_code == 200
        assert res.json()["status"] == "already_processed"
