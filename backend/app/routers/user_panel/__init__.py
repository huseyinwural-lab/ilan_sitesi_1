from fastapi import APIRouter

from app.routers.user_panel import (
    my_listings,
    dealer_onboarding,
    dealer_routes,
    listings_v2
)

api_router = APIRouter(prefix="/v1/user-panel")

api_router.include_router(my_listings.router, prefix="/listings", tags=["User Panel Listings"])
api_router.include_router(dealer_onboarding.router, prefix="/dealer-onboarding", tags=["Dealer Onboarding"])
api_router.include_router(dealer_routes.router, prefix="/dealer", tags=["Dealer Profile"])
api_router.include_router(listings_v2.router, prefix="/listings-v2", tags=["User Panel Listings V2"])
