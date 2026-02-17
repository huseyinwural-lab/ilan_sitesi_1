
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.dependencies import get_db, check_permissions
from app.models.blog import BlogPost
from app.models.user import User
from pydantic import BaseModel, Field
from typing import Optional
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/v1/blog", tags=["blog"])

class BlogPostCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=200)
    slug: str = Field(..., min_length=3, max_length=200)
    summary: Optional[str] = None
    body_html: str
    cover_image: Optional[str] = None
    tags: Optional[str] = None
    is_published: bool = False

# --- Public Endpoints ---

@router.get("")
async def list_posts(
    skip: int = 0,
    limit: int = 10,
    tag: str = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(BlogPost).where(BlogPost.is_published == True)
    
    if tag:
        query = query.where(BlogPost.tags.ilike(f"%{tag}%"))
        
    query = query.order_by(desc(BlogPost.published_at))
    query = query.offset(skip).limit(limit)
    
    res = await db.execute(query)
    posts = res.scalars().all()
    
    return [{
        "slug": p.slug,
        "title": p.title,
        "summary": p.summary,
        "cover_image": p.cover_image,
        "author": p.author,
        "published_at": p.published_at,
        "tags": p.tags.split(",") if p.tags else []
    } for p in posts]

@router.get("/{slug}")
async def get_post(slug: str, db: AsyncSession = Depends(get_db)):
    stmt = select(BlogPost).where(BlogPost.slug == slug, BlogPost.is_published == True)
    post = (await db.execute(stmt)).scalar_one_or_none()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    return {
        "slug": post.slug,
        "title": post.title,
        "body_html": post.body_html,
        "summary": post.summary,
        "cover_image": post.cover_image,
        "author": post.author,
        "published_at": post.published_at,
        "tags": post.tags.split(",") if post.tags else [],
        "meta_title": post.meta_title or post.title,
        "meta_description": post.meta_description or post.summary
    }

# --- Admin Endpoints ---

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_post(
    data: BlogPostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "content_editor"])) # Content Editor rolü eklenebilir
):
    # Check slug
    exists = (await db.execute(select(BlogPost).where(BlogPost.slug == data.slug))).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Slug already exists")
        
    post = BlogPost(
        title=data.title,
        slug=data.slug,
        summary=data.summary,
        body_html=data.body_html,
        cover_image=data.cover_image,
        tags=data.tags,
        is_published=data.is_published,
        published_at=datetime.now(timezone.utc) if data.is_published else None,
        author=current_user.full_name
    )
    db.add(post)
    await db.commit()
    
    return {"slug": post.slug, "status": "created"}
