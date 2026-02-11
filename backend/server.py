from fastapi import FastAPI, APIRouter
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict
from datetime import datetime, timezone
from enum import Enum
import uuid
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import timedelta

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Settings
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-super-secret-key-change-in-production-2024')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
SUPPORTED_COUNTRIES = ['DE', 'CH', 'FR', 'AT']
SUPPORTED_LANGUAGES = ['tr', 'de', 'fr']
COUNTRY_CURRENCIES = {'DE': 'EUR', 'FR': 'EUR', 'AT': 'EUR', 'CH': 'CHF'}

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

# Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2, max_length=255)
    role: UserRole = UserRole.SUPPORT
    country_scope: List[str] = Field(default_factory=list)
    preferred_language: str = "tr"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    country_scope: Optional[List[str]] = None
    preferred_language: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: UserRole
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
    scope: FeatureScope = FeatureScope.FEATURE
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

# Auth helpers
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise credentials_exception
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

def check_permissions(required_roles: list):
    async def permission_checker(current_user = Depends(get_current_user)):
        if current_user.get("role") not in required_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return permission_checker

# Audit helper
async def log_action(action: str, resource_type: str, resource_id: Optional[str] = None, 
                    user_id: Optional[str] = None, user_email: Optional[str] = None,
                    old_values: Optional[dict] = None, new_values: Optional[dict] = None,
                    ip_address: Optional[str] = None, country_scope: Optional[str] = None):
    audit_log = {
        "id": str(uuid.uuid4()),
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "user_id": user_id,
        "user_email": user_email,
        "old_values": old_values,
        "new_values": new_values,
        "ip_address": ip_address,
        "country_scope": country_scope,
        "is_pii_scrubbed": False,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.audit_logs.insert_one(audit_log)

# Create the main app
app = FastAPI(title="Admin Panel API", description="Multi-country Admin Panel", version="1.0.0")
api_router = APIRouter(prefix="/api")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting application...")
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id", unique=True)
    await db.feature_flags.create_index("key", unique=True)
    await db.feature_flags.create_index("id", unique=True)
    await db.countries.create_index("code", unique=True)
    await db.countries.create_index("id", unique=True)
    await db.audit_logs.create_index("id", unique=True)
    await db.audit_logs.create_index([("created_at", -1)])
    
    # Seed data if empty
    if await db.countries.count_documents({}) == 0:
        logger.info("Seeding default data...")
        await seed_default_data()
        logger.info("Default data seeded")

async def seed_default_data():
    # Countries
    countries = [
        {"id": str(uuid.uuid4()), "code": "DE", "name": {"tr": "Almanya", "de": "Deutschland", "fr": "Allemagne"}, "default_currency": "EUR", "default_language": "de", "area_unit": "m²", "distance_unit": "km", "weight_unit": "kg", "date_format": "DD.MM.YYYY", "number_format": "1.234,56", "support_email": "support@platform.de", "is_enabled": True, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "code": "CH", "name": {"tr": "İsviçre", "de": "Schweiz", "fr": "Suisse"}, "default_currency": "CHF", "default_language": "de", "area_unit": "m²", "distance_unit": "km", "weight_unit": "kg", "date_format": "DD.MM.YYYY", "number_format": "1'234.56", "support_email": "support@platform.ch", "is_enabled": True, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "code": "FR", "name": {"tr": "Fransa", "de": "Frankreich", "fr": "France"}, "default_currency": "EUR", "default_language": "fr", "area_unit": "m²", "distance_unit": "km", "weight_unit": "kg", "date_format": "DD/MM/YYYY", "number_format": "1 234,56", "support_email": "support@platform.fr", "is_enabled": True, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "code": "AT", "name": {"tr": "Avusturya", "de": "Österreich", "fr": "Autriche"}, "default_currency": "EUR", "default_language": "de", "area_unit": "m²", "distance_unit": "km", "weight_unit": "kg", "date_format": "DD.MM.YYYY", "number_format": "1.234,56", "support_email": "support@platform.at", "is_enabled": True, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
    ]
    await db.countries.insert_many(countries)
    
    # Feature Flags - Modules
    modules = [
        {"id": str(uuid.uuid4()), "key": "real_estate", "name": {"tr": "Emlak", "de": "Immobilien", "fr": "Immobilier"}, "description": {"tr": "Emlak ilanları modülü", "de": "Immobilienanzeigen Modul", "fr": "Module immobilier"}, "scope": "module", "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"], "depends_on": [], "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "key": "vehicle", "name": {"tr": "Vasıta", "de": "Fahrzeuge", "fr": "Véhicules"}, "description": {"tr": "Araç ilanları modülü", "de": "Fahrzeuganzeigen Modul", "fr": "Module véhicules"}, "scope": "module", "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"], "depends_on": [], "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "key": "machinery", "name": {"tr": "İş Makineleri", "de": "Baumaschinen", "fr": "Machines"}, "description": {"tr": "İş makineleri modülü", "de": "Baumaschinen Modul", "fr": "Module machines"}, "scope": "module", "is_enabled": False, "enabled_countries": [], "depends_on": [], "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "key": "services", "name": {"tr": "Hizmetler", "de": "Dienstleistungen", "fr": "Services"}, "description": {"tr": "Hizmet ilanları modülü", "de": "Dienstleistungen Modul", "fr": "Module services"}, "scope": "module", "is_enabled": False, "enabled_countries": [], "depends_on": [], "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "key": "jobs", "name": {"tr": "İş İlanları", "de": "Stellenangebote", "fr": "Emplois"}, "description": {"tr": "İş ilanları modülü", "de": "Stellenangebote Modul", "fr": "Module emplois"}, "scope": "module", "is_enabled": False, "enabled_countries": [], "depends_on": [], "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
    ]
    
    # Feature Flags - Features
    features = [
        {"id": str(uuid.uuid4()), "key": "premium", "name": {"tr": "Premium", "de": "Premium", "fr": "Premium"}, "description": {"tr": "Premium ilan özellikleri", "de": "Premium-Anzeigenfunktionen", "fr": "Fonctionnalités premium"}, "scope": "feature", "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"], "depends_on": [], "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "key": "dealer", "name": {"tr": "Bayi", "de": "Händler", "fr": "Concessionnaire"}, "description": {"tr": "Bayi hesap yönetimi", "de": "Händlerkontoverwaltung", "fr": "Gestion des comptes concessionnaires"}, "scope": "feature", "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"], "depends_on": [], "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "key": "moderation", "name": {"tr": "Moderasyon", "de": "Moderation", "fr": "Modération"}, "description": {"tr": "İlan moderasyon sistemi", "de": "Anzeigenmoderierungssystem", "fr": "Système de modération"}, "scope": "feature", "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"], "depends_on": [], "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "key": "messaging", "name": {"tr": "Mesajlaşma", "de": "Nachrichten", "fr": "Messagerie"}, "description": {"tr": "Kullanıcı mesajlaşma", "de": "Benutzernachrichten", "fr": "Messagerie utilisateur"}, "scope": "feature", "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"], "depends_on": [], "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "key": "favorites", "name": {"tr": "Favoriler", "de": "Favoriten", "fr": "Favoris"}, "description": {"tr": "İlan favorileme", "de": "Anzeigen-Favoriten", "fr": "Annonces favorites"}, "scope": "feature", "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"], "depends_on": [], "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "key": "gdpr", "name": {"tr": "GDPR", "de": "DSGVO", "fr": "RGPD"}, "description": {"tr": "GDPR uyumluluk araçları", "de": "DSGVO-Compliance-Tools", "fr": "Outils de conformité RGPD"}, "scope": "feature", "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"], "depends_on": [], "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "key": "tax", "name": {"tr": "Vergi", "de": "Steuer", "fr": "Taxe"}, "description": {"tr": "Vergi hesaplama motoru", "de": "Steuerberechnungsmodul", "fr": "Module de calcul des taxes"}, "scope": "feature", "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"], "depends_on": [], "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
        {"id": str(uuid.uuid4()), "key": "billing", "name": {"tr": "Faturalandırma", "de": "Abrechnung", "fr": "Facturation"}, "description": {"tr": "Fatura yönetimi", "de": "Rechnungsverwaltung", "fr": "Gestion des factures"}, "scope": "feature", "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"], "depends_on": ["tax"], "version": 1, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat()},
    ]
    await db.feature_flags.insert_many(modules + features)
    
    # Admin User
    admin = {
        "id": str(uuid.uuid4()),
        "email": "admin@platform.com",
        "hashed_password": get_password_hash("Admin123!"),
        "full_name": "System Administrator",
        "role": "super_admin",
        "country_scope": ["*"],
        "preferred_language": "tr",
        "is_active": True,
        "is_verified": True,
        "two_factor_enabled": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "last_login": None
    }
    await db.users.insert_one(admin)
    
    # Demo Users
    demo_users = [
        {"id": str(uuid.uuid4()), "email": "moderator@platform.de", "hashed_password": get_password_hash("Demo123!"), "full_name": "Hans Müller", "role": "moderator", "country_scope": ["DE"], "preferred_language": "de", "is_active": True, "is_verified": True, "two_factor_enabled": False, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat(), "last_login": None},
        {"id": str(uuid.uuid4()), "email": "finance@platform.com", "hashed_password": get_password_hash("Demo123!"), "full_name": "Marie Dupont", "role": "finance", "country_scope": ["*"], "preferred_language": "fr", "is_active": True, "is_verified": True, "two_factor_enabled": False, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat(), "last_login": None},
        {"id": str(uuid.uuid4()), "email": "support@platform.ch", "hashed_password": get_password_hash("Demo123!"), "full_name": "Peter Schmidt", "role": "support", "country_scope": ["CH", "DE", "AT"], "preferred_language": "de", "is_active": True, "is_verified": True, "two_factor_enabled": False, "created_at": datetime.now(timezone.utc).isoformat(), "updated_at": datetime.now(timezone.utc).isoformat(), "last_login": None},
    ]
    await db.users.insert_many(demo_users)

