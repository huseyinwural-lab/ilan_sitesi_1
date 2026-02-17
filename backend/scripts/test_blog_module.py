
import asyncio
import os
import sys
import uuid
import httpx
from sqlalchemy import text

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from app.database import AsyncSessionLocal
from app.models.blog import BlogPost
from app.models.user import User
from server import create_access_token

async def test_blog_module():
    print("🚀 Starting Blog Module Test...")
    
    admin_id = str(uuid.uuid4())
    admin_email = "admin_blog@test.com"
    
    # 1. Setup Admin
    async with AsyncSessionLocal() as session:
        # Clean first
        await session.execute(text("DELETE FROM users WHERE email = 'admin_blog@test.com'"))
        await session.execute(text(f"INSERT INTO users (id, email, hashed_password, full_name, role, is_active, is_verified, country_scope, preferred_language, two_factor_enabled, created_at, updated_at) VALUES ('{admin_id}', '{admin_email}', 'hash', 'Admin User', 'super_admin', true, true, '[]', 'en', false, NOW(), NOW())"))
        await session.execute(text(f"DELETE FROM blog_posts WHERE slug = 'test-post'"))
        await session.commit()

    token = create_access_token({"sub": admin_id, "email": admin_email, "role": "super_admin"})
    headers = {"Authorization": f"Bearer {token}"}
    base_url = "http://localhost:8001/api/v1/blog"
    
    async with httpx.AsyncClient() as client:
        # 2. Create Post (Admin)
        print("\n🔹 1. Create Post...")
        payload = {
            "title": "Test Blog Post",
            "slug": "test-post",
            "body_html": "<p>Hello World</p>",
            "summary": "Short summary",
            "is_published": True,
            "tags": "news,update"
        }
        resp = await client.post(base_url, json=payload, headers=headers)
        
        if resp.status_code == 201:
            print("✅ Post Created")
        else:
            print(f"❌ Create Failed: {resp.text}")
            return

        # 3. List Posts (Public)
        print("\n🔹 2. List Posts...")
        resp = await client.get(base_url)
        # Check if response is 200 and is a list
        if resp.status_code != 200:
             print(f"❌ List Failed: {resp.status_code} {resp.text}")
             return
             
        posts = resp.json()
        if not isinstance(posts, list):
             print(f"❌ List Failed: Expected list, got {type(posts)}")
             print(posts)
             return

        target = next((p for p in posts if p["slug"] == "test-post"), None)
        
        if target:
            print(f"✅ Post found in list: {target['title']}")
        else:
            print("❌ Post NOT found in list")

        # 4. Get Detail (Public)
        print("\n🔹 3. Get Detail...")
        resp = await client.get(f"{base_url}/test-post")
        if resp.status_code == 200:
            data = resp.json()
            if data["body_html"] == "<p>Hello World</p>":
                print("✅ Content verified")
            else:
                print("❌ Content mismatch")
        else:
            print(f"❌ Detail Failed: {resp.status_code}")

    # Cleanup
    async with AsyncSessionLocal() as session:
        await session.execute(text(f"DELETE FROM blog_posts WHERE slug = 'test-post'"))
        await session.execute(text(f"DELETE FROM users WHERE id = '{admin_id}'"))
        await session.commit()

    print("\n🎉 Blog Module PASSED!")

if __name__ == "__main__":
    asyncio.run(test_blog_module())
