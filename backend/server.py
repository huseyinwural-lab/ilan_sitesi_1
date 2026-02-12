from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Query, Request
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, DateTime, JSON, Integer, Text, Enum as SQLEnum, select, func, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database setup
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://admin_user:admin_pass@localhost:5432/admin_panel')
ASYNC_DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')

engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

# Settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-super-secret-key-change-in-production-2024')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
SUPPORTED_COUNTRIES = ['DE', 'CH', 'FR', 'AT']
SUPPORTED_LANGUAGES = ['tr', 'de', 'fr']

# Configure logging
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

# Enums
class UserRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    COUNTRY_ADMIN = "country_admin"
    MODERATOR = "moderator"
    SUPPORT = "support"
    FINANCE = "finance"

class FeatureScope(str, Enum):
    MODULE = "module"
    FEATURE = "feature"

# SQLAlchemy Models
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="support", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    country_scope: Mapped[dict] = mapped_column(JSON, default=list)
    preferred_language: Mapped[str] = mapped_column(String(5), default='tr')
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

class FeatureFlag(Base):
    __tablename__ = "feature_flags"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[dict] = mapped_column(JSON, nullable=False)
    description: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    scope: Mapped[str] = mapped_column(String(20), default="feature", nullable=False)
    enabled_countries: Mapped[dict] = mapped_column(JSON, default=list)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    depends_on: Mapped[dict] = mapped_column(JSON, default=list)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Country(Base):
    __tablename__ = "countries"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(5), unique=True, nullable=False, index=True)
    name: Mapped[dict] = mapped_column(JSON, nullable=False)
    default_currency: Mapped[str] = mapped_column(String(5), nullable=False)
    default_language: Mapped[str] = mapped_column(String(5), default='de')
    area_unit: Mapped[str] = mapped_column(String(10), default='m²')
    distance_unit: Mapped[str] = mapped_column(String(10), default='km')
    weight_unit: Mapped[str] = mapped_column(String(10), default='kg')
    date_format: Mapped[str] = mapped_column(String(20), default='DD.MM.YYYY')
    number_format: Mapped[str] = mapped_column(String(20), default='1.234,56')
    support_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    support_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    old_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    metadata_info: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    country_scope: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    is_pii_scrubbed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

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
    area_unit: str = "m²"
    distance_unit: str = "km"
    weight_unit: str = "kg"
    date_format: str = "DD.MM.YYYY"
    number_format: str = "1.234,56"
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    is_enabled: bool = True

class CountryUpdate(BaseModel):
    name: Optional[Dict[str, str]] = None
    default_currency: Optional[str] = None
    default_language: Optional[str] = None
    is_enabled: Optional[bool] = None
    support_email: Optional[str] = None
    support_phone: Optional[str] = None

# Database dependency
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Auth helpers
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise credentials_exception
    user_id = payload.get("sub")
    if not user_id:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    
    if not user:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

def check_permissions(required_roles: list):
    async def permission_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return permission_checker

# Audit helper
async def log_action(db: AsyncSession, action: str, resource_type: str, resource_id: Optional[str] = None, 
                    user_id: Optional[uuid.UUID] = None, user_email: Optional[str] = None,
                    old_values: Optional[dict] = None, new_values: Optional[dict] = None,
                    ip_address: Optional[str] = None, country_scope: Optional[str] = None):
    audit_log = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        user_email=user_email,
        old_values=old_values,
        new_values=new_values,
        ip_address=ip_address,
        country_scope=country_scope
    )
    db.add(audit_log)
    await db.commit()

