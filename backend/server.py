from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from sqlalchemy import text

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from app.core.database import engine, Base, AsyncSessionLocal
from app.core.config import settings
from app.routers import (
    auth_router, 
    users_router, 
    feature_flags_router,
    countries_router,
    audit_router
)
from app.models import User, FeatureFlag, Country, AuditLog
from app.services.seed import seed_default_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application...")
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Seed data if empty
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT COUNT(*) FROM countries"))
        count = result.scalar()
        if count == 0:
            logger.info("Seeding default data...")
            await seed_default_data(session)
            logger.info("Default data seeded successfully")
    
    yield
    
    logger.info("Shutting down application...")
    await engine.dispose()

# Create the main app
app = FastAPI(
    title="Admin Panel API",
    description="Multi-country Admin Panel for Classified Ads Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Health check
@api_router.get("/")
async def root():
    return {"message": "Admin Panel API", "version": "1.0.0", "status": "healthy"}

@api_router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "supported_countries": settings.SUPPORTED_COUNTRIES,
        "supported_languages": settings.SUPPORTED_LANGUAGES
    }

# Include routers
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(feature_flags_router)
api_router.include_router(countries_router)
api_router.include_router(audit_router)

# Include the main router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.CORS_ORIGINS.split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
