import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
load_dotenv(ROOT_DIR / '.env')

class Settings:
    APP_ENV: str = os.environ.get('APP_ENV', 'dev').lower()
    DATABASE_URL: str = os.environ.get('DATABASE_URL', 'postgresql://admin_user:admin_pass@localhost:5432/admin_panel')
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
if settings.APP_ENV == "prod" and not os.environ.get("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL must be set in prod")
