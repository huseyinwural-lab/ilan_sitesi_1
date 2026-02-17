
import logging
import hashlib
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from fastapi import Request
from app.models.analytics import ListingView
from app.models.moderation import Listing

logger = logging.getLogger(__name__)


async def track_interaction(
    db: AsyncSession,
    user_id,
    event_type: str,
    country_code: str,
    listing_id,
    category_id=None,
    city: str | None = None,
    meta_data: dict | None = None,
):
    """Compatibility shim used by public routes.

    Existing public endpoints import `track_interaction` to log key actions.
    The full analytics pipeline isn't wired end-to-end yet, so we implement
    a minimal no-op that keeps the app bootable.
    """
    # Intentionally no-op for now.
    return


class AnalyticsService:
    # Bot keyword list (Lowercase for case-insensitive matching)
    BOT_KEYWORDS = [
        "bot", "crawl", "spider", "slurp", "facebook", "twitter", "whatsapp", 
        "slack", "telegram", "pinterest", "linkedin", "instagram", "discord", 
        "curl", "wget", "python", "postman", "insomnia", "axios", "scrapy", 
        "headless", "phantomjs", "selenium", "playwright", "googlebot", "bingbot"
    ]

    def __init__(self, db: AsyncSession):
        self.db = db
        self.salt = os.environ.get("ANALYTICS_SALT", "random_salt_value")

    def _get_ip(self, request: Request) -> str:
        """Extracts IP address handling proxies"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0]
        return request.client.host if request.client else "unknown"

    def _hash_data(self, data: str) -> str:
        """Hashes data for privacy"""
        return hashlib.sha256(f"{data}{self.salt}".encode()).hexdigest()

    def _is_bot(self, user_agent: str) -> bool:
        if not user_agent:
            return True # Empty UA is suspicious
        ua = user_agent.lower()
        return any(keyword in ua for keyword in self.BOT_KEYWORDS)

    async def track_view(self, listing: Listing, request: Request, viewer_id: str = None):
        """
        Tracks a view for a listing with dedup and bot protection.
        """
        try:
            # 1. Owner Check
            if viewer_id and str(listing.user_id) == str(viewer_id):
                return # Owner viewing their own listing

            # 2. Bot Check
            user_agent = request.headers.get("user-agent", "")
            if self._is_bot(user_agent):
                # logger.debug(f"Bot blocked: {user_agent}")
                return

            # 3. Identity Hashing
            ip_address = self._get_ip(request)
            ip_hash = self._hash_data(ip_address)
            ua_hash = self._hash_data(user_agent)

            # 4. Deduplication (30 Minutes Window)
            # Check if this IP viewed this listing recently
            window_start = datetime.now(timezone.utc) - timedelta(minutes=30)
            stmt = select(ListingView).where(
                and_(
                    ListingView.listing_id == listing.id,
                    ListingView.ip_hash == ip_hash,
                    ListingView.created_at >= window_start
                )
            )
            result = await self.db.execute(stmt)
            if result.scalar_one_or_none():
                # Duplicate view
                return

            # 5. Record View (Atomic)
            # Create Audit Record
            view_record = ListingView(
                listing_id=listing.id,
                ip_hash=ip_hash,
                user_agent_hash=ua_hash
            )
            self.db.add(view_record)

            # Increment Counter Atomically
            # We use an UPDATE statement to avoid race conditions (read-modify-write)
            await self.db.execute(
                update(Listing)
                .where(Listing.id == listing.id)
                .values(view_count=Listing.view_count + 1)
            )
            
            # Commit logic is handled by the caller route usually, but here we want to ensure
            # stats are saved even if the main read transaction is read-only? 
            # Usually routes use one session. We should flush/commit here if we want to persist stats immediately.
            # Or rely on route commit.
            # Ideally, stats should not block response or fail main request.
            # But for simple implementation, we join the route's transaction.
            await self.db.commit() 
            
        except Exception as e:
            logger.error(f"Analytics Error: {e}")
            # Do not raise exception to avoid breaking the listing page load
