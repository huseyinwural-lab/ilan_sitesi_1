from fastapi import APIRouter

from app.routers.mobile import (
    auth_routes,
    listing_routes,
    notification_routes,
    recommendation_routes,
    messaging_routes,
    verification_routes
)

api_router = APIRouter(prefix="/v2/mobile")

api_router.include_router(auth_routes.router, prefix="/auth", tags=["Mobile Auth"])
api_router.include_router(listing_routes.router, prefix="/listings", tags=["Mobile Listings"])
api_router.include_router(notification_routes.router, prefix="/notifications", tags=["Mobile Notifications"])
api_router.include_router(recommendation_routes.router, prefix="/recommendations", tags=["Mobile Recommendations"])
api_router.include_router(messaging_routes.router, prefix="/messages", tags=["Mobile Messaging"])
api_router.include_router(verification_routes.router, prefix="/verification", tags=["Mobile Verification"])
