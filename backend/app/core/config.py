import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')
load_dotenv(ROOT_DIR / '.env.local', override=False)

class Settings:
    APP_ENV: str = os.environ.get('APP_ENV', 'dev').lower()
    DATABASE_URL: str = os.environ.get('DATABASE_URL')
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'change-this-in-production')
    ALGORITHM: str = os.environ.get('ALGORITHM', 'HS256')
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', 30))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.environ.get('REFRESH_TOKEN_EXPIRE_DAYS', 7))
    CORS_ORIGINS: str = os.environ.get('CORS_ORIGINS', '*')
    
    # Multi-language support
    SUPPORTED_LANGUAGES = ['tr', 'de', 'fr']
    DEFAULT_LANGUAGE = 'tr'
    
    # Multi-country support
    SUPPORTED_COUNTRIES = ['DE', 'CH', 'FR', 'AT']
    DEFAULT_COUNTRY = 'DE'
    
    # Currency mapping
    COUNTRY_CURRENCIES = {
        'DE': 'EUR',
        'FR': 'EUR',
        'AT': 'EUR',
        'CH': 'CHF'
    }

settings = Settings()
if settings.APP_ENV in {"preview", "prod"}:
    if not settings.DATABASE_URL:
        raise RuntimeError("CONFIG_MISSING: DATABASE_URL")
    lowered_url = settings.DATABASE_URL.lower()
    if "localhost" in lowered_url or "127.0.0.1" in lowered_url:
        raise RuntimeError("CONFIG_MISSING: DATABASE_URL")

if settings.APP_ENV == "prod" and not os.environ.get("DATABASE_URL"):
    raise RuntimeError("CONFIG_MISSING: DATABASE_URL")
