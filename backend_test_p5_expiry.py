#!/usr/bin/env python3
"""
P5-005 Expiry Job Comprehensive Test
Tests the expiry job implementation, database index, and audit logging.
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

from app.database import AsyncSessionLocal
from app.jobs.expiry_worker import run_expiry_job
from app.models.commercial import DealerSubscription, DealerPackage
from app.models.dealer import Dealer, DealerApplication
from app.models.billing import Invoice
from app.models.core import AuditLog
from sqlalchemy import select, delete, text

class P5ExpiryJobTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.failures = []

    def log_test(self, name, success, message=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name}")
            if message:
                print(f"   {message}")
        else:
            self.failures.append(name)
            print(f"❌ {name}")
            if message:
                print(f"   {message}")

    async def cleanup_test_data(self):
        """Clean up test data"""
        async with AsyncSessionLocal() as session:
            # Clean up in correct order due to foreign keys
            await session.execute(delete(AuditLog).where(AuditLog.action == "SYSTEM_EXPIRE"))
            await session.execute(delete(DealerSubscription))
            await session.execute(delete(DealerPackage))
            await session.execute(delete(Invoice))
            await session.execute(delete(Dealer))
            await session.execute(delete(DealerApplication))
            await session.commit()

    async def test_database_index_exists(self):
        """Test that the expiry job database index exists"""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(text("""
                    SELECT indexname, indexdef 
                    FROM pg_indexes 
                    WHERE tablename = 'dealer_subscriptions' 
                    AND indexname = 'ix_dealer_subscriptions_status_end_at'
                """))
                indexes = result.fetchall()
                
                if indexes:
                    index_def = indexes[0][1]
                    expected_columns = "status, end_at"
                    if expected_columns in index_def:
                        self.log_test("Database Index Exists", True, f"Index: {index_def}")
                        return True
                    else:
                        self.log_test("Database Index Exists", False, f"Index exists but wrong columns: {index_def}")
                        return False
                else:
                    self.log_test("Database Index Exists", False, "Index ix_dealer_subscriptions_status_end_at not found")
                    return False
        except Exception as e:
            self.log_test("Database Index Exists", False, f"Error: {str(e)}")
            return False

    async def test_expiry_job_functionality(self):
        """Test the core expiry job functionality"""
        try:
            await self.cleanup_test_data()
            
            async with AsyncSessionLocal() as session:
                # Create test data
                # 1. Dealer Application
                app_id = uuid.uuid4()
                session.add(DealerApplication(
                    id=app_id,
                    country="DE",
                    dealer_type="auto_dealer",
                    company_name="Test Expiry Company",
                    contact_name="Test Contact",
                    contact_email="test@expiry.com",
                    status="approved"
                ))
                await session.flush()

                # 2. Dealer
                dealer_id = uuid.uuid4()
                session.add(Dealer(
                    id=dealer_id,
                    application_id=app_id,
                    country="DE",
                    dealer_type="auto_dealer",
                    company_name="Test Expiry Company"
                ))
                await session.flush()

                # 3. Package
                package_id = uuid.uuid4()
                session.add(DealerPackage(
                    id=package_id,
                    key="TEST_EXPIRY",
                    country="DE",
                    name={"en": "Test Expiry Package"},
                    price_net=Decimal("50.00"),
                    currency="EUR",
                    duration_days=30
                ))
                await session.flush()

                # 4. Invoice
                invoice_id = uuid.uuid4()
                session.add(Invoice(
                    id=invoice_id,
                    invoice_no="INV-EXPIRY-TEST",
                    country="DE",
                    currency="EUR",
                    customer_type="dealer",
                    customer_ref_id=dealer_id,
                    customer_name="Test Expiry Company",
                    status="paid",
                    gross_total=Decimal("50.00"),
                    net_total=Decimal("50.00"),
                    tax_total=Decimal("0.00"),
                    tax_rate_snapshot=Decimal("0.00")
                ))
                await session.flush()

                # 5. Expired Subscription
                expired_sub_id = uuid.uuid4()
                session.add(DealerSubscription(
                    id=expired_sub_id,
                    dealer_id=dealer_id,
                    package_id=package_id,
                    invoice_id=invoice_id,
                    start_at=datetime.now(timezone.utc) - timedelta(days=60),
                    end_at=datetime.now(timezone.utc) - timedelta(days=1),  # Yesterday
                    status="active",  # Should be changed to expired
                    included_listing_quota=10
                ))

                # 6. Valid Subscription (for comparison)
                valid_invoice_id = uuid.uuid4()
                session.add(Invoice(
                    id=valid_invoice_id,
                    invoice_no="INV-VALID-TEST",
                    country="DE",
                    currency="EUR",
                    customer_type="dealer",
                    customer_ref_id=dealer_id,
                    customer_name="Test Expiry Company",
                    status="paid",
                    gross_total=Decimal("50.00"),
                    net_total=Decimal("50.00"),
                    tax_total=Decimal("0.00"),
                    tax_rate_snapshot=Decimal("0.00")
                ))
                await session.flush()

                valid_sub_id = uuid.uuid4()
                session.add(DealerSubscription(
                    id=valid_sub_id,
                    dealer_id=dealer_id,
                    package_id=package_id,
                    invoice_id=valid_invoice_id,
                    start_at=datetime.now(timezone.utc),
                    end_at=datetime.now(timezone.utc) + timedelta(days=30),  # Future
                    status="active",  # Should remain active
                    included_listing_quota=10
                ))

                await session.commit()

            # Run the expiry job
            await run_expiry_job()

            # Verify results
            async with AsyncSessionLocal() as session:
                # Check expired subscription
                expired_sub = await session.execute(
                    select(DealerSubscription).where(DealerSubscription.id == expired_sub_id)
                )
                expired_sub = expired_sub.scalar_one()
                
                # Check valid subscription
                valid_sub = await session.execute(
                    select(DealerSubscription).where(DealerSubscription.id == valid_sub_id)
                )
                valid_sub = valid_sub.scalar_one()

                # Check audit log
                audit_logs = await session.execute(
                    select(AuditLog).where(AuditLog.action == "SYSTEM_EXPIRE")
                )
                audit_logs = audit_logs.scalars().all()

                # Verify results
                success = True
                messages = []

                if expired_sub.status != "expired":
                    success = False
                    messages.append(f"Expired subscription status is '{expired_sub.status}', expected 'expired'")
                else:
                    messages.append("Expired subscription correctly marked as expired")

                if valid_sub.status != "active":
                    success = False
                    messages.append(f"Valid subscription status is '{valid_sub.status}', expected 'active'")
                else:
                    messages.append("Valid subscription remains active")

                if len(audit_logs) != 1:
                    success = False
                    messages.append(f"Expected 1 audit log, found {len(audit_logs)}")
                else:
                    audit_log = audit_logs[0]
                    if audit_log.new_values.get("count") != 1:
                        success = False
                        messages.append(f"Audit log count is {audit_log.new_values.get('count')}, expected 1")
                    elif str(expired_sub_id) not in audit_log.new_values.get("ids", []):
                        success = False
                        messages.append("Expired subscription ID not found in audit log")
                    else:
                        messages.append("Audit log correctly recorded expiry action")

                self.log_test("Expiry Job Functionality", success, "; ".join(messages))
                return success

        except Exception as e:
            self.log_test("Expiry Job Functionality", False, f"Error: {str(e)}")
            return False

    async def test_expiry_job_no_expired_subscriptions(self):
        """Test expiry job when no subscriptions need expiring"""
        try:
            await self.cleanup_test_data()
            
            # Run expiry job on empty database
            await run_expiry_job()
            
            # Check that no audit logs were created
            async with AsyncSessionLocal() as session:
                audit_logs = await session.execute(
                    select(AuditLog).where(AuditLog.action == "SYSTEM_EXPIRE")
                )
                audit_logs = audit_logs.scalars().all()
                
                if len(audit_logs) == 0:
                    self.log_test("Expiry Job - No Expired Subscriptions", True, "No audit logs created when no subscriptions to expire")
                    return True
                else:
                    self.log_test("Expiry Job - No Expired Subscriptions", False, f"Unexpected {len(audit_logs)} audit logs created")
                    return False

        except Exception as e:
            self.log_test("Expiry Job - No Expired Subscriptions", False, f"Error: {str(e)}")
            return False

    async def test_start_script_exists(self):
        """Test that the start script exists and is executable"""
        try:
            import os
            script_path = "/app/backend/start_cron.sh"
            
            if os.path.exists(script_path):
                # Check if file is executable
                if os.access(script_path, os.X_OK):
                    self.log_test("Start Script Exists and Executable", True, f"Script found at {script_path}")
                    return True
                else:
                    self.log_test("Start Script Exists and Executable", False, f"Script exists but not executable: {script_path}")
                    return False
            else:
                self.log_test("Start Script Exists and Executable", False, f"Script not found: {script_path}")
                return False

        except Exception as e:
            self.log_test("Start Script Exists and Executable", False, f"Error: {str(e)}")
            return False

    async def run_all_tests(self):
        """Run all P5-005 expiry job tests"""
        print("🚀 Starting P5-005 Expiry Job Tests")
        print("=" * 50)

        # Test database index
        await self.test_database_index_exists()
        
        # Test expiry job functionality
        await self.test_expiry_job_functionality()
        
        # Test no expired subscriptions scenario
        await self.test_expiry_job_no_expired_subscriptions()
        
        # Test start script
        await self.test_start_script_exists()

        # Cleanup
        await self.cleanup_test_data()

        # Print results
        print("\n" + "=" * 50)
        print(f"📊 Tests completed: {self.tests_passed}/{self.tests_run}")
        
        if self.failures:
            print(f"\n❌ Failed tests ({len(self.failures)}):")
            for failure in self.failures:
                print(f"  • {failure}")
        
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"\n📈 Success rate: {success_rate:.1f}%")
        
        return success_rate >= 100  # All tests must pass

async def main():
    tester = P5ExpiryJobTester()
    success = await tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main()))