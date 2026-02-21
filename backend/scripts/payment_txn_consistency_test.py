import asyncio
import os
import uuid
from datetime import datetime, timezone, timedelta

from dotenv import load_dotenv
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.plan import Plan
from app.models.admin_invoice import AdminInvoice
from app.models.monetization import UserSubscription
from app.models.payment import Payment, PaymentTransaction
from app.server import _apply_payment_status

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.local"), override=True)


async def run():
    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.email == "user@platform.com"))).scalar_one()
        plan = (await session.execute(select(Plan).order_by(Plan.created_at.asc()))).scalars().first()
        if not plan:
            raise RuntimeError("Plan not found")

        subscription = (await session.execute(select(UserSubscription).where(UserSubscription.user_id == user.id))).scalar_one_or_none()
        now = datetime.now(timezone.utc)
        if not subscription:
            subscription = UserSubscription(
                id=uuid.uuid4(),
                user_id=user.id,
                plan_id=plan.id,
                status="trial",
                current_period_start=now,
                current_period_end=now + timedelta(days=30),
                provider="stripe",
                provider_customer_id=None,
                provider_subscription_id=None,
                created_at=now,
                updated_at=now,
            )
            session.add(subscription)
            await session.flush()
        else:
            subscription.plan_id = plan.id
            subscription.status = "trial"
            subscription.current_period_start = now
            subscription.current_period_end = now + timedelta(days=30)
            subscription.updated_at = now

        invoice = AdminInvoice(
            id=uuid.uuid4(),
            invoice_no=f"TEST-{uuid.uuid4().hex[:8]}",
            user_id=user.id,
            subscription_id=subscription.id,
            plan_id=plan.id,
            amount_total=plan.price_amount,
            currency=plan.currency_code or "EUR",
            status="issued",
            payment_status="requires_payment_method",
            issued_at=now,
            due_at=now + timedelta(days=1),
            scope="country",
            country_code=user.country_code,
            created_at=now,
            updated_at=now,
        )
        session.add(invoice)
        await session.flush()

        payment = Payment(
            id=uuid.uuid4(),
            invoice_id=invoice.id,
            user_id=user.id,
            provider="stripe",
            provider_ref=f"pi_{uuid.uuid4().hex[:8]}",
            status="requires_payment_method",
            amount_total=invoice.amount_total,
            currency=invoice.currency,
            meta_json={"source": "consistency_test"},
            created_at=now,
            updated_at=now,
        )
        transaction = PaymentTransaction(
            id=uuid.uuid4(),
            provider="stripe",
            session_id=f"sess_{uuid.uuid4().hex[:8]}",
            provider_payment_id=None,
            invoice_id=invoice.id,
            dealer_id=user.id,
            amount=invoice.amount_total,
            currency=invoice.currency,
            status="requires_payment_method",
            payment_status="requires_payment_method",
            metadata_json={"test": True},
            created_at=now,
            updated_at=now,
        )
        session.add_all([payment, transaction])
        await session.flush()

        await _apply_payment_status(
            invoice,
            payment,
            transaction,
            "succeeded",
            provider_payment_id="pi_test_123",
            provider_ref=payment.provider_ref,
            meta={"test": True},
            session=session,
        )

        await session.commit()

        await session.refresh(invoice)
        await session.refresh(subscription)
        await session.refresh(user)

        print(
            {
                "invoice_status": invoice.status,
                "payment_status": invoice.payment_status,
                "subscription_status": subscription.status,
                "listing_quota_limit": user.listing_quota_limit,
                "showcase_quota_limit": user.showcase_quota_limit,
            }
        )


if __name__ == "__main__":
    asyncio.run(run())
