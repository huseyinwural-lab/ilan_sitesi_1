# Multi-Country Admin Panel PRD (PostgreSQL)

## Original Problem Statement
Build a comprehensive Admin Panel for a multi-country classified ads platform targeting European markets (DE/CH/FR/AT). Modular architecture with Feature Flags, Category System, Attribute Engine, Menu Management, and GDPR compliance.

## Tech Stack (Final)
- **Backend**: Python FastAPI + PostgreSQL + SQLAlchemy + Alembic
- **Frontend**: React + TailwindCSS
- **Auth**: JWT + Refresh Tokens
- **Design**: Modern/Minimal, Blue (Primary) + Orange (Accent)

## User Personas
1. **Super Admin** - Full access to all features and countries
2. **Country Admin** - Manage specific countries
3. **Moderator** - Content moderation
4. **Support** - User support functions
5. **Finance** - Billing and invoice access

## What's Been Implemented (v1.0 - 2026-02-12)

### P0-0: MongoDB → PostgreSQL Migration ✅
- [x] SQLAlchemy ORM models
- [x] Alembic migration setup
- [x] All entity tables created
- [x] Seed data with env-based passwords

### P0-1: Category System ✅
- [x] N-level hierarchy with Materialized Path
- [x] Module association (real_estate, vehicle, etc.)
- [x] Country scope inheritance
- [x] Multi-language translations
- [x] Soft delete support

### P0-2: Attribute Engine ✅
- [x] Dynamic attribute types (text, number, select, etc.)
- [x] Options management for select fields
- [x] Category-attribute mapping
- [x] Filterable/Sortable flags
- [x] Unit support

### P0-3: Menu Management ✅
- [x] Top menu items with Feature Flag dependencies
- [x] Mega menu sections and links
- [x] Country scope filtering
- [x] Link types (category, pre_filtered, external)

### P0-4: Home Layout ✅
- [x] Per-country layout settings
- [x] Showcase/Vitrin management
- [x] Special listings
- [x] Ad slots (direct, adsense, header bidding)

### Core Features ✅
- [x] Auth (JWT + Refresh)
- [x] Users RBAC (5 roles)
- [x] Feature Flags (module + feature level)
- [x] Countries with locale settings
- [x] Audit Logs (immutable)
- [x] Dashboard with KPI stats

## Database Schema
- users, countries, feature_flags, audit_logs
- categories, category_translations
- attributes, attribute_options, category_attribute_map
- top_menu_items, top_menu_sections, top_menu_links
- home_layout_settings, home_showcase_items, home_special_listings, ad_slots

## Demo Credentials
- Super Admin: admin@platform.com / Admin123!
- Moderator: moderator@platform.de / Demo123!
- Finance: finance@platform.com / Demo123!
- Support: support@platform.ch / Demo123!

## Prioritized Backlog

### P1 - Business Features (Next)
- [ ] Dealer Management (başvuru onay/red)
- [ ] Premium Product Catalog
- [ ] Moderation Queue
- [ ] Tax/VAT Management (VAT rates per country)
- [ ] Invoice Core (net/tax/gross)

### P2 - Enhancements
- [ ] 2FA support
- [ ] User profile settings
- [ ] Category drag-drop reordering
- [ ] Attribute validation rules
- [ ] Advanced search/filtering
- [ ] Data export functionality

### V2 Features
- [ ] Stripe payment integration
- [ ] Elasticsearch for search
- [ ] Redis caching
- [ ] RabbitMQ for async tasks