# Seed data
async def seed_default_data(db: AsyncSession):
    # Check if data exists
    result = await db.execute(select(func.count(Country.id)))
    if result.scalar() > 0:
        return
    
    logger.info("Seeding default data...")
    
    # Countries
    countries = [
        Country(code="DE", name={"tr": "Almanya", "de": "Deutschland", "fr": "Allemagne"}, default_currency="EUR", default_language="de", support_email="support@platform.de"),
        Country(code="CH", name={"tr": "İsviçre", "de": "Schweiz", "fr": "Suisse"}, default_currency="CHF", default_language="de", number_format="1'234.56", support_email="support@platform.ch"),
        Country(code="FR", name={"tr": "Fransa", "de": "Frankreich", "fr": "France"}, default_currency="EUR", default_language="fr", date_format="DD/MM/YYYY", number_format="1 234,56", support_email="support@platform.fr"),
        Country(code="AT", name={"tr": "Avusturya", "de": "Österreich", "fr": "Autriche"}, default_currency="EUR", default_language="de", support_email="support@platform.at"),
    ]
    for c in countries:
        db.add(c)
    
    # Feature Flags - Modules
    modules = [
        FeatureFlag(key="real_estate", name={"tr": "Emlak", "de": "Immobilien", "fr": "Immobilier"}, description={"tr": "Emlak ilanları modülü", "de": "Immobilienanzeigen Modul", "fr": "Module immobilier"}, scope="module", is_enabled=True, enabled_countries=["DE", "CH", "FR", "AT"]),
        FeatureFlag(key="vehicle", name={"tr": "Vasıta", "de": "Fahrzeuge", "fr": "Véhicules"}, description={"tr": "Araç ilanları modülü", "de": "Fahrzeuganzeigen Modul", "fr": "Module véhicules"}, scope="module", is_enabled=True, enabled_countries=["DE", "CH", "FR", "AT"]),
        FeatureFlag(key="machinery", name={"tr": "İş Makineleri", "de": "Baumaschinen", "fr": "Machines"}, description={"tr": "İş makineleri modülü", "de": "Baumaschinen Modul", "fr": "Module machines"}, scope="module", is_enabled=False, enabled_countries=[]),
        FeatureFlag(key="services", name={"tr": "Hizmetler", "de": "Dienstleistungen", "fr": "Services"}, description={"tr": "Hizmet ilanları modülü", "de": "Dienstleistungen Modul", "fr": "Module services"}, scope="module", is_enabled=False, enabled_countries=[]),
        FeatureFlag(key="jobs", name={"tr": "İş İlanları", "de": "Stellenangebote", "fr": "Emplois"}, description={"tr": "İş ilanları modülü", "de": "Stellenangebote Modul", "fr": "Module emplois"}, scope="module", is_enabled=False, enabled_countries=[]),
    ]
    for m in modules:
        db.add(m)
    
    # Feature Flags - Features
    features = [
        FeatureFlag(key="premium", name={"tr": "Premium", "de": "Premium", "fr": "Premium"}, description={"tr": "Premium ilan özellikleri", "de": "Premium-Anzeigenfunktionen", "fr": "Fonctionnalités premium"}, scope="feature", is_enabled=True, enabled_countries=["DE", "CH", "FR", "AT"]),
        FeatureFlag(key="dealer", name={"tr": "Bayi", "de": "Händler", "fr": "Concessionnaire"}, description={"tr": "Bayi hesap yönetimi", "de": "Händlerkontoverwaltung", "fr": "Gestion des comptes concessionnaires"}, scope="feature", is_enabled=True, enabled_countries=["DE", "CH", "FR", "AT"]),
        FeatureFlag(key="moderation", name={"tr": "Moderasyon", "de": "Moderation", "fr": "Modération"}, description={"tr": "İlan moderasyon sistemi", "de": "Anzeigenmoderierungssystem", "fr": "Système de modération"}, scope="feature", is_enabled=True, enabled_countries=["DE", "CH", "FR", "AT"]),
        FeatureFlag(key="messaging", name={"tr": "Mesajlaşma", "de": "Nachrichten", "fr": "Messagerie"}, description={"tr": "Kullanıcı mesajlaşma", "de": "Benutzernachrichten", "fr": "Messagerie utilisateur"}, scope="feature", is_enabled=True, enabled_countries=["DE", "CH", "FR", "AT"]),
        FeatureFlag(key="favorites", name={"tr": "Favoriler", "de": "Favoriten", "fr": "Favoris"}, description={"tr": "İlan favorileme", "de": "Anzeigen-Favoriten", "fr": "Annonces favorites"}, scope="feature", is_enabled=True, enabled_countries=["DE", "CH", "FR", "AT"]),
        FeatureFlag(key="gdpr", name={"tr": "GDPR", "de": "DSGVO", "fr": "RGPD"}, description={"tr": "GDPR uyumluluk araçları", "de": "DSGVO-Compliance-Tools", "fr": "Outils de conformité RGPD"}, scope="feature", is_enabled=True, enabled_countries=["DE", "CH", "FR", "AT"]),
        FeatureFlag(key="tax", name={"tr": "Vergi", "de": "Steuer", "fr": "Taxe"}, description={"tr": "Vergi hesaplama motoru", "de": "Steuerberechnungsmodul", "fr": "Module de calcul des taxes"}, scope="feature", is_enabled=True, enabled_countries=["DE", "CH", "FR", "AT"]),
        FeatureFlag(key="billing", name={"tr": "Faturalandırma", "de": "Abrechnung", "fr": "Facturation"}, description={"tr": "Fatura yönetimi", "de": "Rechnungsverwaltung", "fr": "Gestion des factures"}, scope="feature", is_enabled=True, enabled_countries=["DE", "CH", "FR", "AT"], depends_on=["tax"]),
    ]
    for f in features:
        db.add(f)
    
    # Admin User
    admin = User(
        email="admin@platform.com",
        hashed_password=get_password_hash("Admin123!"),
        full_name="System Administrator",
        role="super_admin",
        country_scope=["*"],
        preferred_language="tr",
        is_active=True,
        is_verified=True
    )
    db.add(admin)
    
    # Demo Users
    demo_users = [
        User(email="moderator@platform.de", hashed_password=get_password_hash("Demo123!"), full_name="Hans Müller", role="moderator", country_scope=["DE"], preferred_language="de", is_active=True, is_verified=True),
        User(email="finance@platform.com", hashed_password=get_password_hash("Demo123!"), full_name="Marie Dupont", role="finance", country_scope=["*"], preferred_language="fr", is_active=True, is_verified=True),
        User(email="support@platform.ch", hashed_password=get_password_hash("Demo123!"), full_name="Peter Schmidt", role="support", country_scope=["CH", "DE", "AT"], preferred_language="de", is_active=True, is_verified=True),
    ]
    for u in demo_users:
        db.add(u)
    
    await db.commit()
    logger.info("Default data seeded successfully")

