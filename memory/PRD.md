# FAZ EU Panel — Ürün Gereksinimleri
**Son güncelleme:** 2026-03-01 11:12:00 UTC (L0/L1 alfabetik sıralama modu + kardeş onayı kaldırıldı)

## Orijinal Problem
Avrupa odaklı ilan platformu için full-stack (React + FastAPI + PostgreSQL) bir sistem isteniyor. Yönetici panelinde kategori hiyerarşisi, ilan oluşturma akışı ve vitrin/doping yönetimi; public tarafta ise kategori + vitrin listeleri ve ilan verme akışı uçtan uca çalışmalı.

## Kullanıcı Personaları
- **Admin (Backoffice)**
- **Consumer (Bireysel)**
- **Dealer (Kurumsal)**

## Temel Gereksinimler
- Kategori yönetimi: modül bazlı, çok seviyeli (Level 0/1/2/...) hiyerarşi
- İlan verme: kategori seçimi → detaylar → önizleme → doping → moderasyon
- Vitrin/Acil: admin ayarı ve public render entegrasyonu
- Güvenlik: RBAC, 2FA (TOTP), audit log

## Mimari
- **Frontend:** React (Account/Dealer/Admin portal)
- **Backend:** FastAPI (server.py monolith + SQLAlchemy)
- **Database:** PostgreSQL (DATABASE_URL)
- **Mongo:** EU panel sprintlerinde devre dışı (MONGO_ENABLED=false)

## Önemli Veri Modelleri (Özet)
- **Category:** id, name, slug, parent_id, module, sort_order, active_flag, image_url, form_schema
- **Listing:** id, category_id, status, doping_type, published_at, featured_until, urgent_until

## 3rd Party Entegrasyonlar
- Meilisearch
- Stripe
- (Planlanan) Slack / SMTP / PagerDuty

## Dokümantasyon
- `/app/memory/CHANGELOG.md`
- `/app/memory/ROADMAP.md`
