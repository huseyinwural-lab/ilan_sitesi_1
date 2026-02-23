import argparse
import os
import random
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
import psycopg2
from pymongo import MongoClient

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / '.env')
load_dotenv(ROOT_DIR / '.env.local', override=False)

MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME')
DATABASE_URL = os.environ.get('DATABASE_URL')

if not MONGO_URL or not DB_NAME:
    raise RuntimeError('MONGO_URL and DB_NAME are required')
if not DATABASE_URL:
    raise RuntimeError('DATABASE_URL is required')

CITY_POOL = [
    "Berlin", "Munich", "Hamburg", "Cologne", "Frankfurt", "Stuttgart", "Dusseldorf",
    "Ankara", "Istanbul", "Izmir", "Bursa", "Antalya",
]
KEYWORDS = [
    "satilik", "kiralik", "temiz", "bakimli", "acil", "uygun", "lux",
    "daire", "villa", "araba", "suv", "sedan", "hybrid", "ev", "arsa", "ofis",
]
MODULES = [
    ("vehicle", 0.6),
    ("real_estate", 0.25),
    ("services", 0.15),
]
PRICE_RANGES = [
    (500, 5000),
    (5000, 20000),
    (20000, 50000),
    (50000, 150000),
    (150000, 500000),
]


def weighted_choice(options):
    total = sum(weight for _, weight in options)
    r = random.uniform(0, total)
    upto = 0
    for value, weight in options:
        if upto + weight >= r:
            return value
        upto += weight
    return options[-1][0]


def fetch_categories(limit=200):
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT id FROM categories LIMIT %s', (limit,))
            rows = cur.fetchall()
    return [str(row[0]) for row in rows]


def main():
    parser = argparse.ArgumentParser(description='Seed Mongo listings for search parity')
    parser.add_argument('--count', type=int, default=5000)
    parser.add_argument('--truncate', action='store_true')
    args = parser.parse_args()

    categories = fetch_categories()
    if not categories:
        raise RuntimeError('No categories found in Postgres to seed listings')

    client = MongoClient(MONGO_URL)
    db = client[DB_NAME]
    collection = db.listings

    if args.truncate:
        collection.delete_many({})

    documents = []
    now = datetime.now(timezone.utc)

    for i in range(args.count):
        module = weighted_choice(MODULES)
        category_id = random.choice(categories)
        city = random.choice(CITY_POOL)
        country = "DE" if random.random() < 0.8 else "TR"
        keyword = random.choice(KEYWORDS)
        price_min, price_max = random.choice(PRICE_RANGES)
        price_amount = random.randint(price_min, price_max)
        price_type = "HOURLY" if random.random() < 0.1 else "FIXED"
        created_at = now - timedelta(days=random.randint(0, 365), hours=random.randint(0, 23))

        title = f"{keyword.title()} {module.replace('_', ' ').title()} #{i}"
        description = f"{keyword} ilan aciklamasi. {random.choice(KEYWORDS)} detayli bilgi."

        attributes = {}
        vehicle = {}
        if module == "real_estate":
            attributes["m2_gross"] = random.randint(40, 400)
            attributes["room_count"] = random.choice([1, 2, 3, 4, 5])
        if module == "vehicle":
            vehicle = {
                "make_id": str(uuid.uuid4()),
                "model_id": str(uuid.uuid4()),
                "year": random.randint(2005, 2024),
            }
            attributes["fuel_type"] = random.choice(["gasoline", "diesel", "hybrid", "electric"])

        documents.append(
            {
                "id": str(uuid.uuid4()),
                "title": title,
                "description": description,
                "module": module,
                "category_id": category_id,
                "country": country,
                "city": city,
                "status": "active",
                "price": {
                    "amount": price_amount,
                    "currency": "EUR",
                    "type": price_type,
                },
                "price_type": price_type,
                "currency": "EUR",
                "seller_type": random.choice(["individual", "commercial"]),
                "is_premium": random.random() < 0.1,
                "is_showcase": random.random() < 0.05,
                "vehicle": vehicle,
                "attributes": attributes,
                "images": [f"https://picsum.photos/seed/{i}/800/600"],
                "published_at": created_at.isoformat(),
                "created_at": created_at.isoformat(),
                "updated_at": created_at.isoformat(),
            }
        )

    if documents:
        collection.insert_many(documents)

    print(f"Seeded {len(documents)} listings into Mongo collection '{DB_NAME}.listings'")


if __name__ == '__main__':
    main()
