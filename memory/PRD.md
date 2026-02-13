# Multi-Country Admin Panel PRD (PostgreSQL)

## Original Problem Statement
Build a comprehensive Admin Panel for a multi-country classified ads platform targeting European markets (DE/CH/FR/AT/TR). Modular architecture with Feature Flags, Category System, Attribute Engine, Menu Management, Master Data Management (MDM), and GDPR compliance.

## Tech Stack (Final)
- **Backend**: Python FastAPI + PostgreSQL + SQLAlchemy + Alembic
- **Frontend**: React + TailwindCSS
- **Auth**: JWT + Refresh Tokens
- **Payments**: Stripe
- **Rate Limiting**: Redis
- **Design**: Modern/Minimal, Blue (Primary) + Orange (Accent)

## User Personas
1. **Super Admin** - Full access to all features and countries
2. **Country Admin** - Manage specific countries
3. **Moderator** - Content moderation
4. **Support** - User support functions
5. **Finance** - Billing and invoice access

## What's Been Implemented

### P0-P4: Core Infrastructure ✅
- [x] PostgreSQL + SQLAlchemy ORM + Alembic migrations
- [x] Category System (N-level hierarchy, Materialized Path)
- [x] Attribute Engine (dynamic types, options, category mappings)
- [x] Menu Management (feature flag dependencies)
- [x] Home Layout (per-country settings)
- [x] Auth (JWT + Refresh), RBAC (5 roles)
- [x] Feature Flags, Audit Logs, Countries

### P5: Scale Hardening ✅
- [x] Atomic transactions for subscriptions
- [x] DB constraints for data integrity
- [x] Expiry Job for subscriptions
- [x] Rate Limiting (Redis-based)

### P6: Deployment Preparation ✅
- [x] Dockerfile, render.yaml
- [x] Deployment documentation

### T2: Advanced Pricing Engine ✅
- [x] Database-driven "waterfall" pricing model
- [x] Dealer Packages & Subscriptions

### Domain Modeling (Completed 2026-02-13) ✅
- **Emlak (Real Estate)**: EU standard attributes (room_count as number, not "3+1")
- **Vasıta (Vehicle)**: Full MDM system (vehicle_makes, vehicle_models tables)
- **Alışveriş (Shopping)**: Attribute System v2 (typed columns: value_string, value_number, value_option_id)

### P7.0: Stabilization (Completed 2026-02-13) ✅
- [x] Structured JSON logging (structlog)
- [x] Correlation IDs (asgi-correlation-id)
- [x] Standardized error responses
- [x] Rate limiting guardrails
- [x] Parameter validation
- [x] **Query Plan Audit** - All queries using Index Scan (<5ms execution)
- [x] Database seeded with 10K+ listings

## Database Schema

### Core Tables
- users, countries, feature_flags, audit_logs
- categories, category_translations
- attributes, attribute_options, category_attribute_map

### MDM Tables (Vehicle)
- vehicle_makes: {id, slug, label_tr, label_de, label_fr, is_active}
- vehicle_models: {id, make_id, slug, labels, is_active}

### Attribute v2 Tables
- listing_attributes: {listing_id, attribute_id, value_string, value_number, value_boolean, value_date, value_option_id}

### Business Tables
- dealer_packages, dealer_subscriptions
- listings (with make_id, model_id FK to MDM)

## Key API Endpoints
- `GET /api/v2/search` - Performant search with typed attribute filtering
- `GET/PATCH /api/v1/admin/master-data/attributes` - Admin attribute management
- `GET /api/health` - Health check

## Demo Credentials
- Super Admin: admin@platform.com / admin

## Current Data (2026-02-13)
- **Listings**: 10,270
- **Categories**: 23 (Real Estate + Vehicle + Shopping)
- **Vehicle Makes**: 10 (BMW, Mercedes, VW, Audi, Tesla, etc.)
- **Vehicle Models**: 27
- **Attributes**: 57

## Prioritized Backlog

### P1 - P7.2: Admin UI Minimum Scope (Next)
- [ ] Admin UI for Attributes management
- [ ] Admin UI for Attribute Options management
- [ ] Admin UI for Vehicle Makes/Models management
- [ ] Wireframes at `/app/architecture/`

### P2 - P7.3: Public UI Search Integration
- [ ] Integrate Search API v2 into frontend
- [ ] Dynamic facets based on category

### P3 - Future
- [ ] Provider-Driven Master Data Sync (Vehicle data)
- [ ] Shopping vertical MDM (brands)
- [ ] ML-based abuse scoring
- [ ] Self-service analytics

## Performance Metrics
| Query | Execution Time | Status |
|-------|----------------|--------|
| Base Category Paging | 1.7ms | ✅ |
| Filter by Brand | 0.4ms | ✅ |
| Facet Aggregation | 2.0ms | ✅ |

Target: <150ms p95 | Achieved: <5ms
