import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
import uuid

# Path setup
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT_DIR))

from dotenv import load_dotenv
from app.mongo import get_mongo_client, get_db_name
from app.core.security import get_password_hash

load_dotenv(ROOT_DIR / ".env")


async def reset_admin_password():
    print("🔄 Resetting Admin Password (Mongo)...")

    client = get_mongo_client()
    db = client[get_db_name()]

    now_iso = datetime.now(timezone.utc).isoformat()
    email = "admin@platform.com"
    new_hash = get_password_hash("Admin123!")

    existing = await db.users.find_one({"email": email}, {"_id": 0})
    if existing:
        await db.users.update_one({"email": email}, {"$set": {"hashed_password": new_hash, "is_active": True, "updated_at": now_iso}})
        print("✅ Password reset to 'Admin123!'")
    else:
        await db.users.insert_one(
            {
                "id": str(uuid.uuid4()),
                "email": email,
                "hashed_password": new_hash,
                "full_name": "System Administrator",
                "role": "super_admin",
                "is_active": True,
                "is_verified": True,
                "country_scope": ["*"],
                "preferred_language": "tr",
                "created_at": now_iso,
                "last_login": None,
            }
        )
        print("✅ Admin user created with password 'Admin123!'")

    client.close()


if __name__ == "__main__":
    asyncio.run(reset_admin_password())
