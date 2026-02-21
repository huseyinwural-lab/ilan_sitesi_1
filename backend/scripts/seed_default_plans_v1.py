import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import select

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / ".env.local", override=True)

from app.database import AsyncSessionLocal
from app.models.plan import Plan


def _slugify(value: str) -> str:
    return "-".join("".join(ch.lower() if ch.isalnum() else " " for ch in value).split())


PLANS = [
    {
        "name": "Consumer Free",
        "period": "monthly",
        "price_amount": 0,
        "currency_code": "EUR",
        "listing_quota": 3,
        "showcase_quota": 0,
    },
    {
        "name": "Consumer Free",
        "period": "yearly",
        "price_amount": 0,
        "currency_code": "EUR",
        "listing_quota": 3,
        "showcase_quota": 0,
    },
    {
        "name": "Dealer Pro",
        "period": "monthly",
        "price_amount": 49,
        "currency_code": "EUR",
        "listing_quota": 50,
        "showcase_quota": 5,
    },
    {
        "name": "Dealer Pro",
        "period": "yearly",
        "price_amount": 499,
        "currency_code": "EUR",
        "listing_quota": 600,
        "showcase_quota": 60,
    },
    {
        "name": "Dealer Enterprise",
        "period": "monthly",
        "price_amount": 199,
        "currency_code": "EUR",
        "listing_quota": 200,
        "showcase_quota": 20,
    },
    {
        "name": "Dealer Enterprise",
        "period": "yearly",
        "price_amount": 1999,
        "currency_code": "EUR",
        "listing_quota": 2400,
        "showcase_quota": 240,
    },
]


async def seed() -> None:
    country_scope = "country"
    country_code = "DE"

    created = 0
    updated = 0
    items = []

    async with AsyncSessionLocal() as session:
        for plan_data in PLANS:
            slug = _slugify(f"{plan_data['name']} {plan_data['period']}")
            stmt = select(Plan).where(
                Plan.country_scope == country_scope,
                Plan.country_code == country_code,
                Plan.slug == slug,
                Plan.period == plan_data["period"],
            )
            existing = (await session.execute(stmt)).scalar_one_or_none()

            if existing:
                existing.name = plan_data["name"]
                existing.period = plan_data["period"]
                existing.price_amount = plan_data["price_amount"]
                existing.currency_code = plan_data["currency_code"]
                existing.listing_quota = plan_data["listing_quota"]
                existing.showcase_quota = plan_data["showcase_quota"]
                existing.active_flag = True
                existing.updated_at = datetime.now(timezone.utc)
                updated += 1
                plan_id = existing.id
            else:
                plan = Plan(
                    slug=slug,
                    name=plan_data["name"],
                    country_scope=country_scope,
                    country_code=country_code,
                    period=plan_data["period"],
                    price_amount=plan_data["price_amount"],
                    currency_code=plan_data["currency_code"],
                    listing_quota=plan_data["listing_quota"],
                    showcase_quota=plan_data["showcase_quota"],
                    active_flag=True,
                    archived_at=None,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(plan)
                await session.flush()
                created += 1
                plan_id = plan.id

            items.append({"slug": slug, "period": plan_data["period"], "id": str(plan_id)})

        await session.commit()

    report = {
        "created": created,
        "updated": updated,
        "total": len(PLANS),
        "country_scope": country_scope,
        "country_code": country_code,
        "items": items,
    }

    Path("/app/docs/default_plans_seed_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(seed())