# Routes
@api_router.get("/")
async def root():
    return {"message": "Admin Panel API", "version": "1.0.0", "status": "healthy"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "supported_countries": SUPPORTED_COUNTRIES, "supported_languages": SUPPORTED_LANGUAGES}

# Auth routes
@api_router.post("/auth/register", response_model=UserResponse, status_code=201)
async def register(user_data: UserCreate):
    if await db.users.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = {
        "id": str(uuid.uuid4()),
        "email": user_data.email,
        "hashed_password": get_password_hash(user_data.password),
        "full_name": user_data.full_name,
        "role": user_data.role.value,
        "country_scope": user_data.country_scope,
        "preferred_language": user_data.preferred_language,
        "is_active": True,
        "is_verified": False,
        "two_factor_enabled": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "last_login": None
    }
    await db.users.insert_one(user)
    await log_action("CREATE", "user", user["id"], new_values={"email": user["email"], "role": user["role"]})
    
    return UserResponse(id=user["id"], email=user["email"], full_name=user["full_name"], role=user["role"], country_scope=user["country_scope"], preferred_language=user["preferred_language"], is_active=user["is_active"], is_verified=user["is_verified"], created_at=user["created_at"], last_login=user["last_login"])

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request):
    user = await db.users.find_one({"email": credentials.email})
    if not user or not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="User account is disabled")
    
    # Update last login
    await db.users.update_one({"id": user["id"]}, {"$set": {"last_login": datetime.now(timezone.utc).isoformat()}})
    
    token_data = {"sub": user["id"], "email": user["email"], "role": user["role"]}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    await log_action("LOGIN", "user", user["id"], user_id=user["id"], user_email=user["email"], ip_address=request.client.host if request.client else None)
    
    user_response = UserResponse(id=user["id"], email=user["email"], full_name=user["full_name"], role=user["role"], country_scope=user["country_scope"], preferred_language=user["preferred_language"], is_active=user["is_active"], is_verified=user["is_verified"], created_at=user["created_at"], last_login=user.get("last_login"))
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=user_response)

