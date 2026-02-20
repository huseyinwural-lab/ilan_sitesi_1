from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dotenv import load_dotenv
load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models
from app.models import Base
from app.models.user import User
from app.models.user import User, SignupAllowlist
from app.models.core import Country, FeatureFlag, AuditLog
from app.models.category import Category, CategoryTranslation
from app.models.attribute import Attribute, AttributeOption, CategoryAttributeMap
from app.models.menu import TopMenuItem, TopMenuSection, TopMenuLink
from app.models.home import HomeLayoutSettings, HomeShowcaseItem, HomeSpecialListing, AdSlot

from app.models.commercial import DealerPackage, DealerSubscription
from app.models.pricing import PriceConfig, FreeQuotaConfig, Discount, ListingConsumptionLog, CountryCurrencyMap
from app.models.payment import StripeSettings, PaymentAttempt, Refund
from app.models.dealer import DealerApplication, Dealer, DealerUser
from app.models.premium import PremiumProduct, ListingPromotion, PremiumRankingRule
from app.models.moderation import Listing, ModerationAction, ModerationRule
from app.models.billing import VatRate, Invoice, InvoiceItem, StripeEvent, BillingCustomer, StripeSubscription
from app.models.vehicle_mdm import VehicleMake, VehicleModel
from app.models.monetization import SubscriptionPlan, UserSubscription, QuotaUsage
from app.models.promotion import Promotion, Coupon, CouponRedemption

from app.models.referral import ReferralReward, ConversionEvent
from app.models.analytics import ListingView
from app.models.ledger import RewardLedger
from app.models.referral_tier import ReferralTier
from app.models.affiliate import Affiliate, AffiliateClick
target_metadata = Base.metadata
from app.models.blog import BlogPost
from app.models.growth import GrowthEvent
from app.models.application import Application

def get_url():
    return os.environ.get("DATABASE_URL", "postgresql://admin_user:admin_pass@localhost:5432/admin_panel")

def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
