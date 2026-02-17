# ADMIN_IA_V2 — Bilgi Mimarisi (IA) + Navigasyon

## 1) Amaç
Admin Panel IA v2’nin amacı:
- Menü karmaşasını azaltmak
- Operasyonel görevleri 1–2 tıkla erişilebilir kılmak
- Country context (Global vs Country) karışıklığını bitirmek
- RBAC ile rol bazlı görünürlük standardını netleştirmek

## 2) IA v2 — Bölümler / Domain Grupları
Menü domain bazlı aşağıdaki gruplara ayrılır:
1. Dashboard
2. Genel Bakış
3. Kullanıcı & Satıcı
4. İlan & Moderasyon
5. Katalog & Yapılandırma
6. Master Data
7. Finans
8. Sistem

> Final sidebar ağacı için: `ADMIN_SIDEBAR_TREE_V2.md`

## 3) Sayfa Hiyerarşisi (Örnek)
- Dashboard
  - Dashboard (Ops Panel)
- Sistem
  - Ülkeler
    - Ülke Listesi
    - Ülke Detayı (drawer/modal)

## 4) Yetki Kapsamları (Rol Bazlı)
Aşağıdaki roller IA v2 seviyesinde temel alınır:

### Super Admin
- Tüm menüler ve tüm CRUD
- Global + Country mode kullanımı

### Admin (Country Admin / Ops Admin / Finance Admin gibi alt roller)
- Kendi kapsamına göre sınırlı domain erişimi
- Country mode’de CRUD (yetkisine göre)

### Moderator
- Moderation Queue
- Listings read-only (varsa)

> Detay RBAC kuralları: `ADMIN_RBAC_MENU_VISIBILITY.md`

## 5) Navigasyon Standartları
- Breadcrumb zorunlu
- Active state net
- Sidebar collapse (desktop)
- Global/Country context switcher header’da

> Detay kurallar: `ADMIN_NAVIGATION_CONSISTENCY_RULES.md`
