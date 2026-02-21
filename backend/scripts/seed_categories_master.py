import asyncio
import uuid
from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy import select, func

from app.database import AsyncSessionLocal
from app.models.category import Category, CategoryTranslation
from app.models.category_schema_version import CategorySchemaVersion
from app.core.config import settings

SUPPORTED_COUNTRIES = {"DE", "CH", "FR", "AT"}


def build_default_schema() -> Dict:
    return {
        "status": "published",
        "core_fields": {
            "title": {"required": True, "min": 10, "max": 80},
            "description": {"required": True, "min": 30, "max": 2000},
            "price": {
                "required": True,
                "currency_primary": "EUR",
                "currency_secondary": "CHF",
                "range": {"min": 0, "max": 2000000},
            },
        },
        "dynamic_fields": [],
        "detail_groups": [],
        "modules": {"photos": {"enabled": True, "max_uploads": 12}},
    }


def build_categories() -> List[Dict]:
    return [
        {
            "key": "cars",
            "slug": {"tr": "otomobil", "en": "cars", "de": "autos"},
            "name": {"tr": "Otomobil", "en": "Cars", "de": "Autos"},
            "children": [
                {
                    "key": "sedan",
                    "slug": {"tr": "sedan", "en": "sedan", "de": "limousine"},
                    "name": {"tr": "Sedan", "en": "Sedan", "de": "Limousine"},
                },
                {
                    "key": "hatchback",
                    "slug": {"tr": "hatchback", "en": "hatchback", "de": "kompakt"},
                    "name": {"tr": "Hatchback", "en": "Hatchback", "de": "Kompakt"},
                },
            ],
        },
        {
            "key": "suv",
            "slug": {"tr": "suv", "en": "suv", "de": "suv"},
            "name": {"tr": "SUV / Arazi", "en": "SUV / Offroad", "de": "SUV / Gele4ndewagen"},
            "children": [
                {
                    "key": "pickup",
                    "slug": {"tr": "pickup", "en": "pickup", "de": "pickup"},
                    "name": {"tr": "Pickup", "en": "Pickup", "de": "Pickup"},
                }
            ],
        },
        {
            "key": "motorcycles",
            "slug": {"tr": "motosiklet", "en": "motorcycles", "de": "motorre4der"},
            "name": {"tr": "Motosiklet", "en": "Motorcycles", "de": "Motorre4der"},
            "children": [
                {
                    "key": "scooter",
                    "slug": {"tr": "scooter", "en": "scooter", "de": "roller"},
                    "name": {"tr": "Scooter", "en": "Scooter", "de": "Roller"},
                }
            ],
        },
    ]


async def seed_categories() -> None:
    async with AsyncSessionLocal() as session:
        count = await session.execute(select(func.count()).select_from(Category))
        total = count.scalar_one()
        if total and total > 0:
            print(f"Categories already exist: {total}. Skipping seed.")
            return

        now = datetime.now(timezone.utc)
        allowed_countries = sorted(SUPPORTED_COUNTRIES)
        schema = build_default_schema()
        root_categories = build_categories()

        for index, root in enumerate(root_categories, start=1):
            root_id = uuid.uuid4()
            root_category = Category(
                id=root_id,
                parent_id=None,
                path=root["slug"]["tr"],
                depth=0,
                sort_order=index * 10,
                module="vehicle",
                slug=root["slug"],
                icon=None,
                image_url=None,
                is_enabled=True,
                is_visible_on_home=True,
                is_deleted=False,
                inherit_enabled=True,
                override_enabled=None,
                inherit_countries=True,
                override_countries=None,
                allowed_countries=allowed_countries,
                listing_count=0,
                country_code=None,
                hierarchy_complete=True,
                form_schema=schema,
                created_at=now,
                updated_at=now,
            )
            session.add(root_category)

            for lang in ("tr", "en", "de"):
                session.add(
                    CategoryTranslation(
                        category_id=root_id,
                        language=lang,
                        name=root["name"][lang],
                        description=None,
                        meta_title=None,
                        meta_description=None,
                    )
                )

            session.add(
                CategorySchemaVersion(
                    id=uuid.uuid4(),
                    category_id=root_id,
                    version=1,
                    status="published",
                    schema_snapshot=schema,
                    created_at=now,
                    created_by=None,
                    created_by_role="system",
                    created_by_email=settings.DEFAULT_ADMIN_EMAIL if hasattr(settings, "DEFAULT_ADMIN_EMAIL") else None,
                    published_at=now,
                    published_by=None,
                )
            )

            for child_index, child in enumerate(root.get("children", []), start=1):
                child_id = uuid.uuid4()
                child_category = Category(
                    id=child_id,
                    parent_id=root_id,
                    path=f"{root["slug"]["tr"]}.{child["slug"]["tr"]}",
                    depth=1,
                    sort_order=index * 10 + child_index,
                    module="vehicle",
                    slug=child["slug"],
                    icon=None,
                    image_url=None,
                    is_enabled=True,
                    is_visible_on_home=False,
                    is_deleted=False,
                    inherit_enabled=True,
                    override_enabled=None,
                    inherit_countries=True,
                    override_countries=None,
                    allowed_countries=allowed_countries,
                    listing_count=0,
                    country_code=None,
                    hierarchy_complete=True,
                    form_schema=schema,
                    created_at=now,
                    updated_at=now,
                )
                session.add(child_category)

                for lang in ("tr", "en", "de"):
                    session.add(
                        CategoryTranslation(
                            category_id=child_id,
                            language=lang,
                            name=child["name"][lang],
                            description=None,
                            meta_title=None,
                            meta_description=None,
                        )
                    )

                session.add(
                    CategorySchemaVersion(
                        id=uuid.uuid4(),
                        category_id=child_id,
                        version=1,
                        status="published",
                        schema_snapshot=schema,
                        created_at=now,
                        created_by=None,
                        created_by_role="system",
                        created_by_email=settings.DEFAULT_ADMIN_EMAIL if hasattr(settings, "DEFAULT_ADMIN_EMAIL") else None,
                        published_at=now,
                        published_by=None,
                    )
                )

        await session.commit()
        print("Category seed completed.")


if __name__ == "__main__":
    asyncio.run(seed_categories())
