# PORTAL_BOUNDARY_V1

## Portal Tanımı & Route Prefix
- **Public:** `/` (genel içerik, login gerektirmez)
- **Consumer (Bireysel):** `/account/*`
- **Dealer (Kurumsal):** `/dealer/*`
- **Admin (Sistem):** `/admin/*`

## Layout Ayrımı
- **PublicLayout:** Public sayfalar (Home, Search, Listing Detail)
- **AccountLayout:** Bireysel panel (turuncu tema, ayrı sidebar/header)
- **DealerLayout:** Kurumsal panel (dealer menüleri, ayrı sidebar/header)
- **AdminLayout:** Sistem paneli (admin menüleri, ayrı sidebar/header)

## Login Yüzeyleri
- Public login: `/login`
- Consumer login: `/login` (başarılı login sonrası `/account`)
- Dealer login: `/dealer/login`
- Admin login: `/admin/login`

## Portal Scope
- ADMIN → `admin`
- DEALER → `dealer`
- USER/INDIVIDUAL → `account`

## Paylaşılan UI Bileşenleri (Ortak)
- Button, Modal, Table, Badge, Input, Select
- Empty/Loading/Error state bileşenleri

## Design Token (Consumer)
- `consumer_primary_color = orange`
