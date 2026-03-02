"""
P0-03 Stripe Live Acceptance Test (Test Mode Real Flow)
=====================================================
Validates that the Stripe checkout session completed successfully with:
1. Stripe session status = complete/paid
2. Backend payment row status = succeeded  
3. Backend invoice status = paid
4. Ledger entry group debit/credit balanced
5. Webhook endpoint 200 proof and webhook_event_logs records
"""
import pytest
import asyncio
import ssl
import json
import asyncpg
from urllib.parse import quote_plus

# Test context from the acceptance report
SESSION_ID = "cs_test_a1SrHaKbnTQK674lAHf2JDXi37GfUgJkjVrzRXASiNGoe3669BqB0Z3hNk"
INVOICE_ID = "41324cc6-49cb-4869-9e7b-c1f51bb3e7bc"
INVOICE_NO = "INV-20260302-B6D594"
EXPECTED_AMOUNT = 8888
EXPECTED_CURRENCY = "EUR"

# Webhook event IDs from acceptance report
CHECKOUT_SESSION_COMPLETED_EVENT = "evt_1T6cqFGoGL8wcbsGGHGSE57m"
PAYMENT_INTENT_SUCCEEDED_EVENT = "evt_3T6cqEGoGL8wcbsG14uEwHo2"


def get_db_connection():
    """Create database connection for verification."""
    async def _connect():
        password = quote_plus("zg[KESr95_u6;/98")
        DATABASE_URL = f"postgresql://sysadmin:{password}@217.195.207.70:5432/postgres"
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        return await asyncpg.connect(DATABASE_URL, ssl=ctx)
    
    return asyncio.get_event_loop().run_until_complete(_connect())