# Helper to convert User to response
def user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        country_scope=user.country_scope if isinstance(user.country_scope, list) else [],
        preferred_language=user.preferred_language,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login=user.last_login.isoformat() if user.last_login else None
    )

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        await seed_default_data(session)
    
    yield
    
    logger.info("Shutting down...")
    await engine.dispose()

# Create app
app = FastAPI(title="Admin Panel API", description="Multi-country Admin Panel (PostgreSQL)", version="1.0.0", lifespan=lifespan)
api_router = APIRouter(prefix="/api")

# Routes
@api_router.get("/")
async def root():
    return {"message": "Admin Panel API", "version": "1.0.0", "status": "healthy", "database": "PostgreSQL"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "supported_countries": SUPPORTED_COUNTRIES, "supported_languages": SUPPORTED_LANGUAGES, "database": "PostgreSQL"}

# Auth routes
@api_router.post("/auth/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        country_scope=user_data.country_scope,
        preferred_language=user_data.preferred_language
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    await log_action(db, "CREATE", "user", str(user.id), new_values={"email": user.email, "role": user.role})
    return user_to_response(user)

@api_router.post("/auth/login", response_model=TokenResponse)
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
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    await log_action(db, "LOGIN", "user", str(user.id), user_id=user.id, user_email=user.email, ip_address=request.client.host if request.client else None)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=user_to_response(user))

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
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token, user=user_to_response(user))

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return user_to_response(current_user)

