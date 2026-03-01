import asyncio
import sys
import uuid
from datetime import datetime, timezone, timedelta

sys.path.append('/app/backend')

from sqlalchemy import select, and_  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.models.category import Category, CategoryTranslation  # noqa: E402
from app.models.vehicle_mdm import VehicleMake, VehicleModel  # noqa: E402
from app.models.vehicle_trim import VehicleTrim  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.moderation import Listing  # noqa: E402


COUNTRIES = ["DE", "AT", "CH", "FR"]


def leaf_schema(field_label: str, detail_title: str) -> dict:
    return {
        "status": "published",
        "dynamic_fields": [
            {
                "id": f"field_{field_label.lower()}",
                "label": field_label,
                "key": f"field_{field_label.lower()}",
                "type": "select",
                "required": True,
                "options": ["A", "B", "C"],
                "messages": {"required": f"{field_label} required"},
            }
        ],
        "detail_groups": [
            {
                "id": f"group_{detail_title.lower()}",
                "title": detail_title,
                "required": True,
                "options": ["Opsiyon-1", "Opsiyon-2", "Opsiyon-3"],
                "messages": {"required": f"{detail_title} required"},
            }
        ],
        "modules": {
            "address": {"enabled": True},
            "photos": {"enabled": True, "max_uploads": 20},
            "contact": {"enabled": True},
            "payment": {"enabled": True},
        },
    }


async def ensure_category(session, module: str, parent: Category | None, slug_tr: str, name_tr: str, sort_order: int, schema: dict | None = None) -> Category:
    query = select(Category).where(
        Category.module == module,
        Category.parent_id == (parent.id if parent else None),
        Category.is_deleted.is_(False),
    )
    row = await session.execute(query)
    category = None
    for item in row.scalars().all():
        slug_map = item.slug if isinstance(item.slug, dict) else {}
        if str(slug_map.get("tr") or "").strip() == slug_tr:
            category = item
            break
    now = datetime.now(timezone.utc)

    if not category:
        category = Category(
            parent_id=parent.id if parent else None,
            path="",
            depth=(parent.depth + 1) if parent else 0,
            sort_order=sort_order,
            module=module,
            country_code=None,
            slug={"tr": slug_tr, "de": slug_tr, "fr": slug_tr},
            icon=None,
            image_url=None,
            is_enabled=True,
            is_visible_on_home=False,
            is_deleted=False,
            inherit_enabled=True,
            override_enabled=None,
            inherit_countries=True,
            override_countries=None,
            allowed_countries=COUNTRIES,
            hierarchy_complete=True,
            form_schema=schema,
            wizard_progress=None,
            listing_count=0,
            created_at=now,
            updated_at=now,
        )
        session.add(category)
        await session.flush()
        category.path = f"{parent.path}.{category.id}" if parent else str(category.id)
    else:
        category.sort_order = sort_order
        category.allowed_countries = COUNTRIES
        if schema:
            category.form_schema = schema
        category.updated_at = now

    tr_query = select(CategoryTranslation).where(
        CategoryTranslation.category_id == category.id,
        CategoryTranslation.language == "tr",
    )
    tr_row = await session.execute(tr_query)
    tr = tr_row.scalar_one_or_none()
    if not tr:
        tr = CategoryTranslation(
            category_id=category.id,
            language="tr",
            name=name_tr,
            description=None,
            meta_title=None,
            meta_description=None,
            created_at=now,
            updated_at=now,
        )
        session.add(tr)
    else:
        tr.name = name_tr
        tr.updated_at = now

    return category


async def ensure_vehicle_make(session, slug: str, name: str) -> VehicleMake:
    result = await session.execute(select(VehicleMake).where(VehicleMake.slug == slug))
    make = result.scalar_one_or_none()
    if not make:
        make = VehicleMake(slug=slug, name=name, vehicle_types=["car"], is_active=True, source="seed", source_ref=f"seed-{slug}")
        session.add(make)
        await session.flush()
    else:
        make.name = name
        make.is_active = True
        make.updated_at = datetime.now(timezone.utc)
    return make


async def ensure_vehicle_model(session, make: VehicleMake, slug: str, name: str) -> VehicleModel:
    result = await session.execute(
        select(VehicleModel).where(
            VehicleModel.make_id == make.id,
            VehicleModel.slug == slug,
        )
    )
    model = result.scalar_one_or_none()
    if not model:
        model = VehicleModel(
            make_id=make.id,
            slug=slug,
            name=name,
            vehicle_type="car",
            year_from=2023,
            year_to=2026,
            is_active=True,
        )
        session.add(model)
        await session.flush()
    else:
        model.name = name
        model.is_active = True
    return model