@api_router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    payload = decode_token(data.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user = await db.users.find_one({"id": payload.get("sub")})
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    token_data = {"sub": user["id"], "email": user["email"], "role": user["role"]}
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    user_response = UserResponse(id=user["id"], email=user["email"], full_name=user["full_name"], role=user["role"], country_scope=user["country_scope"], preferred_language=user["preferred_language"], is_active=user["is_active"], is_verified=user["is_verified"], created_at=user["created_at"], last_login=user.get("last_login"))
    return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    return UserResponse(id=current_user["id"], email=current_user["email"], full_name=current_user["full_name"], role=current_user["role"], country_scope=current_user["country_scope"], preferred_language=current_user["preferred_language"], is_active=current_user["is_active"], is_verified=current_user["is_verified"], created_at=current_user["created_at"], last_login=current_user.get("last_login"))

# Users routes
@api_router.get("/users", response_model=List[UserResponse])
async def get_users(skip: int = 0, limit: int = 50, role: Optional[str] = None, country: Optional[str] = None, search: Optional[str] = None, current_user = Depends(check_permissions(["super_admin", "country_admin"]))):
    query = {}
    if role:
        query["role"] = role
    if country:
        query["country_scope"] = {"$in": [country, "*"]}
    if search:
        query["$or"] = [{"email": {"$regex": search, "$options": "i"}}, {"full_name": {"$regex": search, "$options": "i"}}]
    
    users = await db.users.find(query, {"_id": 0, "hashed_password": 0}).skip(skip).limit(limit).sort("created_at", -1).to_list(limit)
    return [UserResponse(**u) for u in users]

@api_router.get("/users/count")
async def get_users_count(role: Optional[str] = None, country: Optional[str] = None, current_user = Depends(check_permissions(["super_admin", "country_admin"]))):
    query = {}
    if role:
        query["role"] = role
    if country:
        query["country_scope"] = {"$in": [country, "*"]}
    count = await db.users.count_documents(query)
    return {"count": count}

@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, current_user = Depends(check_permissions(["super_admin", "country_admin"]))):
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)