# Users routes
@api_router.get("/users", response_model=List[UserResponse])
async def get_users(skip: int = 0, limit: int = 50, role: Optional[str] = None, country: Optional[str] = None, search: Optional[str] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    query = select(User)
    if role:
        query = query.where(User.role == role)
    if search:
        query = query.where((User.email.ilike(f"%{search}%")) | (User.full_name.ilike(f"%{search}%")))
    
    query = query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    return [user_to_response(u) for u in users]

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
    update_data = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    user.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(user)
    
    await log_action(db, "UPDATE", "user", user_id, user_id=current_user.id, user_email=current_user.email, old_values=old_values, new_values=update_data)
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
    user.updated_at = datetime.now(timezone.utc)
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
    user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    
    await log_action(db, "ACTIVATE", "user", user_id, user_id=current_user.id, user_email=current_user.email)
    return {"message": "User activated successfully"}

# Feature Flags routes
@api_router.get("/feature-flags")
async def get_feature_flags(scope: Optional[str] = None, country: Optional[str] = None, enabled_only: bool = False, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(FeatureFlag)
    if scope:
        query = query.where(FeatureFlag.scope == scope)
    if enabled_only:
        query = query.where(FeatureFlag.is_enabled == True)
    
    query = query.order_by(FeatureFlag.scope, FeatureFlag.key)
    result = await db.execute(query)
    flags = result.scalars().all()
    
    return [{
        "id": str(f.id),
        "key": f.key,
        "name": f.name,
        "description": f.description,
        "scope": f.scope,
        "enabled_countries": f.enabled_countries if isinstance(f.enabled_countries, list) else [],
        "is_enabled": f.is_enabled,
        "depends_on": f.depends_on if isinstance(f.depends_on, list) else [],
        "version": f.version,
        "created_at": f.created_at.isoformat() if f.created_at else None,
        "updated_at": f.updated_at.isoformat() if f.updated_at else None
    } for f in flags]

@api_router.get("/feature-flags/check/{key}")
async def check_feature_flag(key: str, country: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.key == key))
    flag = result.scalar_one_or_none()
    if not flag:
        return {"key": key, "enabled": False, "exists": False}
    
    is_enabled = flag.is_enabled
    if country and is_enabled:
        enabled_countries = flag.enabled_countries if isinstance(flag.enabled_countries, list) else []
        is_enabled = country in enabled_countries or "*" in enabled_countries
    return {"key": key, "enabled": is_enabled, "exists": True}

@api_router.get("/feature-flags/{flag_id}")
async def get_feature_flag(flag_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == uuid.UUID(flag_id)))
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return {
        "id": str(flag.id),
        "key": flag.key,
        "name": flag.name,
        "description": flag.description,
        "scope": flag.scope,
        "enabled_countries": flag.enabled_countries,
        "is_enabled": flag.is_enabled,
        "depends_on": flag.depends_on,
        "version": flag.version,
        "created_at": flag.created_at.isoformat(),
        "updated_at": flag.updated_at.isoformat()
    }

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
    
    return {
        "id": str(flag.id),
        "key": flag.key,
        "name": flag.name,
        "description": flag.description,
        "scope": flag.scope,
        "enabled_countries": flag.enabled_countries,
        "is_enabled": flag.is_enabled,
        "depends_on": flag.depends_on,
        "version": flag.version,
        "created_at": flag.created_at.isoformat(),
        "updated_at": flag.updated_at.isoformat()
    }

