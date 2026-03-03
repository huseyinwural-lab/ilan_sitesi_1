from app.routers.system.health_routes import router as health_router
from app.routers.system.sitemap_routes import router as sitemap_router
from app.routers.system.ops_routes import router as ops_router

__all__ = ["health_router", "sitemap_router", "ops_router"]