import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))
load_dotenv(ROOT_DIR / ".env")
load_dotenv(ROOT_DIR / ".env.local", override=True)

url = os.environ.get("DATABASE_URL")
if not url:
    raise SystemExit("DATABASE_URL missing")

engine = create_engine(url)
with engine.connect() as conn:
    rows = conn.execute(text("SELECT id, provider, provider_payment_id, status FROM payments LIMIT 10")).fetchall()
    for row in rows:
        print(row)