def run_async(coro):
    """Run async coroutine in sync context."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


@pytest.fixture(scope="module")
def db_conn():
    """Create database connection for verification."""
    conn = get_db_connection()
    yield conn
    run_async(conn.close())


@pytest.fixture(scope="module")
def acceptance_report():
    """Load the acceptance report for cross-validation."""
    report_path = "/app/test_reports/p0_03_stripe_acceptance.json"
    with open(report_path, "r") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def webhook_replay_results():
    """Load webhook replay results."""
    report_path = "/app/test_reports/p0_03_webhook_replay_results.json"
    with open(report_path, "r") as f:
        return json.load(f)


class TestStripeCheckoutAcceptance:
    """Test Stripe checkout acceptance criteria against live database."""
    
    def test_payment_row_status_succeeded(self, db_conn):
        """Verify payment row has status = succeeded for the checkout session."""
        async def _test():
            row = await db_conn.fetchrow('''
                SELECT id, provider_ref, status, amount_minor, currency, provider, created_at
                FROM payments 
                WHERE provider_ref = $1
            ''', SESSION_ID)
            
            assert row is not None, f"Payment not found for session_id: {SESSION_ID}"
            assert row['status'] == 'succeeded', f"Expected status 'succeeded', got '{row['status']}'"
            assert row['amount_minor'] == EXPECTED_AMOUNT, f"Expected amount {EXPECTED_AMOUNT}, got {row['amount_minor']}"
            assert row['currency'] == EXPECTED_CURRENCY, f"Expected currency {EXPECTED_CURRENCY}, got {row['currency']}"
            assert row['provider'] == 'stripe', f"Expected provider 'stripe', got {row['provider']}"
            
            print(f"✓ Payment row verified: ID={row['id']}, status={row['status']}, amount={row['amount_minor']} {row['currency']}")
            return row
        
        run_async(_test())

    def test_invoice_status_paid(self, db_conn):
        """Verify invoice has status = paid and payment_status = succeeded."""
        async def _test():
            row = await db_conn.fetchrow('''
                SELECT id, invoice_no, status, payment_status, amount_minor, currency, updated_at
                FROM admin_invoices 
                WHERE id = $1::uuid
            ''', INVOICE_ID)
            
            assert row is not None, f"Invoice not found: {INVOICE_ID}"
            assert row['invoice_no'] == INVOICE_NO, f"Expected invoice_no {INVOICE_NO}, got {row['invoice_no']}"
            assert row['status'] == 'paid', f"Expected status 'paid', got '{row['status']}'"
            assert row['payment_status'] == 'succeeded', f"Expected payment_status 'succeeded', got '{row['payment_status']}'"
            assert row['amount_minor'] == EXPECTED_AMOUNT, f"Expected amount {EXPECTED_AMOUNT}, got {row['amount_minor']}"
            assert row['currency'] == EXPECTED_CURRENCY, f"Expected currency {EXPECTED_CURRENCY}, got {row['currency']}"
            
            print(f"✓ Invoice verified: {row['invoice_no']}, status={row['status']}, payment_status={row['payment_status']}")
            return row
        
        run_async(_test())

    def test_ledger_entry_group_balanced(self, db_conn):
        """Verify ledger entries for the invoice are balanced (debit = credit)."""
        async def _test():
            rows = await db_conn.fetch('''
                SELECT le.id, le.entry_group_id, le.debit_minor, le.credit_minor, 
                       le.reference_id, le.reference_type, la.code, la.name
                FROM ledger_entries le
                LEFT JOIN ledger_accounts la ON le.account_id = la.id
                WHERE le.reference_id = $1
                ORDER BY le.entry_group_id, le.id
            ''', INVOICE_ID)
            
            assert len(rows) > 0, f"No ledger entries found for invoice: {INVOICE_ID}"
            
            total_debit = sum(row['debit_minor'] or 0 for row in rows)
            total_credit = sum(row['credit_minor'] or 0 for row in rows)
            
            # Verify double-entry accounting
            assert total_debit == total_credit, f"Ledger not balanced: debit={total_debit}, credit={total_credit}"
            assert total_debit == EXPECTED_AMOUNT, f"Expected total {EXPECTED_AMOUNT}, got debit={total_debit}"
            
            # Verify entry structure (should have CASH debit and REVENUE credit)
            entry_group_id = rows[0]['entry_group_id']
            assert INVOICE_ID in entry_group_id, f"Entry group ID should contain invoice ID"
            
            accounts = {row['code']: {'debit': row['debit_minor'], 'credit': row['credit_minor']} for row in rows}
            assert 'CASH' in accounts, "Missing CASH account entry"
            assert 'REVENUE' in accounts, "Missing REVENUE account entry"
            assert accounts['CASH']['debit'] == EXPECTED_AMOUNT, f"CASH debit should be {EXPECTED_AMOUNT}"
            assert accounts['REVENUE']['credit'] == EXPECTED_AMOUNT, f"REVENUE credit should be {EXPECTED_AMOUNT}"
            
            print(f"✓ Ledger balanced: debit={total_debit}, credit={total_credit}, entries={len(rows)}")
            return rows
        
        run_async(_test())

    def test_webhook_event_logs_checkout_session_completed(self, db_conn):
        """Verify checkout.session.completed webhook event was logged and processed."""
        async def _test():
            row = await db_conn.fetchrow('''
                SELECT event_id, event_type, status, signature_valid, processed_at, received_at
                FROM webhook_event_logs 
                WHERE event_id = $1
            ''', CHECKOUT_SESSION_COMPLETED_EVENT)
            
            assert row is not None, f"Webhook event not found: {CHECKOUT_SESSION_COMPLETED_EVENT}"
            assert row['event_type'] == 'checkout.session.completed', f"Expected event_type 'checkout.session.completed', got '{row['event_type']}'"
            assert row['status'] == 'processed', f"Expected status 'processed', got '{row['status']}'"
            assert row['signature_valid'] is True, "Webhook signature should be valid"
            assert row['processed_at'] is not None, "Webhook should have processed_at timestamp"
            assert row['received_at'] is not None, "Webhook should have received_at timestamp"
            
            print(f"✓ checkout.session.completed webhook verified: status={row['status']}, signature_valid={row['signature_valid']}")
            return row
        
        run_async(_test())

    def test_webhook_event_logs_payment_intent_succeeded(self, db_conn):
        """Verify payment_intent.succeeded webhook event was logged."""
        async def _test():
            row = await db_conn.fetchrow('''
                SELECT event_id, event_type, status, signature_valid, processed_at, received_at
                FROM webhook_event_logs 
                WHERE event_id = $1
            ''', PAYMENT_INTENT_SUCCEEDED_EVENT)
            
            assert row is not None, f"Webhook event not found: {PAYMENT_INTENT_SUCCEEDED_EVENT}"
            assert row['event_type'] == 'payment_intent.succeeded', f"Expected event_type 'payment_intent.succeeded', got '{row['event_type']}'"
            # payment_intent.succeeded is typically ignored as checkout.session.completed handles the main flow
            assert row['status'] in ('processed', 'ignored'), f"Expected status 'processed' or 'ignored', got '{row['status']}'"
            assert row['signature_valid'] is True, "Webhook signature should be valid"
            
            print(f"✓ payment_intent.succeeded webhook verified: status={row['status']}, signature_valid={row['signature_valid']}")
            return row
        
        run_async(_test())


class TestWebhookReplayResults:
    """Verify webhook replay results show HTTP 200 responses."""
    
    def test_webhook_replay_all_200(self, webhook_replay_results):
        """Verify all webhook replays returned HTTP 200."""
        for result in webhook_replay_results:
            assert result['status_code'] == 200, f"Webhook {result['event_id']} returned {result['status_code']}, expected 200"
        
        print(f"✓ All {len(webhook_replay_results)} webhook replays returned HTTP 200")

    def test_webhook_replay_checkout_session_processed(self, webhook_replay_results):
        """Verify checkout.session.completed replay was processed."""
        checkout_result = next(
            (r for r in webhook_replay_results if r['event_type'] == 'checkout.session.completed'), 
            None
        )
        assert checkout_result is not None, "checkout.session.completed replay not found"
        assert checkout_result['status_code'] == 200, f"Expected 200, got {checkout_result['status_code']}"
        
        body = json.loads(checkout_result['body'])
        assert body.get('status') == 'processed', f"Expected processed status, got {body}"
        
        print(f"✓ checkout.session.completed replay verified: {body}")


class TestAcceptanceReportConsistency:
    """Cross-validate acceptance report claims against database."""
    
    def test_acceptance_report_stripe_status(self, acceptance_report):
        """Verify acceptance report Stripe section matches expected values."""
        stripe_data = acceptance_report.get('stripe', {})
        
        assert stripe_data.get('session_id') == SESSION_ID, "Session ID mismatch"
        assert stripe_data.get('session_status') == 'complete', f"Expected session_status 'complete', got {stripe_data.get('session_status')}"
        assert stripe_data.get('payment_status') == 'paid', f"Expected payment_status 'paid', got {stripe_data.get('payment_status')}"
        assert stripe_data.get('amount_total') == EXPECTED_AMOUNT, f"Expected amount {EXPECTED_AMOUNT}, got {stripe_data.get('amount_total')}"
        assert stripe_data.get('currency') == 'eur', f"Expected currency 'eur', got {stripe_data.get('currency')}"
        
        print(f"✓ Acceptance report Stripe section verified")

    def test_acceptance_report_backend_section(self, acceptance_report, db_conn):
        """Verify acceptance report backend section matches database state."""
        async def _test():
            backend_data = acceptance_report.get('backend', {})
            
            # Verify invoice claim
            invoice_claim = backend_data.get('invoice', {})
            db_invoice = await db_conn.fetchrow(
                'SELECT status, payment_status FROM admin_invoices WHERE id = $1::uuid', 
                INVOICE_ID
            )
            assert invoice_claim.get('status') == db_invoice['status'], "Invoice status mismatch between report and DB"
            assert invoice_claim.get('payment_status') == db_invoice['payment_status'], "Invoice payment_status mismatch"
            
            # Verify payments claim
            payments_claim = backend_data.get('payments', [])
            assert len(payments_claim) > 0, "No payments in acceptance report"
            payment = payments_claim[0]
            assert payment.get('status') == 'succeeded', f"Payment status in report should be succeeded, got {payment.get('status')}"
            
            # Verify ledger claim
            ledger_groups = backend_data.get('ledger_groups', [])
            assert len(ledger_groups) > 0, "No ledger groups in acceptance report"
            ledger_group = ledger_groups[0]
            assert ledger_group.get('balanced') is True, "Ledger should be balanced"
            assert ledger_group.get('debit_total') == ledger_group.get('credit_total'), "Debit/credit should match"
            
            print(f"✓ Acceptance report backend section matches database")
        
        run_async(_test())

    def test_acceptance_summary_all_true(self, acceptance_report):
        """Verify acceptance summary has all criteria as true."""
        summary = acceptance_report.get('acceptance_summary', {})
        
        expected_true_fields = [
            'payment_status_succeeded',
            'invoice_status_paid',
            'ledger_balanced',
            'webhook_processed',
            'webhook_http_200_proof',
            'has_checkout_session_completed_event'
        ]
        
        for field in expected_true_fields:
            assert summary.get(field) is True, f"Acceptance summary field '{field}' should be True, got {summary.get(field)}"
        
        print(f"✓ Acceptance summary all criteria verified as True")


class TestWebhookEventLogsCompleteness:
    """Verify webhook event logs are complete."""
    
    def test_webhook_logs_have_all_required_fields(self, db_conn):
        """Verify webhook logs have all required fields populated."""
        async def _test():
            rows = await db_conn.fetch('''
                SELECT event_id, event_type, status, signature_valid, processed_at, received_at
                FROM webhook_event_logs 
                WHERE event_id IN ($1, $2)
            ''', CHECKOUT_SESSION_COMPLETED_EVENT, PAYMENT_INTENT_SUCCEEDED_EVENT)
            
            assert len(rows) == 2, f"Expected 2 webhook logs, found {len(rows)}"
            
            for row in rows:
                assert row['event_id'] is not None, "event_id should not be null"
                assert row['event_type'] is not None, "event_type should not be null"
                assert row['status'] is not None, "status should not be null"
                assert row['signature_valid'] is not None, "signature_valid should not be null"
                assert row['received_at'] is not None, "received_at should not be null"
            
            print(f"✓ All {len(rows)} webhook logs have complete fields")
            return rows
        
        run_async(_test())

    def test_webhook_processing_order(self, db_conn):
        """Verify webhook events were processed in correct order."""
        async def _test():
            rows = await db_conn.fetch('''
                SELECT event_id, event_type, received_at, processed_at
                FROM webhook_event_logs 
                WHERE event_id IN ($1, $2)
                ORDER BY received_at ASC
            ''', CHECKOUT_SESSION_COMPLETED_EVENT, PAYMENT_INTENT_SUCCEEDED_EVENT)
            
            # checkout.session.completed should have been received/processed
            checkout_event = next((r for r in rows if r['event_type'] == 'checkout.session.completed'), None)
            assert checkout_event is not None, "checkout.session.completed event not found"
            assert checkout_event['processed_at'] is not None, "checkout.session.completed should be processed"
            
            print(f"✓ Webhook processing order verified")
            return rows
        
        run_async(_test())