async def ensure_vehicle_trim(
    session,
    make: VehicleMake,
    model: VehicleModel,
    slug: str,
    name: str,
    fuel_type: str,
    transmission: str,
):
    result = await session.execute(
        select(VehicleTrim).where(
            VehicleTrim.make_id == make.id,
            VehicleTrim.model_id == model.id,
            VehicleTrim.year == 2024,
            VehicleTrim.slug == slug,
        )
    )
    trim = result.scalar_one_or_none()
    attrs = {
        "fuel_type": [fuel_type],
        "transmission": [transmission],
        "body": ["Sedan"],
        "drive": ["FWD"],
        "engine_type": ["ICE"],
    }
    if not trim:
        trim = VehicleTrim(
            make_id=make.id,
            model_id=model.id,
            year=2024,
            name=name,
            slug=slug,
            source="seed",
            source_ref=f"seed:{make.slug}:{model.slug}:{slug}",
            attributes=attrs,
        )
        session.add(trim)
    else:
        trim.name = name
        trim.attributes = attrs
        trim.source_ref = f"seed:{make.slug}:{model.slug}:{slug}"


async def ensure_listing(
    session,
    owner: User,
    module: str,
    category_id: uuid.UUID,
    title: str,
    city: str,
    price: int,
    *,
    urgent: bool = False,
):
    row = await session.execute(select(Listing).where(Listing.title == title, Listing.user_id == owner.id))
    listing = row.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if not listing:
        listing = Listing(
            title=title,
            description=f"{title} aciklama",
            module=module,
            category_id=category_id,
            country="DE",
            city=city,
            price_type="FIXED",
            price=price,
            currency="EUR",
            user_id=owner.id,
            status="active",
            images=[],
            image_count=0,
            attributes={},
            contact_option_phone=True,
            contact_option_message=True,
            published_at=now,
            expires_at=now + timedelta(days=30),
        )
        session.add(listing)
        await session.flush()
    listing.status = "active"
    listing.published_at = now
    listing.expires_at = now + timedelta(days=30)
    if urgent:
        listing.urgent_until = now + timedelta(days=7)
        listing.is_showcase = False
        listing.showcase_expires_at = None
    return listing


async def main():
    database_url = settings.DATABASE_URL
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(database_url, future=True)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as session:
        roots = [
            ("konut", "Konut", [
                ("satilik-daire", "Satilik Daire", leaf_schema("Oda Sayisi", "Konut Donanim")),
                ("kiralik-daire", "Kiralik Daire", leaf_schema("Metrekare", "Konut Ozellik")),
            ]),
            ("ticari", "Ticari", [
                ("satilik-dukkan", "Satilik Dukkan", leaf_schema("Vitrin Uzunlugu", "Ticari Donanim")),
                ("kiralik-ofis", "Kiralik Ofis", leaf_schema("Kat", "Ofis Ozellik")),
            ]),
            ("arsa", "Arsa", [
                ("imara-acik", "Imara Acik Arsa", leaf_schema("Parsel No", "Tapu Bilgileri")),
                ("tarla", "Tarla", leaf_schema("Arazi Tipi", "Tarla Özellik")),
            ]),
        ]

        leaf_ids: list[uuid.UUID] = []
        for index, (root_slug, root_name, leaves) in enumerate(roots):
            root = await ensure_category(session, "real_estate", None, root_slug, root_name, index)
            for leaf_index, (leaf_slug, leaf_name, schema) in enumerate(leaves):
                leaf = await ensure_category(session, "real_estate", root, leaf_slug, leaf_name, leaf_index, schema)
                leaf_ids.append(leaf.id)

        vehicle_data = {
            "volkswagen": {
                "name": "Volkswagen",
                "models": {
                    "golf": "Golf",
                    "passat": "Passat",
                },
            },
            "bmw": {
                "name": "BMW",
                "models": {
                    "series-3": "3 Serisi",
                    "series-5": "5 Serisi",
                },
            },
            "toyota": {
                "name": "Toyota",
                "models": {
                    "corolla": "Corolla",
                    "camry": "Camry",
                },
            },
        }

        for make_slug, make_payload in vehicle_data.items():
            make = await ensure_vehicle_make(session, make_slug, make_payload["name"])
            for model_slug, model_name in make_payload["models"].items():
                model = await ensure_vehicle_model(session, make, model_slug, model_name)
                await ensure_vehicle_trim(
                    session,
                    make,
                    model,
                    f"{model_slug}-petrol-auto",
                    f"{model_name} 1.6 Benzin Otomatik",
                    "Benzin",
                    "Otomatik",
                )
                await ensure_vehicle_trim(
                    session,
                    make,
                    model,
                    f"{model_slug}-diesel-manual",
                    f"{model_name} 2.0 Dizel Manuel",
                    "Dizel",
                    "Manuel",
                )

        user_row = await session.execute(select(User).where(User.email == "user@platform.com"))
        owner = user_row.scalar_one_or_none()
        if owner and leaf_ids:
            for idx, leaf_id in enumerate(leaf_ids):
                await ensure_listing(
                    session,
                    owner,
                    "real_estate",
                    leaf_id,
                    f"E2E Emlak Ilani {idx + 1}",
                    "Berlin",
                    100000 + (idx * 5000),
                    urgent=(idx % 2 == 0),
                )
            for i in range(56):
                await ensure_listing(
                    session,
                    owner,
                    "real_estate",
                    leaf_ids[0],
                    f"E2E Urgent Listing {i + 1}",
                    "Berlin",
                    90000 + i,
                    urgent=True,
                )

        await session.commit()

    await engine.dispose()
    print("seed completed")


if __name__ == "__main__":
    asyncio.run(main())