@api_router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, current_user = Depends(check_permissions(["super_admin"]))):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {k: v.value if hasattr(v, 'value') else v for k, v in user_data.model_dump(exclude_unset=True).items()}
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.users.update_one({"id": user_id}, {"$set": update_data})
        await log_action("UPDATE", "user", user_id, user_id=current_user["id"], user_email=current_user["email"], old_values={"role": user["role"]}, new_values=update_data)
    
    updated = await db.users.find_one({"id": user_id}, {"_id": 0, "hashed_password": 0})
    return UserResponse(**updated)

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user = Depends(check_permissions(["super_admin"]))):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await log_action("DELETE", "user", user_id, user_id=current_user["id"], user_email=current_user["email"], old_values={"email": user["email"]})
    await db.users.delete_one({"id": user_id})
    return {"message": "User deleted successfully"}

@api_router.post("/users/{user_id}/suspend")
async def suspend_user(user_id: str, current_user = Depends(check_permissions(["super_admin", "country_admin"]))):
    if user_id == current_user["id"]:
        raise HTTPException(status_code=400, detail="Cannot suspend yourself")
    result = await db.users.update_one({"id": user_id}, {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await log_action("SUSPEND", "user", user_id, user_id=current_user["id"], user_email=current_user["email"])
    return {"message": "User suspended successfully"}

@api_router.post("/users/{user_id}/activate")
async def activate_user(user_id: str, current_user = Depends(check_permissions(["super_admin", "country_admin"]))):
    result = await db.users.update_one({"id": user_id}, {"$set": {"is_active": True, "updated_at": datetime.now(timezone.utc).isoformat()}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await log_action("ACTIVATE", "user", user_id, user_id=current_user["id"], user_email=current_user["email"])
    return {"message": "User activated successfully"}

# Feature Flags routes
@api_router.get("/feature-flags")
async def get_feature_flags(scope: Optional[str] = None, country: Optional[str] = None, enabled_only: bool = False, current_user = Depends(get_current_user)):
    query = {}
    if scope:
        query["scope"] = scope
    if country:
        query["enabled_countries"] = {"$in": [country, "*"]}
    if enabled_only:
        query["is_enabled"] = True
    
    flags = await db.feature_flags.find(query, {"_id": 0}).sort([("scope", 1), ("key", 1)]).to_list(100)
    return flags

@api_router.get("/feature-flags/check/{key}")
async def check_feature_flag(key: str, country: Optional[str] = None):
    flag = await db.feature_flags.find_one({"key": key}, {"_id": 0})
    if not flag:
        return {"key": key, "enabled": False, "exists": False}
    is_enabled = flag.get("is_enabled", False)
    if country and is_enabled:
        enabled_countries = flag.get("enabled_countries", [])
        is_enabled = country in enabled_countries or "*" in enabled_countries
    return {"key": key, "enabled": is_enabled, "exists": True}

@api_router.get("/feature-flags/{flag_id}")
async def get_feature_flag(flag_id: str, current_user = Depends(get_current_user)):
    flag = await db.feature_flags.find_one({"id": flag_id}, {"_id": 0})
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    return flag

@api_router.post("/feature-flags", status_code=201)
async def create_feature_flag(flag_data: FeatureFlagCreate, current_user = Depends(check_permissions(["super_admin"]))):
    if await db.feature_flags.find_one({"key": flag_data.key}):
        raise HTTPException(status_code=400, detail="Feature flag key already exists")
    
    flag = {
        "id": str(uuid.uuid4()),
        **flag_data.model_dump(),
        "scope": flag_data.scope.value,
        "version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.feature_flags.insert_one(flag)
    await log_action("CREATE", "feature_flag", flag["id"], user_id=current_user["id"], user_email=current_user["email"], new_values={"key": flag["key"]})
    
    del flag["_id"]
    return flag

@api_router.patch("/feature-flags/{flag_id}")
async def update_feature_flag(flag_id: str, flag_data: FeatureFlagUpdate, current_user = Depends(check_permissions(["super_admin", "country_admin"]))):
    flag = await db.feature_flags.find_one({"id": flag_id})
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    update_data = flag_data.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        update_data["version"] = flag.get("version", 1) + 1
        await db.feature_flags.update_one({"id": flag_id}, {"$set": update_data})
        await log_action("UPDATE", "feature_flag", flag_id, user_id=current_user["id"], user_email=current_user["email"], old_values={"is_enabled": flag.get("is_enabled")}, new_values=update_data)
    
    updated = await db.feature_flags.find_one({"id": flag_id}, {"_id": 0})
    return updated

@api_router.delete("/feature-flags/{flag_id}")
async def delete_feature_flag(flag_id: str, current_user = Depends(check_permissions(["super_admin"]))):
    flag = await db.feature_flags.find_one({"id": flag_id})
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    await log_action("DELETE", "feature_flag", flag_id, user_id=current_user["id"], user_email=current_user["email"], old_values={"key": flag["key"]})
    await db.feature_flags.delete_one({"id": flag_id})
    return {"message": "Feature flag deleted successfully"}

@api_router.post("/feature-flags/{flag_id}/toggle")
async def toggle_feature_flag(flag_id: str, current_user = Depends(check_permissions(["super_admin", "country_admin"]))):
    flag = await db.feature_flags.find_one({"id": flag_id})
    if not flag:
        raise HTTPException(status_code=404, detail="Feature flag not found")
    
    new_state = not flag.get("is_enabled", False)
    await db.feature_flags.update_one({"id": flag_id}, {"$set": {"is_enabled": new_state, "version": flag.get("version", 1) + 1, "updated_at": datetime.now(timezone.utc).isoformat()}})
    await log_action("TOGGLE", "feature_flag", flag_id, user_id=current_user["id"], user_email=current_user["email"], old_values={"is_enabled": flag.get("is_enabled")}, new_values={"is_enabled": new_state})
    return {"message": f"Feature flag {'enabled' if new_state else 'disabled'}", "is_enabled": new_state}

# Countries routes
@api_router.get("/countries")
async def get_countries(enabled_only: bool = False, current_user = Depends(get_current_user)):
    query = {"is_enabled": True} if enabled_only else {}
    countries = await db.countries.find(query, {"_id": 0}).sort("code", 1).to_list(100)
    return countries

@api_router.get("/countries/public")
async def get_public_countries():
    countries = await db.countries.find({"is_enabled": True}, {"_id": 0}).sort("code", 1).to_list(100)
    return countries

@api_router.get("/countries/{country_id}")
async def get_country(country_id: str, current_user = Depends(get_current_user)):
    country = await db.countries.find_one({"id": country_id}, {"_id": 0})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country

@api_router.get("/countries/code/{code}")
async def get_country_by_code(code: str):
    country = await db.countries.find_one({"code": code.upper()}, {"_id": 0})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    return country

@api_router.post("/countries", status_code=201)
async def create_country(country_data: CountryCreate, current_user = Depends(check_permissions(["super_admin"]))):
    if await db.countries.find_one({"code": country_data.code.upper()}):
        raise HTTPException(status_code=400, detail="Country code already exists")
    
    country = {
        "id": str(uuid.uuid4()),
        **country_data.model_dump(),
        "code": country_data.code.upper(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    await db.countries.insert_one(country)
    await log_action("CREATE", "country", country["id"], user_id=current_user["id"], user_email=current_user["email"], new_values={"code": country["code"]})
    
    del country["_id"]
    return country

@api_router.patch("/countries/{country_id}")
async def update_country(country_id: str, country_data: CountryUpdate, current_user = Depends(check_permissions(["super_admin"]))):
    country = await db.countries.find_one({"id": country_id})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    
    update_data = country_data.model_dump(exclude_unset=True)
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.countries.update_one({"id": country_id}, {"$set": update_data})
        await log_action("UPDATE", "country", country_id, user_id=current_user["id"], user_email=current_user["email"], old_values={"is_enabled": country.get("is_enabled")}, new_values=update_data, country_scope=country["code"])
    
    updated = await db.countries.find_one({"id": country_id}, {"_id": 0})
    return updated

@api_router.delete("/countries/{country_id}")
async def delete_country(country_id: str, current_user = Depends(check_permissions(["super_admin"]))):
    country = await db.countries.find_one({"id": country_id})
    if not country:
        raise HTTPException(status_code=404, detail="Country not found")
    await log_action("DELETE", "country", country_id, user_id=current_user["id"], user_email=current_user["email"], old_values={"code": country["code"]})
    await db.countries.delete_one({"id": country_id})
    return {"message": "Country deleted successfully"}

# Audit Logs routes
@api_router.get("/audit-logs")
async def get_audit_logs(skip: int = 0, limit: int = 50, action: Optional[str] = None, resource_type: Optional[str] = None, user_id: Optional[str] = None, country_scope: Optional[str] = None, current_user = Depends(check_permissions(["super_admin", "country_admin", "finance"]))):
    query = {}
    if action:
        query["action"] = action
    if resource_type:
        query["resource_type"] = resource_type
    if user_id:
        query["user_id"] = user_id
    if country_scope:
        query["country_scope"] = country_scope
    
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return logs

@api_router.get("/audit-logs/actions")
async def get_audit_actions(current_user = Depends(check_permissions(["super_admin", "country_admin"]))):
    return {"actions": ["CREATE", "UPDATE", "DELETE", "LOGIN", "LOGOUT", "TOGGLE", "SUSPEND", "ACTIVATE", "APPROVE", "REJECT"]}

@api_router.get("/audit-logs/resource-types")
async def get_resource_types(current_user = Depends(check_permissions(["super_admin", "country_admin"]))):
    return {"resource_types": ["user", "feature_flag", "country", "category", "listing", "dealer", "invoice", "premium"]}

# Dashboard stats
@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user = Depends(get_current_user)):
    users_count = await db.users.count_documents({})
    active_users = await db.users.count_documents({"is_active": True})
    countries_count = await db.countries.count_documents({"is_enabled": True})
    flags_enabled = await db.feature_flags.count_documents({"is_enabled": True})
    flags_total = await db.feature_flags.count_documents({})
    
    # Recent activity
    recent_logs = await db.audit_logs.find({}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    
    # Users by role
    role_stats = {}
    for role in ["super_admin", "country_admin", "moderator", "support", "finance"]:
        role_stats[role] = await db.users.count_documents({"role": role})
    
    return {
        "users": {"total": users_count, "active": active_users},
        "countries": {"enabled": countries_count},
        "feature_flags": {"enabled": flags_enabled, "total": flags_total},
        "users_by_role": role_stats,
        "recent_activity": recent_logs
    }

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
