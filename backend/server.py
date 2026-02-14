
from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Query, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, func, and_, or_
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
import uuid
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
from asgi_correlation_id import CorrelationIdMiddleware
from app.core.logging import configure_logging
from app.middleware.logging_middleware import LoggingMiddleware
from app.core.redis_rate_limit import RedisRateLimiter

# Configure Structlog
configure_logging()

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Rate Limiters
# We use RedisRateLimiter now, not the deleted RateLimiter (Memory)
limiter_auth_login = RedisRateLimiter(redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0")) 
# Note: Dependency injection pattern for RedisRateLimiter might need refactoring 
# because it's a class with methods, not a callable dependency itself directly in the old style.
# But let's instantiate it.
limiter_auth_register = RedisRateLimiter(redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"))

# Import models
from app.models.base import Base
from app.models.user import User
from app.models.core import Country, FeatureFlag, AuditLog
from app.models.category import Category, CategoryTranslation
from app.models.attribute import Attribute, AttributeOption, CategoryAttributeMap
from app.models.menu import TopMenuItem, TopMenuSection, TopMenuLink
from app.models.home import HomeLayoutSettings, HomeShowcaseItem, HomeSpecialListing, AdSlot
from app.models.dealer import DealerApplication, Dealer, DealerUser
from app.models.premium import PremiumProduct, ListingPromotion, PremiumRankingRule
from app.models.moderation import Listing, ModerationAction, ModerationRule
from app.models.billing import VatRate, Invoice, InvoiceItem
from app.models.payment import StripeSettings, PaymentAttempt, StripeEvent, Refund

from app.models.commercial import DealerPackage, DealerSubscription
# Database setup
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://admin_user:admin_pass@localhost:5432/admin_panel')
# Force password match if needed due to environment reset
if 'admin_user' in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace('admin_pass', 'admin_pass') # No-op, just logic placeholder or env var override 
from app.models.monetization import SubscriptionPlan, UserSubscription, QuotaUsage
ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

from app.database import engine, AsyncSessionLocal
from app.dependencies import get_db, get_current_user, check_permissions, decode_token, security

# Settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-super-secret-key-change-in-production-2024')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
SUPPORTED_COUNTRIES = ['DE', 'CH', 'FR', 'AT']
SUPPORTED_LANGUAGES = ['tr', 'de', 'fr']

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

# Pydantic Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: str = "support"
    country_scope: List[str] = Field(default_factory=list)
    preferred_language: str = "tr"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[str] = None
    country_scope: Optional[List[str]] = None
    preferred_language: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    country_scope: List[str]
    preferred_language: str
    is_active: bool
    is_verified: bool
    created_at: str
    last_login: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class FeatureFlagCreate(BaseModel):
    key: str = Field(..., pattern=r'^[a-z_]+$', min_length=2, max_length=100)
    name: Dict[str, str]
    description: Optional[Dict[str, str]] = None
    scope: str = "feature"
    enabled_countries: List[str] = Field(default_factory=list)
    is_enabled: bool = False
    depends_on: List[str] = Field(default_factory=list)

class FeatureFlagUpdate(BaseModel):
    name: Optional[Dict[str, str]] = None
    description: Optional[Dict[str, str]] = None
    enabled_countries: Optional[List[str]] = None
    is_enabled: Optional[bool] = None
    depends_on: Optional[List[str]] = None

class CountryCreate(BaseModel):
    code: str = Field(..., min_length=2, max_length=5)
    name: Dict[str, str]
    default_currency: str = Field(..., min_length=3, max_length=5)
    default_language: str = "de"
    is_enabled: bool = True

class CountryUpdate(BaseModel):
    name: Optional[Dict[str, str]] = None
    default_currency: Optional[str] = None
    default_language: Optional[str] = None
    is_enabled: Optional[bool] = None
    support_email: Optional[str] = None

# Category Pydantic Models
class CategoryTranslationCreate(BaseModel):
    language: str
    name: str
    description: Optional[str] = None

class CategoryCreate(BaseModel):
    parent_id: Optional[str] = None
    module: str
    slug: Dict[str, str]
    icon: Optional[str] = None
    allowed_countries: List[str] = Field(default_factory=list)
    is_enabled: bool = True
    translations: List[CategoryTranslationCreate]

class CategoryUpdate(BaseModel):
    parent_id: Optional[str] = None
    slug: Optional[Dict[str, str]] = None
    icon: Optional[str] = None
    allowed_countries: Optional[List[str]] = None
    is_enabled: Optional[bool] = None
    is_visible_on_home: Optional[bool] = None
    sort_order: Optional[int] = None

# Attribute Pydantic Models
class AttributeOptionCreate(BaseModel):
    value: str
    label: Dict[str, str]
    sort_order: int = 0

class AttributeCreate(BaseModel):
    key: str = Field(..., pattern=r'^[a-z_]+$')
    name: Dict[str, str]
    attribute_type: str
    is_required: bool = False
    is_filterable: bool = False
    is_sortable: bool = False
    unit: Optional[str] = None
    options: List[AttributeOptionCreate] = Field(default_factory=list)

class AttributeUpdate(BaseModel):
    name: Optional[Dict[str, str]] = None
    is_required: Optional[bool] = None
    is_filterable: Optional[bool] = None
    is_sortable: Optional[bool] = None
    unit: Optional[str] = None
    is_active: Optional[bool] = None

# Menu Pydantic Models
class TopMenuItemCreate(BaseModel):
    key: str
    name: Dict[str, str]
    icon: Optional[str] = None
    required_module: Optional[str] = None
    allowed_countries: List[str] = Field(default_factory=list)
    sort_order: int = 0

class TopMenuItemUpdate(BaseModel):
    name: Optional[Dict[str, str]] = None
    icon: Optional[str] = None
    allowed_countries: Optional[List[str]] = None
    sort_order: Optional[int] = None
    is_enabled: Optional[bool] = None

# Database dependency - Removed (Imported from dependencies)
# Auth helpers - Removed (Imported from dependencies)

async def log_action(db: AsyncSession, action: str, resource_type: str, resource_id: Optional[str] = None, 
                    user_id: Optional[uuid.UUID] = None, user_email: Optional[str] = None,
                    old_values: Optional[dict] = None, new_values: Optional[dict] = None,
                    ip_address: Optional[str] = None, country_scope: Optional[str] = None):
    audit_log = AuditLog(action=action, resource_type=resource_type, resource_id=resource_id, user_id=user_id, user_email=user_email, old_values=old_values, new_values=new_values, ip_address=ip_address, country_scope=country_scope)
    db.add(audit_log)
    await db.commit()

def user_to_response(user: User) -> UserResponse:
    return UserResponse(id=str(user.id), email=user.email, full_name=user.full_name, role=user.role, country_scope=user.country_scope if isinstance(user.country_scope, list) else [], preferred_language=user.preferred_language, is_active=user.is_active, is_verified=user.is_verified, created_at=user.created_at.isoformat() if user.created_at else None, last_login=user.last_login.isoformat() if user.last_login else None)

# Seed data
async def seed_default_data(db: AsyncSession):
    logger.info("Seeding default data...")
    
    # Countries
    for code, name, currency, lang, email in [
        ("DE", {"tr": "Almanya", "de": "Deutschland", "fr": "Allemagne"}, "EUR", "de", "support@platform.de"),
        ("CH", {"tr": "İsviçre", "de": "Schweiz", "fr": "Suisse"}, "CHF", "de", "support@platform.ch"),
        ("FR", {"tr": "Fransa", "de": "Frankreich", "fr": "France"}, "EUR", "fr", "support@platform.fr"),
        ("AT", {"tr": "Avusturya", "de": "Österreich", "fr": "Autriche"}, "EUR", "de", "support@platform.at"),
    ]:
        exists = await db.execute(select(Country).where(Country.code == code))
        if not exists.scalar_one_or_none():
            db.add(Country(code=code, name=name, default_currency=currency, default_language=lang, support_email=email))
    
    # Feature Flags
    modules = [
        ("real_estate", {"tr": "Emlak", "de": "Immobilien", "fr": "Immobilier"}, True),
        ("vehicle", {"tr": "Vasıta", "de": "Fahrzeuge", "fr": "Véhicules"}, True),
        ("machinery", {"tr": "İş Makineleri", "de": "Baumaschinen", "fr": "Machines"}, False),
        ("services", {"tr": "Hizmetler", "de": "Dienstleistungen", "fr": "Services"}, False),
        ("jobs", {"tr": "İş İlanları", "de": "Stellenangebote", "fr": "Emplois"}, False),
    ]
    for key, name, enabled in modules:
        exists = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
        if not exists.scalar_one_or_none():
            db.add(FeatureFlag(key=key, name=name, scope="module", is_enabled=enabled, enabled_countries=["DE", "CH", "FR", "AT"] if enabled else []))
    
    features = [
        ("premium", {"tr": "Premium", "de": "Premium", "fr": "Premium"}),
        ("dealer", {"tr": "Bayi", "de": "Händler", "fr": "Concessionnaire"}),
        ("moderation", {"tr": "Moderasyon", "de": "Moderation", "fr": "Modération"}),
        ("messaging", {"tr": "Mesajlaşma", "de": "Nachrichten", "fr": "Messagerie"}),
        ("favorites", {"tr": "Favoriler", "de": "Favoriten", "fr": "Favoris"}),
        ("gdpr", {"tr": "GDPR", "de": "DSGVO", "fr": "RGPD"}),
        ("tax", {"tr": "Vergi", "de": "Steuer", "fr": "Taxe"}),
        ("billing", {"tr": "Faturalandırma", "de": "Abrechnung", "fr": "Facturation"}),
    ]
    for key, name in features:
        exists = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
        if not exists.scalar_one_or_none():
            db.add(FeatureFlag(key=key, name=name, scope="feature", is_enabled=True, enabled_countries=["DE", "CH", "FR", "AT"]))
    
    # Admin user - Password from env or default
    admin_password = os.environ.get('ADMIN_PASSWORD', 'Admin123!')
    exists = await db.execute(select(User).where(User.email == "admin@platform.com"))
    if not exists.scalar_one_or_none():
        db.add(User(email="admin@platform.com", hashed_password=get_password_hash(admin_password), full_name="System Administrator", role="super_admin", country_scope=["*"], is_active=True, is_verified=True))
    
    # Demo users
    demo_password = os.environ.get('DEMO_PASSWORD', 'Demo123!')
    for email, name, role, scope in [
        ("moderator@platform.de", "Hans Müller", "moderator", ["DE"]),
        ("finance@platform.com", "Marie Dupont", "finance", ["*"]),
        ("support@platform.ch", "Peter Schmidt", "support", ["CH", "DE", "AT"])
    ]:
        exists = await db.execute(select(User).where(User.email == email))
        if not exists.scalar_one_or_none():
            db.add(User(email=email, hashed_password=get_password_hash(demo_password), full_name=name, role=role, country_scope=scope, is_active=True, is_verified=True))
    
    # Top Menu Items
    menu_items = [
        ("real_estate", {"tr": "Emlak", "de": "Immobilien", "fr": "Immobilier"}, "building-2", "real_estate", 1),
        ("vehicle", {"tr": "Vasıta", "de": "Fahrzeuge", "fr": "Véhicules"}, "car", "vehicle", 2),
        ("spare_parts", {"tr": "Yedek Parça", "de": "Ersatzteile", "fr": "Pièces détachées"}, "settings", None, 3),
        ("shopping", {"tr": "Alışveriş", "de": "Einkaufen", "fr": "Shopping"}, "shopping-bag", None, 4),
        ("hobby", {"tr": "Hobi", "de": "Hobby", "fr": "Loisirs"}, "palette", None, 5),
        ("services", {"tr": "Hizmetler", "de": "Dienstleistungen", "fr": "Services"}, "briefcase", "services", 6),
        ("jobs", {"tr": "İş İlanları", "de": "Stellenangebote", "fr": "Emplois"}, "users", "jobs", 7),
    ]
    for key, name, icon, module, order in menu_items:
        exists = await db.execute(select(TopMenuItem).where(TopMenuItem.key == key))
        if not exists.scalar_one_or_none():
            is_enabled = module in ["real_estate", "vehicle"] if module else key in ["spare_parts", "shopping", "hobby"]
            db.add(TopMenuItem(key=key, name=name, icon=icon, required_module=module, sort_order=order, is_enabled=is_enabled, allowed_countries=["DE", "CH", "FR", "AT"]))
    
    # Home Layout Settings per country
    for code in ["DE", "CH", "FR", "AT"]:
        exists = await db.execute(select(HomeLayoutSettings).where(HomeLayoutSettings.country_code == code))
        if not exists.scalar_one_or_none():
            db.add(HomeLayoutSettings(country_code=code, block_order=["showcase", "special", "ads"], mobile_nav_mode="drawer"))
    
    # P1: Premium Products (seed)
    from decimal import Decimal
    premium_products = [
        ("SHOWCASE", {"tr": "Vitrin", "de": "Schaufenster", "fr": "Vitrine"}, "DE", "EUR", 9.99, 7),
        ("FEATURED", {"tr": "Öne Çıkar", "de": "Hervorheben", "fr": "Mettre en avant"}, "DE", "EUR", 4.99, 3),
        ("BUMP", {"tr": "Üste Taşı", "de": "Nach oben", "fr": "Remonter"}, "DE", "EUR", 2.99, 1),
        ("SHOWCASE", {"tr": "Vitrin", "de": "Schaufenster", "fr": "Vitrine"}, "CH", "CHF", 12.99, 7),
        ("FEATURED", {"tr": "Öne Çıkar", "de": "Hervorheben", "fr": "Mettre en avant"}, "CH", "CHF", 6.99, 3),
    ]
    for key, name, country, currency, price, days in premium_products:
        exists = await db.execute(select(PremiumProduct).where(and_(PremiumProduct.key == key, PremiumProduct.country == country)))
        if not exists.scalar_one_or_none():
            db.add(PremiumProduct(key=key, name=name, country=country, currency=currency, price_net=Decimal(str(price)), duration_days=days))
    
    # P1: VAT Rates (seed)
    vat_rates = [
        ("DE", Decimal("19.0"), "standard"),
        ("CH", Decimal("8.1"), "standard"),
        ("FR", Decimal("20.0"), "standard"),
        ("AT", Decimal("20.0"), "standard"),
    ]
    for country, rate, tax_type in vat_rates:
        exists = await db.execute(select(VatRate).where(and_(VatRate.country == country, VatRate.tax_type == tax_type, VatRate.is_active == True)))
        if not exists.scalar_one_or_none():
            db.add(VatRate(country=country, rate=rate, valid_from=datetime.now(timezone.utc), tax_type=tax_type))
    
    # P1: Moderation Rules (seed)
    for code in ["DE", "CH", "FR", "AT"]:
        exists = await db.execute(select(ModerationRule).where(ModerationRule.country == code))
        if not exists.scalar_one_or_none():
            db.add(ModerationRule(country=code, bad_words_enabled=True, bad_words_list=[], min_images_enabled=True, min_images_count=1))
    
    # P1: Premium Ranking Rules (seed)
    for code in ["DE", "CH", "FR", "AT"]:
        exists = await db.execute(select(PremiumRankingRule).where(PremiumRankingRule.country == code))
        if not exists.scalar_one_or_none():
            db.add(PremiumRankingRule(country=code, premium_first=True, weight_priority=60, weight_recency=40))
    
    # P1: Demo Dealer Application (seed)
    exists = await db.execute(select(DealerApplication).where(DealerApplication.company_name == "Auto Schmidt GmbH"))
    if not exists.scalar_one_or_none():
        db.add(DealerApplication(
            country="DE",
            dealer_type="auto_dealer",
            company_name="Auto Schmidt GmbH",
            vat_tax_no="DE123456789",
            address="Hauptstraße 1, 10115 Berlin",
            city="Berlin",
            website="https://auto-schmidt.de",
            contact_name="Hans Schmidt",
            contact_email="info@auto-schmidt.de",
            contact_phone="+49 30 12345678",
            status="pending"
        ))
    
    # P1: Demo Listings for moderation (seed)
    demo_user_result = await db.execute(select(User).where(User.email == "admin@platform.com"))
    demo_user = demo_user_result.scalar_one_or_none()
    if demo_user:
        for i, (title, module, country, price) in enumerate([
            ("Schöne 3-Zimmer Wohnung in Berlin", "real_estate", "DE", 250000),
            ("BMW 320i 2022 Modell", "vehicle", "DE", 35000),
            ("Appartement à Paris", "real_estate", "FR", 450000),
            ("Mercedes C200 zu verkaufen", "vehicle", "CH", 42000),
        ]):
            exists = await db.execute(select(Listing).where(Listing.title == title))
            if not exists.scalar_one_or_none():
                db.add(Listing(
                    title=title,
                    description=f"Demo listing for moderation queue - {title}",
                    module=module,
                    country=country,
                    price=price,
                    currency="CHF" if country == "CH" else "EUR",
                    user_id=demo_user.id,
                    images=[f"https://picsum.photos/800/600?random={i}"],
                    image_count=1,
                    status="pending"
                ))
    
    await db.commit()
    
    # P2: Stripe Settings (seed)
    # References to Env Vars - No real keys in DB!
    for country in ["DE", "CH", "FR", "AT"]:
        exists = await db.execute(select(StripeSettings).where(StripeSettings.country == country))
        if not exists.scalar_one_or_none():
            db.add(StripeSettings(
                country=country,
                is_enabled=True,
                secret_key_env_key=f"STRIPE_SECRET_KEY_{country}", # e.g. STRIPE_SECRET_KEY_DE
                webhook_secret_env_key=f"STRIPE_WEBHOOK_SECRET_{country}",
                publishable_key=f"pk_test_mock_{country}", # Mock for now
                account_mode="test"
            ))

    # P4: Dealer Packages (seed)
    from app.models.commercial import DealerPackage
    for country, currency in [("DE", "EUR"), ("CH", "CHF"), ("FR", "EUR"), ("AT", "EUR")]:
        for key, price, days, limit, prem in [
            ("BASIC", 49.00, 30, 10, 0),
            ("PRO", 149.00, 30, 50, 5),
            ("ENTERPRISE", 499.00, 30, 500, 20)
        ]:
            exists = await db.execute(select(DealerPackage).where(and_(DealerPackage.key == key, DealerPackage.country == country)))
            if not exists.scalar_one_or_none():
                db.add(DealerPackage(
                    key=key,
                    country=country,
                    name={"en": f"{key} Package"},
                    price_net=Decimal(str(price)),
                    currency=currency,
                    duration_days=days,
                    listing_limit=limit,
                    premium_quota=prem,
                    highlight_quota=prem # Same for now
                ))

    
    # P5: Pricing Engine Seeds (T2B)
    from app.models.pricing import PriceConfig, FreeQuotaConfig, CountryCurrencyMap
    
    # Currency Map
    for country, currency in [("DE", "EUR"), ("CH", "CHF"), ("FR", "EUR"), ("AT", "EUR")]:
        exists = await db.execute(select(CountryCurrencyMap).where(CountryCurrencyMap.country == country))
        if not exists.scalar_one_or_none():
            db.add(CountryCurrencyMap(country=country, currency=currency))
            
    # Price Configs (DE example)
    prices = [
        ("DE", "dealer", "pay_per_listing", 5.00, "EUR"),
        ("DE", "individual", "pay_per_listing", 2.00, "EUR"),
        ("CH", "dealer", "pay_per_listing", 8.00, "CHF"),
    ]
    for country, segment, ptype, price, curr in prices:
        exists = await db.execute(select(PriceConfig).where(and_(
            PriceConfig.country == country,
            PriceConfig.segment == segment,
            PriceConfig.pricing_type == ptype,
            PriceConfig.is_active == True
        )))
        if not exists.scalar_one_or_none():
            db.add(PriceConfig(
                country=country,
                segment=segment,
                pricing_type=ptype,
                unit_price_net=Decimal(str(price)),
                currency=curr,
                valid_from=datetime.now(timezone.utc)
            ))
            
    # Free Quota (DE Dealer)
    exists = await db.execute(select(FreeQuotaConfig).where(and_(
        FreeQuotaConfig.country == "DE",
        FreeQuotaConfig.segment == "dealer",
        FreeQuotaConfig.is_active == True
    )))
    if not exists.scalar_one_or_none():
        db.add(FreeQuotaConfig(
            country="DE",
            segment="dealer",
            quota_amount=10,
            period_days=30,
            quota_scope="listing_only"
        ))


    logger.info("Default data seeded")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application with PostgreSQL...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        async with AsyncSessionLocal() as session:
            try:
                await seed_default_data(session)
            except Exception as e:
                logger.error(f"SEED_FAILED (non-fatal): {e}")
                # Don't raise, allow app to start even if seed fails
    except Exception as e:
        logger.error(f"Critical startup error: {e}")
        raise e
        
    yield
    logger.info("Shutting down...")
    await engine.dispose()

app = FastAPI(title="Admin Panel API", description="Multi-country Admin Panel (PostgreSQL + Alembic)", version="1.0.0", lifespan=lifespan)

from app.core.exceptions import global_exception_handler
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Observability Middleware
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(LoggingMiddleware)

# Exception Handlers
app.add_exception_handler(RequestValidationError, global_exception_handler)
app.add_exception_handler(StarletteHTTPException, global_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

api_router = APIRouter(prefix="/api")

# Health check
@api_router.get("/")
async def root():
    return {"message": "Admin Panel API", "version": "1.0.0", "status": "healthy", "database": "PostgreSQL"}

@api_router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        # P6-005: Real DB Ping with Timeout (5 seconds)
        await db.execute(select(1).execution_options(timeout=5))
        return {"status": "healthy", "supported_countries": SUPPORTED_COUNTRIES, "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Database unavailable")

# ==================== AUTH ROUTES ====================
@api_router.post("/auth/register", response_model=UserResponse, status_code=201, dependencies=[Depends(limiter_auth_register)])
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=user_data.email, hashed_password=get_password_hash(user_data.password), full_name=user_data.full_name, role=user_data.role, country_scope=user_data.country_scope, preferred_language=user_data.preferred_language)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await log_action(db, "CREATE", "user", str(user.id), new_values={"email": user.email, "role": user.role})
    return user_to_response(user)

@api_router.post("/auth/login", response_model=TokenResponse, dependencies=[Depends(limiter_auth_login)])
async def login(credentials: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="User account is disabled")
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    await log_action(db, "LOGIN", "user", str(user.id), user_id=user.id, user_email=user.email, ip_address=request.client.host if request.client else None)
    return TokenResponse(access_token=create_access_token(token_data), refresh_token=create_refresh_token(token_data), user=user_to_response(user))

@api_router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token_endpoint(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    result = await db.execute(select(User).where(User.id == uuid.UUID(payload.get("sub"))))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    return TokenResponse(access_token=create_access_token(token_data), refresh_token=create_refresh_token(token_data), user=user_to_response(user))

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return user_to_response(current_user)

# ==================== USERS ROUTES ====================
@api_router.get("/users", response_model=List[UserResponse])
async def get_users(skip: int = 0, limit: int = 50, role: Optional[str] = None, search: Optional[str] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if search:
        query = query.where(or_(User.email.ilike(f"%{search}%"), User.full_name.ilike(f"%{search}%")))
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return [user_to_response(u) for u in result.scalars().all()]

@api_router.get("/users/count")
async def get_users_count(role: Optional[str] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    query = select(func.count(User.id))
    if role:
        query = query.where(User.role == role)
    result = await db.execute(query)
    return {"count": result.scalar()}

@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user_to_response(user)

@api_router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    old_values = {"role": user.role, "is_active": user.is_active}
    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)
    await log_action(db, "UPDATE", "user", user_id, user_id=current_user.id, user_email=current_user.email, old_values=old_values, new_values=user_data.model_dump(exclude_unset=True))
    return user_to_response(user)

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    if user_id == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await log_action(db, "DELETE", "user", user_id, user_id=current_user.id, user_email=current_user.email, old_values={"email": user.email})
    await db.delete(user)
    await db.commit()
    return {"message": "User deleted successfully"}

@api_router.post("/users/{user_id}/suspend")
async def suspend_user(user_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    if user_id == str(current_user.id):
        raise HTTPException(status_code=400, detail="Cannot suspend yourself")
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await db.commit()
    await log_action(db, "SUSPEND", "user", user_id, user_id=current_user.id, user_email=current_user.email)
    return {"message": "User suspended successfully"}

@api_router.post("/users/{user_id}/activate")
async def activate_user(user_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = True
    await db.commit()
    await log_action(db, "ACTIVATE", "user", user_id, user_id=current_user.id, user_email=current_user.email)
    return {"message": "User activated successfully"}

# ==================== FEATURE FLAGS ROUTES ====================
@api_router.get("/feature-flags")
async def get_feature_flags(scope: Optional[str] = None, enabled_only: bool = False, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(FeatureFlag)
    if scope:
        query = query.where(FeatureFlag.scope == scope)
    if enabled_only:
        query = query.where(FeatureFlag.is_enabled == True)
    query = query.order_by(FeatureFlag.scope, FeatureFlag.key)
    result = await db.execute(query)
    return [{"id": str(f.id), "key": f.key, "name": f.name, "description": f.description, "scope": f.scope, "enabled_countries": f.enabled_countries or [], "is_enabled": f.is_enabled, "depends_on": f.depends_on or [], "version": f.version, "created_at": f.created_at.isoformat() if f.created_at else None, "updated_at": f.updated_at.isoformat() if f.updated_at else None} for f in result.scalars().all()]

@api_router.get("/feature-flags/check/{key}")
async def check_feature_flag(key: str, country: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
    flag = result.scalar_one_or_none()
    if not flag:
        return {"key": key, "enabled": False, "exists": False}
    is_enabled = flag.is_enabled
    if country and is_enabled:
        enabled_countries = flag.enabled_countries or []
        is_enabled = country in enabled_countries or "*" in enabled_countries
    return {"key": key, "enabled": is_enabled, "exists": True}

@api_router.post("/feature-flags", status_code=201)
async def create_feature_flag(flag_data: FeatureFlagCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.key == flag_data.key))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Feature flag key already exists")
    flag = FeatureFlag(**flag_data.model_dump())
    db.add(flag)
    await db.commit()
    await db.refresh(flag)
    await log_action(db, "CREATE", "feature_flag", str(flag.id), user_id=current_user.id, user_email=current_user.email, new_values={"key": flag.key})
    return {"id": str(flag.id), "key": flag.key, "name": flag.name, "scope": flag.scope, "is_enabled": flag.is_enabled}

@api_router.patch("/feature-flags/{flag_id}")
async def update_feature_flag(flag_id: str, flag_data: FeatureFlagUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == uuid.UUID(flag_id)))
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    old_values = {"is_enabled": flag.is_enabled}
    for field, value in flag_data.model_dump(exclude_unset=True).items():
        setattr(flag, field, value)
    flag.version += 1
    flag.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(flag)
    await log_action(db, "UPDATE", "feature_flag", flag_id, user_id=current_user.id, user_email=current_user.email, old_values=old_values, new_values=flag_data.model_dump(exclude_unset=True))
    return {"id": str(flag.id), "key": flag.key, "is_enabled": flag.is_enabled, "version": flag.version}

@api_router.delete("/feature-flags/{flag_id}")
async def delete_feature_flag(flag_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == uuid.UUID(flag_id)))
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    await log_action(db, "DELETE", "feature_flag", flag_id, user_id=current_user.id, user_email=current_user.email, old_values={"key": flag.key})
    await db.delete(flag)
    await db.commit()
    return {"message": "Feature flag deleted successfully"}

@api_router.post("/feature-flags/{flag_id}/toggle")
async def toggle_feature_flag(flag_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == uuid.UUID(flag_id)))
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    old_state = flag.is_enabled
    flag.is_enabled = not flag.is_enabled
    flag.version += 1
    await db.commit()
    await log_action(db, "TOGGLE", "feature_flag", flag_id, user_id=current_user.id, user_email=current_user.email, old_values={"is_enabled": old_state}, new_values={"is_enabled": flag.is_enabled})
    return {"message": f"Feature flag {'enabled' if flag.is_enabled else 'disabled'}", "is_enabled": flag.is_enabled}

# ==================== COUNTRIES ROUTES ====================
@api_router.get("/countries")
async def get_countries(enabled_only: bool = False, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Country)
    if enabled_only:
        query = query.where(Country.is_enabled == True)
    query = query.order_by(Country.code)
    result = await db.execute(query)
    return [{"id": str(c.id), "code": c.code, "name": c.name, "default_currency": c.default_currency, "default_language": c.default_language, "area_unit": c.area_unit, "distance_unit": c.distance_unit, "weight_unit": c.weight_unit, "date_format": c.date_format, "number_format": c.number_format, "support_email": c.support_email, "is_enabled": c.is_enabled, "created_at": c.created_at.isoformat() if c.created_at else None, "updated_at": c.updated_at.isoformat() if c.updated_at else None} for c in result.scalars().all()]

@api_router.get("/countries/public")
async def get_public_countries(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Country).where(Country.is_enabled == True).order_by(Country.code))
    return [{"id": str(c.id), "code": c.code, "name": c.name, "default_currency": c.default_currency, "is_enabled": c.is_enabled} for c in result.scalars().all()]

@api_router.patch("/countries/{country_id}")
async def update_country(country_id: str, country_data: CountryUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    result = await db.execute(select(Country).where(Country.id == uuid.UUID(country_id)))
    country = result.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    for field, value in country_data.model_dump(exclude_unset=True).items():
        setattr(country, field, value)
    country.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(country)
    await log_action(db, "UPDATE", "country", country_id, user_id=current_user.id, user_email=current_user.email, new_values=country_data.model_dump(exclude_unset=True), country_scope=country.code)
    return {"id": str(country.id), "code": country.code, "is_enabled": country.is_enabled}

# ==================== CATEGORIES ROUTES (P0-1) ====================
@api_router.get("/categories")
async def get_categories(module: Optional[str] = None, country: Optional[str] = None, parent_id: Optional[str] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Category).where(Category.is_deleted == False)
    if module:
        query = query.where(Category.module == module)
    if parent_id:
        query = query.where(Category.parent_id == uuid.UUID(parent_id))
    else:
        query = query.where(Category.parent_id == None)
    query = query.order_by(Category.sort_order)
    result = await db.execute(query)
    categories = result.scalars().all()
    return [{
        "id": str(c.id),
        "parent_id": str(c.parent_id) if c.parent_id else None,
        "path": c.path,
        "depth": c.depth,
        "module": c.module,
        "slug": c.slug,
        "icon": c.icon,
        "is_enabled": c.is_enabled,
        "is_visible_on_home": c.is_visible_on_home,
        "allowed_countries": c.allowed_countries or [],
        "listing_count": c.listing_count,
        "sort_order": c.sort_order,
        "translations": [{"language": t.language, "name": t.name, "description": t.description} for t in c.translations] if c.translations else []
    } for c in categories]

@api_router.get("/categories/tree")
async def get_category_tree(module: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Get full category tree for a module"""
    result = await db.execute(select(Category).where(and_(Category.module == module, Category.is_deleted == False)).order_by(Category.path, Category.sort_order))
    categories = result.scalars().all()
    
    def build_tree(cats, parent_id=None):
        return [{
            "id": str(c.id),
            "slug": c.slug,
            "icon": c.icon,
            "is_enabled": c.is_enabled,
            "translations": [{"language": t.language, "name": t.name} for t in c.translations] if c.translations else [],
            "children": build_tree(cats, c.id)
        } for c in cats if c.parent_id == parent_id]
    
    return build_tree(categories)

@api_router.post("/categories", status_code=201)
async def create_category(cat_data: CategoryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    # Calculate path and depth
    path = ""
    depth = 0
    if cat_data.parent_id:
        parent_result = await db.execute(select(Category).where(Category.id == uuid.UUID(cat_data.parent_id)))
        parent = parent_result.scalar_one_or_none()
        if parent:
            depth = parent.depth + 1
    
    category = Category(
        parent_id=uuid.UUID(cat_data.parent_id) if cat_data.parent_id else None,
        module=cat_data.module,
        slug=cat_data.slug,
        icon=cat_data.icon,
        allowed_countries=cat_data.allowed_countries,
        is_enabled=cat_data.is_enabled,
        depth=depth
    )
    db.add(category)
    await db.flush()
    
    # Update path with actual ID
    if cat_data.parent_id:
        parent_result = await db.execute(select(Category).where(Category.id == uuid.UUID(cat_data.parent_id)))
        parent = parent_result.scalar_one_or_none()
        category.path = f"{parent.path}.{category.id}" if parent and parent.path else str(category.id)
    else:
        category.path = str(category.id)
    
    # Add translations
    for trans in cat_data.translations:
        db.add(CategoryTranslation(category_id=category.id, language=trans.language, name=trans.name, description=trans.description))
    
    await db.commit()
    await db.refresh(category)
    await log_action(db, "CREATE", "category", str(category.id), user_id=current_user.id, user_email=current_user.email, new_values={"module": category.module, "slug": category.slug})
    
    return {"id": str(category.id), "path": category.path, "depth": category.depth}

@api_router.patch("/categories/{category_id}")
async def update_category(category_id: str, cat_data: CategoryUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    result = await db.execute(select(Category).where(Category.id == uuid.UUID(category_id)))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    for field, value in cat_data.model_dump(exclude_unset=True).items():
        if field == "parent_id" and value:
            setattr(category, field, uuid.UUID(value))
        else:
            setattr(category, field, value)
    category.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await log_action(db, "UPDATE", "category", category_id, user_id=current_user.id, user_email=current_user.email, new_values=cat_data.model_dump(exclude_unset=True))
    return {"id": str(category.id), "is_enabled": category.is_enabled}

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    result = await db.execute(select(Category).where(Category.id == uuid.UUID(category_id)))
    category = result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    category.is_deleted = True
    category.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    await log_action(db, "DELETE", "category", category_id, user_id=current_user.id, user_email=current_user.email, old_values={"module": category.module})
    return {"message": "Category soft deleted"}

# ==================== ATTRIBUTES ROUTES (P0-2) ====================
@api_router.get("/attributes")
async def get_attributes(attribute_type: Optional[str] = None, filterable_only: bool = False, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Attribute).where(Attribute.is_active == True)
    if attribute_type:
        query = query.where(Attribute.attribute_type == attribute_type)
    if filterable_only:
        query = query.where(Attribute.is_filterable == True)
    query = query.order_by(Attribute.display_order)
    result = await db.execute(query)
    return [{
        "id": str(a.id),
        "key": a.key,
        "name": a.name,
        "attribute_type": a.attribute_type,
        "is_required": a.is_required,
        "is_filterable": a.is_filterable,
        "is_sortable": a.is_sortable,
        "unit": a.unit,
        "options": [{"id": str(o.id), "value": o.value, "label": o.label} for o in a.options] if a.options else []
    } for a in result.scalars().all()]

@api_router.post("/attributes", status_code=201)
async def create_attribute(attr_data: AttributeCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    result = await db.execute(select(Attribute).where(Attribute.key == attr_data.key))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Attribute key already exists")
    
    attribute = Attribute(key=attr_data.key, name=attr_data.name, attribute_type=attr_data.attribute_type, is_required=attr_data.is_required, is_filterable=attr_data.is_filterable, is_sortable=attr_data.is_sortable, unit=attr_data.unit)
    db.add(attribute)
    await db.flush()
    
    for opt in attr_data.options:
        db.add(AttributeOption(attribute_id=attribute.id, value=opt.value, label=opt.label, sort_order=opt.sort_order))
    
    await db.commit()
    await db.refresh(attribute)
    await log_action(db, "CREATE", "attribute", str(attribute.id), user_id=current_user.id, user_email=current_user.email, new_values={"key": attribute.key})
    return {"id": str(attribute.id), "key": attribute.key}

@api_router.patch("/attributes/{attribute_id}")
async def update_attribute(attribute_id: str, attr_data: AttributeUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    result = await db.execute(select(Attribute).where(Attribute.id == uuid.UUID(attribute_id)))
    attribute = result.scalar_one_or_none()
    if not attribute:
        raise HTTPException(status_code=404, detail="Attribute not found")
    for field, value in attr_data.model_dump(exclude_unset=True).items():
        setattr(attribute, field, value)
    attribute.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await log_action(db, "UPDATE", "attribute", attribute_id, user_id=current_user.id, user_email=current_user.email, new_values=attr_data.model_dump(exclude_unset=True))
    return {"id": str(attribute.id), "is_active": attribute.is_active}

@api_router.post("/attributes/{attribute_id}/options", status_code=201)
async def add_attribute_option(attribute_id: str, option_data: AttributeOptionCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    result = await db.execute(select(Attribute).where(Attribute.id == uuid.UUID(attribute_id)))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Attribute not found")
    option = AttributeOption(attribute_id=uuid.UUID(attribute_id), value=option_data.value, label=option_data.label, sort_order=option_data.sort_order)
    db.add(option)
    await db.commit()
    await db.refresh(option)
    return {"id": str(option.id), "value": option.value}

@api_router.post("/categories/{category_id}/attributes/{attribute_id}")
async def map_attribute_to_category(category_id: str, attribute_id: str, inherit_to_children: bool = True, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    mapping = CategoryAttributeMap(category_id=uuid.UUID(category_id), attribute_id=uuid.UUID(attribute_id), inherit_to_children=inherit_to_children)
    db.add(mapping)
    await db.commit()
    return {"message": "Attribute mapped to category"}

# ==================== TOP MENU ROUTES (P0-3) ====================
@api_router.get("/menu/top-items")
async def get_top_menu_items(country: Optional[str] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(TopMenuItem).order_by(TopMenuItem.sort_order)
    result = await db.execute(query)
    items = result.scalars().all()
    return [{
        "id": str(m.id),
        "key": m.key,
        "name": m.name,
        "icon": m.icon,
        "badge": m.badge,
        "required_module": m.required_module,
        "allowed_countries": m.allowed_countries or [],
        "sort_order": m.sort_order,
        "is_enabled": m.is_enabled,
        "sections": [{"id": str(s.id), "title": s.title, "links": [{"id": str(l.id), "label": l.label, "link_type": l.link_type, "target_ref": l.target_ref} for l in s.links]} for s in m.sections] if m.sections else []
    } for m in items]

@api_router.post("/menu/top-items", status_code=201)
async def create_top_menu_item(item_data: TopMenuItemCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    item = TopMenuItem(**item_data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    await log_action(db, "CREATE", "top_menu_item", str(item.id), user_id=current_user.id, user_email=current_user.email, new_values={"key": item.key})
    return {"id": str(item.id), "key": item.key}

@api_router.patch("/menu/top-items/{item_id}")
async def update_top_menu_item(item_id: str, item_data: TopMenuItemUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    result = await db.execute(select(TopMenuItem).where(TopMenuItem.id == uuid.UUID(item_id)))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Menu item not found")
    for field, value in item_data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    item.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await log_action(db, "UPDATE", "top_menu_item", item_id, user_id=current_user.id, user_email=current_user.email, new_values=item_data.model_dump(exclude_unset=True))
    return {"id": str(item.id), "is_enabled": item.is_enabled}

# ==================== HOME LAYOUT ROUTES (P0-4) ====================
@api_router.get("/home/layout/{country_code}")
async def get_home_layout(country_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HomeLayoutSettings).where(HomeLayoutSettings.country_code == country_code.upper()))
    layout = result.scalar_one_or_none()
    if not layout:
        return {"country_code": country_code, "block_order": ["showcase", "special", "ads"], "mobile_nav_mode": "drawer"}
    return {"id": str(layout.id), "country_code": layout.country_code, "block_order": layout.block_order, "mobile_nav_mode": layout.mobile_nav_mode, "show_mega_menu": layout.show_mega_menu}

@api_router.get("/home/showcase/{country_code}")
async def get_home_showcase(country_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HomeShowcaseItem).where(and_(HomeShowcaseItem.country_code == country_code.upper(), HomeShowcaseItem.is_active == True)).order_by(HomeShowcaseItem.sort_order))
    return [{"id": str(i.id), "listing_id": i.listing_id, "sort_order": i.sort_order} for i in result.scalars().all()]

@api_router.get("/home/special/{country_code}")
async def get_home_special(country_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HomeSpecialListing).where(and_(HomeSpecialListing.country_code == country_code.upper(), HomeSpecialListing.is_active == True)).order_by(HomeSpecialListing.sort_order))
    return [{"id": str(i.id), "listing_id": i.listing_id, "label": i.label, "dealer_only": i.dealer_only, "premium_only": i.premium_only} for i in result.scalars().all()]

@api_router.get("/home/ads/{country_code}")
async def get_home_ads(country_code: str, placement: str = "home_sidebar", db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdSlot).where(and_(AdSlot.country_code == country_code.upper(), AdSlot.placement == placement, AdSlot.is_active == True)).order_by(AdSlot.sort_order))
    return [{"id": str(a.id), "provider_type": a.provider_type, "config": a.config, "image_url": a.image_url, "click_url": a.click_url, "width": a.width, "height": a.height} for a in result.scalars().all()]

# ==================== AUDIT LOGS ROUTES ====================
@api_router.get("/audit-logs")
async def get_audit_logs(skip: int = 0, limit: int = 50, action: Optional[str] = None, resource_type: Optional[str] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin", "finance"]))):
    query = select(AuditLog)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return [{"id": str(l.id), "user_id": str(l.user_id) if l.user_id else None, "user_email": l.user_email, "action": l.action, "resource_type": l.resource_type, "resource_id": l.resource_id, "old_values": l.old_values, "new_values": l.new_values, "ip_address": l.ip_address, "country_scope": l.country_scope, "created_at": l.created_at.isoformat() if l.created_at else None} for l in result.scalars().all()]

@api_router.get("/audit-logs/actions")
async def get_audit_actions(current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    return {"actions": ["CREATE", "UPDATE", "DELETE", "LOGIN", "TOGGLE", "SUSPEND", "ACTIVATE"]}

# ==================== DASHBOARD STATS ====================
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    users_count = (await db.execute(select(func.count(User.id)))).scalar()
    active_users = (await db.execute(select(func.count(User.id)).where(User.is_active == True))).scalar()
    countries_count = (await db.execute(select(func.count(Country.id)).where(Country.is_enabled == True))).scalar()
    flags_enabled = (await db.execute(select(func.count(FeatureFlag.id)).where(FeatureFlag.is_enabled == True))).scalar()
    flags_total = (await db.execute(select(func.count(FeatureFlag.id)))).scalar()
    categories_count = (await db.execute(select(func.count(Category.id)).where(Category.is_deleted == False))).scalar()
    attributes_count = (await db.execute(select(func.count(Attribute.id)).where(Attribute.is_active == True))).scalar()
    
    role_stats = {}
    for role in ["super_admin", "country_admin", "moderator", "support", "finance"]:
        role_stats[role] = (await db.execute(select(func.count(User.id)).where(User.role == role))).scalar()
    
    logs_result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10))
    recent_logs = [{"id": str(l.id), "action": l.action, "resource_type": l.resource_type, "user_email": l.user_email, "created_at": l.created_at.isoformat() if l.created_at else None} for l in logs_result.scalars().all()]
    
    # Payment Stats (P2)
    payment_failures_24h = (await db.execute(select(func.count(PaymentAttempt.id)).where(and_(PaymentAttempt.status == 'failed', PaymentAttempt.created_at >= datetime.now(timezone.utc) - timedelta(hours=24))))).scalar() or 0

    # P1 stats
    pending_applications = (await db.execute(select(func.count(DealerApplication.id)).where(DealerApplication.status == "pending"))).scalar()
    pending_moderation = (await db.execute(select(func.count(Listing.id)).where(Listing.status == "pending"))).scalar()
    dealers_count = (await db.execute(select(func.count(Dealer.id)).where(Dealer.is_active == True))).scalar()
    
    return {
        "users": {"total": users_count, "active": active_users},
        "countries": {"enabled": countries_count},
        "feature_flags": {"enabled": flags_enabled, "total": flags_total},
        "categories": {"total": categories_count},
        "attributes": {"total": attributes_count},
        "dealers": {"total": dealers_count or 0, "pending_applications": pending_applications or 0},
        "moderation": {"pending": pending_moderation or 0},
        "users_by_role": role_stats,
        "recent_activity": recent_logs,
        "payment_failures_24h": payment_failures_24h
    }

# ==================== P1 ROUTES ====================
# Import P1 functions
from app.routers.p1_routes import (
    get_dealer_applications, get_dealer_application, review_dealer_application,
    get_dealers, update_dealer, DealerApplicationReview, DealerUpdate,
    get_premium_products, create_premium_product, update_premium_product,
    PremiumProductCreate, PremiumProductUpdate, get_ranking_rules, update_ranking_rule, RankingRuleUpdate,
    get_moderation_queue, get_moderation_queue_count, get_listing_detail, moderate_listing,
    ModerationActionCreate, get_moderation_rules, update_moderation_rule, ModerationRuleUpdate,
    get_vat_rates, create_vat_rate, update_vat_rate, VatRateCreate, VatRateUpdate,
    get_invoices, get_invoice_detail
)

# Wrapper to inject dependencies
@api_router.get("/dealer-applications")

async def get_dealer_apps(country: Optional[str] = None, dealer_type: Optional[str] = None, status: Optional[str] = None, skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    from app.routers.p1_routes import get_dealer_applications
    return await get_dealer_applications(country, dealer_type, status, skip, limit, db, current_user)

@api_router.get("/dealer-applications/{app_id}")
async def get_dealer_app(app_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    from app.routers.p1_routes import get_dealer_application
    return await get_dealer_application(app_id, db, current_user)

@api_router.post("/dealer-applications/{app_id}/review")
async def review_dealer_app(app_id: str, review: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    from app.routers.p1_routes import review_dealer_application, DealerApplicationReview
    return await review_dealer_application(app_id, DealerApplicationReview(**review), db, current_user)

@api_router.get("/dealers")
async def list_dealers(country: Optional[str] = None, is_active: Optional[bool] = None, skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    from app.routers.p1_routes import get_dealers
    return await get_dealers(country, is_active, skip, limit, db, current_user)

@api_router.patch("/dealers/{dealer_id}")
async def update_dealer_endpoint(dealer_id: str, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    from app.routers.p1_routes import update_dealer, DealerUpdate
    return await update_dealer(dealer_id, DealerUpdate(**data), db, current_user)

@api_router.get("/premium-products")
async def list_premium_products(country: Optional[str] = None, is_active: Optional[bool] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.routers.p1_routes import get_premium_products
    return await get_premium_products(country, is_active, db, current_user)

@api_router.post("/premium-products")
async def create_premium_product_endpoint(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    from app.routers.p1_routes import create_premium_product, PremiumProductCreate
    return await create_premium_product(PremiumProductCreate(**data), db, current_user)

@api_router.patch("/premium-products/{product_id}")
async def update_premium_product_endpoint(product_id: str, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    from app.routers.p1_routes import update_premium_product, PremiumProductUpdate
    return await update_premium_product(product_id, PremiumProductUpdate(**data), db, current_user)

@api_router.post("/premium-products/promotions")
async def create_promotion_endpoint(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    from app.routers.p1_routes import create_listing_promotion, ListingPromotionCreate
    return await create_listing_promotion(ListingPromotionCreate(**data), db, current_user)


@api_router.get("/moderation/queue")
async def get_mod_queue(country: Optional[str] = None, module: Optional[str] = None, status: str = "pending", is_dealer: Optional[bool] = None, is_premium: Optional[bool] = None, skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin", "moderator"]))):
    from app.routers.p1_routes import get_moderation_queue
    return await get_moderation_queue(country, module, status, is_dealer, is_premium, skip, limit, db, current_user)

@api_router.get("/moderation/queue/count")
async def get_mod_count(country: Optional[str] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin", "moderator"]))):
    from app.routers.p1_routes import get_moderation_queue_count
    return await get_moderation_queue_count(country, db, current_user)

@api_router.get("/moderation/listings/{listing_id}")
async def get_mod_listing(listing_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin", "moderator"]))):
    from app.routers.p1_routes import get_listing_detail
    return await get_listing_detail(listing_id, db, current_user)

@api_router.post("/moderation/listings/{listing_id}/action")
async def moderate_listing_endpoint(listing_id: str, action: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin", "moderator"]))):
    from app.routers.p1_routes import moderate_listing, ModerationActionCreate
    return await moderate_listing(listing_id, ModerationActionCreate(**action), db, current_user)

@api_router.get("/moderation/rules")
async def get_mod_rules(db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    from app.routers.p1_routes import get_moderation_rules
    return await get_moderation_rules(db, current_user)

@api_router.patch("/moderation/rules/{country}")
async def update_mod_rule(country: str, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    from app.routers.p1_routes import update_moderation_rule, ModerationRuleUpdate
    return await update_moderation_rule(country, ModerationRuleUpdate(**data), db, current_user)

@api_router.get("/vat-rates")
async def list_vat_rates(country: Optional[str] = None, is_active: Optional[bool] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "finance"]))):
    from app.routers.p1_routes import get_vat_rates
    return await get_vat_rates(country, is_active, db, current_user)

from app.routers import commercial_routes, admin_routes, search_routes, admin_mdm_routes
app.include_router(api_router)
app.include_router(commercial_routes.router, prefix="/api/v1")
app.include_router(admin_routes.router, prefix="/api/v1")
app.include_router(admin_mdm_routes.router, prefix="/api/v1/admin")
app.include_router(search_routes.router, prefix="/api")

# P1: Invoice Routes
@api_router.get("/invoices")
async def list_invoices(country: Optional[str] = None, status: Optional[str] = None, customer_type: Optional[str] = None, skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "finance"]))):
    return await get_invoices(country, status, customer_type, skip, limit, db, current_user)

@api_router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "finance"]))):
    return await get_invoice_detail(invoice_id, db, current_user)

from app.routers import payment_routes
app.include_router(payment_routes.router, prefix="/api/v1")

# P11: Billing Routes
from app.routers import billing_routes
from app.routers import billing_webhook
app.include_router(billing_webhook.router, prefix="/api")

from app.routers import billing_read_routes
app.include_router(billing_read_routes.router, prefix="/api")

app.include_router(billing_routes.router, prefix="/api")



from app.routers import listing_routes
app.include_router(listing_routes.router, prefix="/api")