@api_router.patch("/feature-flags/{flag_id}")
async def update_feature_flag(flag_id: str, flag_data: FeatureFlagUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == uuid.UUID(flag_id)))
    flag = result.scalar_one_or_none()
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    old_values = {"is_enabled": flag.is_enabled, "enabled_countries": flag.enabled_countries}
    update_data = flag_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(flag, field, value)
    flag.version += 1
    flag.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(flag)
    
    await log_action(db, "UPDATE", "feature_flag", flag_id, user_id=current_user.id, user_email=current_user.email, old_values=old_values, new_values=update_data)
    
    return {
        "id": str(flag.id),
        "key": flag.key,
        "name": flag.name,
        "description": flag.description,
        "scope": flag.scope,
        "enabled_countries": flag.enabled_countries,
        "is_enabled": flag.is_enabled,
        "depends_on": flag.depends_on,
        "version": flag.version,
        "created_at": flag.created_at.isoformat(),
        "updated_at": flag.updated_at.isoformat()
    }

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
    flag.updated_at = datetime.now(timezone.utc)
    await db.commit()
    
    await log_action(db, "TOGGLE", "feature_flag", flag_id, user_id=current_user.id, user_email=current_user.email, old_values={"is_enabled": old_state}, new_values={"is_enabled": flag.is_enabled})
    return {"message": f"Feature flag {'enabled' if flag.is_enabled else 'disabled'}", "is_enabled": flag.is_enabled}

# Countries routes
@api_router.get("/countries")
async def get_countries(enabled_only: bool = False, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Country)
    if enabled_only:
        query = query.where(Country.is_enabled == True)
    query = query.order_by(Country.code)
    result = await db.execute(query)
    countries = result.scalars().all()
    
    return [{
        "id": str(c.id),
        "code": c.code,
        "name": c.name,
        "default_currency": c.default_currency,
        "default_language": c.default_language,
        "area_unit": c.area_unit,
        "distance_unit": c.distance_unit,
        "weight_unit": c.weight_unit,
        "date_format": c.date_format,
        "number_format": c.number_format,
        "support_email": c.support_email,
        "support_phone": c.support_phone,
        "is_enabled": c.is_enabled,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "updated_at": c.updated_at.isoformat() if c.updated_at else None
    } for c in countries]

@api_router.get("/countries/public")
async def get_public_countries(db: AsyncSession = Depends(get_db)):
    query = select(Country).where(Country.is_enabled == True).order_by(Country.code)
    result = await db.execute(query)
    countries = result.scalars().all()
    
    return [{
        "id": str(c.id),
        "code": c.code,
        "name": c.name,
        "default_currency": c.default_currency,
        "default_language": c.default_language,
        "is_enabled": c.is_enabled
    } for c in countries]

@api_router.get("/countries/{country_id}")
async def get_country(country_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Country).where(Country.id == uuid.UUID(country_id)))
    country = result.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return {
        "id": str(country.id),
        "code": country.code,
        "name": country.name,
        "default_currency": country.default_currency,
        "default_language": country.default_language,
        "area_unit": country.area_unit,
        "distance_unit": country.distance_unit,
        "weight_unit": country.weight_unit,
        "date_format": country.date_format,
        "number_format": country.number_format,
        "support_email": country.support_email,
        "is_enabled": country.is_enabled
    }

@api_router.get("/countries/code/{code}")
async def get_country_by_code(code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Country).where(Country.code == code.upper()))
    country = result.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return {
        "id": str(country.id),
        "code": country.code,
        "name": country.name,
        "default_currency": country.default_currency,
        "default_language": country.default_language,
        "is_enabled": country.is_enabled
    }

