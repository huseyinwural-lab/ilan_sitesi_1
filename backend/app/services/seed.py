from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User, UserRole
from app.models.core import FeatureFlag, FeatureScope, Country
from app.core.security import get_password_hash

async def seed_default_data(db: AsyncSession):
    """Seed default data for the application"""
    
    # Seed Countries
    countries_data = [
        {
            "code": "DE",
            "name": {"tr": "Almanya", "de": "Deutschland", "fr": "Allemagne"},
            "default_currency": "EUR",
            "default_language": "de",
            "support_email": "support@platform.de",
            "is_enabled": True
        },
        {
            "code": "CH",
            "name": {"tr": "İsviçre", "de": "Schweiz", "fr": "Suisse"},
            "default_currency": "CHF",
            "default_language": "de",
            "support_email": "support@platform.ch",
            "is_enabled": True
        },
        {
            "code": "FR",
            "name": {"tr": "Fransa", "de": "Frankreich", "fr": "France"},
            "default_currency": "EUR",
            "default_language": "fr",
            "support_email": "support@platform.fr",
            "is_enabled": True
        },
        {
            "code": "AT",
            "name": {"tr": "Avusturya", "de": "Österreich", "fr": "Autriche"},
            "default_currency": "EUR",
            "default_language": "de",
            "support_email": "support@platform.at",
            "is_enabled": True
        }
    ]
    
    for country_data in countries_data:
        country = Country(**country_data)
        db.add(country)
    
    # Seed Feature Flags - Modules
    modules = [
        {"key": "real_estate", "name": {"tr": "Emlak", "de": "Immobilien", "fr": "Immobilier"}, "scope": FeatureScope.MODULE, "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"]},
        {"key": "vehicle", "name": {"tr": "Vasıta", "de": "Fahrzeuge", "fr": "Véhicules"}, "scope": FeatureScope.MODULE, "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"]},
        {"key": "machinery", "name": {"tr": "İş Makineleri", "de": "Baumaschinen", "fr": "Machines"}, "scope": FeatureScope.MODULE, "is_enabled": False, "enabled_countries": []},
        {"key": "services", "name": {"tr": "Hizmetler", "de": "Dienstleistungen", "fr": "Services"}, "scope": FeatureScope.MODULE, "is_enabled": False, "enabled_countries": []},
        {"key": "jobs", "name": {"tr": "İş İlanları", "de": "Stellenangebote", "fr": "Emplois"}, "scope": FeatureScope.MODULE, "is_enabled": False, "enabled_countries": []},
    ]
    
    # Seed Feature Flags - Features
    features = [
        {"key": "premium", "name": {"tr": "Premium", "de": "Premium", "fr": "Premium"}, "scope": FeatureScope.FEATURE, "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"]},
        {"key": "dealer", "name": {"tr": "Bayi", "de": "Händler", "fr": "Concessionnaire"}, "scope": FeatureScope.FEATURE, "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"]},
        {"key": "moderation", "name": {"tr": "Moderasyon", "de": "Moderation", "fr": "Modération"}, "scope": FeatureScope.FEATURE, "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"]},
        {"key": "messaging", "name": {"tr": "Mesajlaşma", "de": "Nachrichten", "fr": "Messagerie"}, "scope": FeatureScope.FEATURE, "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"]},
        {"key": "favorites", "name": {"tr": "Favoriler", "de": "Favoriten", "fr": "Favoris"}, "scope": FeatureScope.FEATURE, "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"]},
        {"key": "geo", "name": {"tr": "Konum", "de": "Standort", "fr": "Localisation"}, "scope": FeatureScope.FEATURE, "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"]},
        {"key": "gdpr", "name": {"tr": "GDPR", "de": "DSGVO", "fr": "RGPD"}, "scope": FeatureScope.FEATURE, "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"]},
        {"key": "tax", "name": {"tr": "Vergi", "de": "Steuer", "fr": "Taxe"}, "scope": FeatureScope.FEATURE, "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"]},
        {"key": "billing", "name": {"tr": "Faturalandırma", "de": "Abrechnung", "fr": "Facturation"}, "scope": FeatureScope.FEATURE, "is_enabled": True, "enabled_countries": ["DE", "CH", "FR", "AT"]},
    ]
    
    for flag_data in modules + features:
        flag = FeatureFlag(**flag_data)
        db.add(flag)
    
    # Seed Super Admin User
    admin_user = User(
        email="admin@platform.com",
        hashed_password=get_password_hash("Admin123!"),
        full_name="System Administrator",
        role=UserRole.SUPER_ADMIN,
        country_scope=["*"],
        is_active=True,
        is_verified=True,
        preferred_language="tr"
    )
    db.add(admin_user)
    
    # Seed Demo Users
    demo_users = [
        {"email": "moderator@platform.de", "full_name": "Hans Müller", "role": UserRole.MODERATOR, "country_scope": ["DE"], "preferred_language": "de"},
        {"email": "finance@platform.com", "full_name": "Marie Dupont", "role": UserRole.FINANCE, "country_scope": ["*"], "preferred_language": "fr"},
        {"email": "support@platform.ch", "full_name": "Peter Schmidt", "role": UserRole.SUPPORT, "country_scope": ["CH", "DE", "AT"], "preferred_language": "de"},
    ]
    
    for user_data in demo_users:
        user = User(
            **user_data,
            hashed_password=get_password_hash("Demo123!"),
            is_active=True,
            is_verified=True
        )
        db.add(user)
    
    await db.commit()
