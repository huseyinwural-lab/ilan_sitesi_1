# Multi-Country Admin Panel PRD

## Original Problem Statement
Build a comprehensive Admin Panel for a multi-country classified ads platform targeting European markets (DE/CH/FR/AT). Features include Feature Flags, Multi-Country management, RBAC, Audit Logs, and more.

## Tech Stack
- **Backend**: Python FastAPI + MongoDB
- **Frontend**: React + TailwindCSS
- **Auth**: JWT + Refresh Tokens
- **Design**: Modern/Minimal, Blue (Primary) + Orange (Accent)

## User Personas
1. **Super Admin** - Full access to all features and countries
2. **Country Admin** - Manage specific countries
3. **Moderator** - Content moderation
4. **Support** - User support functions
5. **Finance** - Billing and invoice access

## Core Requirements (Static)
- Multi-country support (DE/CH/FR/AT)
- Multi-language (TR/DE/FR)
- Feature Flags (module + feature level)
- RBAC with 5 roles
- Audit logging (GDPR compliant)
- JWT authentication

## What's Been Implemented (v1.0 - 2026-02-11)
### Backend (FastAPI + MongoDB)
- [x] Auth routes (login, register, refresh, me)
- [x] Users CRUD + suspend/activate
- [x] Feature Flags CRUD + toggle
- [x] Countries CRUD + locale settings
- [x] Audit Logs with filtering
- [x] Dashboard stats endpoint
- [x] Auto-seed data on startup

### Frontend (React + TailwindCSS)
- [x] Login page with i18n
- [x] Dashboard with KPI cards, role distribution, recent activity
- [x] Users management table
- [x] Feature Flags with toggle cards
- [x] Countries management cards
- [x] Audit Logs with pagination
- [x] Sidebar + Topbar layout
- [x] Country selector, Language selector, Theme toggle
- [x] Responsive design

## Prioritized Backlog

### P0 - Next Phase (Core Business)
- [ ] Category System (N-level with Materialized Path)
- [ ] Attribute Engine (dynamic form fields)
- [ ] Top Menu / Mega Menu management
- [ ] Home Layout Manager (Vitrin/Özel İlan/Reklam)

### P1 - Business Features
- [ ] Dealer Management (başvuru onay/red)
- [ ] Premium Product Catalog
- [ ] Moderation Queue
- [ ] Tax/VAT Management
- [ ] Invoice Core

### P2 - Enhancements
- [ ] 2FA support
- [ ] User profile settings
- [ ] Advanced search/filtering
- [ ] Export functionality

## Demo Credentials
- Super Admin: admin@platform.com / Admin123!
- Moderator: moderator@platform.de / Demo123!
- Finance: finance@platform.com / Demo123!
- Support: support@platform.ch / Demo123!