@api_router.post("/countries", status_code=201)
async def create_country(country_data: CountryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    result = await db.execute(select(Country).where(Country.code == country_data.code.upper()))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Country code already exists")
    
    country = Country(**country_data.model_dump())
    country.code = country.code.upper()
    db.add(country)
    await db.commit()
    await db.refresh(country)
    
    await log_action(db, "CREATE", "country", str(country.id), user_id=current_user.id, user_email=current_user.email, new_values={"code": country.code})
    
    return {
        "id": str(country.id),
        "code": country.code,
        "name": country.name,
        "default_currency": country.default_currency,
        "default_language": country.default_language,
        "is_enabled": country.is_enabled
    }

@api_router.patch("/countries/{country_id}")
async def update_country(country_id: str, country_data: CountryUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    result = await db.execute(select(Country).where(Country.id == uuid.UUID(country_id)))
    country = result.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    old_values = {"is_enabled": country.is_enabled}
    update_data = country_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(country, field, value)
    country.updated_at = datetime.now(timezone.utc)
    
    await db.commit()
    await db.refresh(country)
    
    await log_action(db, "UPDATE", "country", country_id, user_id=current_user.id, user_email=current_user.email, old_values=old_values, new_values=update_data, country_scope=country.code)
    
    return {
        "id": str(country.id),
        "code": country.code,
        "name": country.name,
        "default_currency": country.default_currency,
        "default_language": country.default_language,
        "is_enabled": country.is_enabled
    }

@api_router.delete("/countries/{country_id}")
async def delete_country(country_id: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin"]))):
    result = await db.execute(select(Country).where(Country.id == uuid.UUID(country_id)))
    country = result.scalar_one_or_none()
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    await log_action(db, "DELETE", "country", country_id, user_id=current_user.id, user_email=current_user.email, old_values={"code": country.code})
    await db.delete(country)
    await db.commit()
    return {"message": "Country deleted successfully"}

# Audit Logs routes
@api_router.get("/audit-logs")
async def get_audit_logs(skip: int = 0, limit: int = 50, action: Optional[str] = None, resource_type: Optional[str] = None, user_id: Optional[str] = None, country_scope: Optional[str] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(check_permissions(["super_admin", "country_admin", "finance"]))):
    query = select(AuditLog)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if user_id:
        query = query.where(AuditLog.user_id == uuid.UUID(user_id))
    if country_scope:
        query = query.where(AuditLog.country_scope == country_scope)
    
    query = query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return [{
        "id": str(log.id),
        "user_id": str(log.user_id) if log.user_id else None,
        "user_email": log.user_email,
        "action": log.action,
        "resource_type": log.resource_type,
        "resource_id": log.resource_id,
        "old_values": log.old_values,
        "new_values": log.new_values,
        "ip_address": log.ip_address,
        "country_scope": log.country_scope,
        "is_pii_scrubbed": log.is_pii_scrubbed,
        "created_at": log.created_at.isoformat() if log.created_at else None
    } for log in logs]

@api_router.get("/audit-logs/actions")
async def get_audit_actions(current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    return {"actions": ["CREATE", "UPDATE", "DELETE", "LOGIN", "LOGOUT", "TOGGLE", "SUSPEND", "ACTIVATE", "APPROVE", "REJECT"]}

@api_router.get("/audit-logs/resource-types")
async def get_resource_types(current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))):
    return {"resource_types": ["user", "feature_flag", "country", "category", "listing", "dealer", "invoice", "premium"]}

# Dashboard stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Users count
    users_result = await db.execute(select(func.count(User.id)))
    users_count = users_result.scalar()
    
    active_users_result = await db.execute(select(func.count(User.id)).where(User.is_active == True))
    active_users = active_users_result.scalar()
    
    # Countries count
    countries_result = await db.execute(select(func.count(Country.id)).where(Country.is_enabled == True))
    countries_count = countries_result.scalar()
    
    # Feature flags count
    flags_enabled_result = await db.execute(select(func.count(FeatureFlag.id)).where(FeatureFlag.is_enabled == True))
    flags_enabled = flags_enabled_result.scalar()
    
    flags_total_result = await db.execute(select(func.count(FeatureFlag.id)))
    flags_total = flags_total_result.scalar()
    
    # Users by role
    role_stats = {}
    for role in ["super_admin", "country_admin", "moderator", "support", "finance"]:
        role_result = await db.execute(select(func.count(User.id)).where(User.role == role))
        role_stats[role] = role_result.scalar()
    
    # Recent activity
    logs_result = await db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10))
    recent_logs = logs_result.scalars().all()
    
    return {
        "users": {"total": users_count, "active": active_users},
        "countries": {"enabled": countries_count},
        "feature_flags": {"enabled": flags_enabled, "total": flags_total},
        "users_by_role": role_stats,
        "recent_activity": [{
            "id": str(log.id),
            "action": log.action,
            "resource_type": log.resource_type,
            "user_email": log.user_email,
            "created_at": log.created_at.isoformat() if log.created_at else None
        } for log in recent_logs]
    }

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)
