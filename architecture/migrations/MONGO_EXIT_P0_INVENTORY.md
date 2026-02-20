# Mongo Exit Inventory (P0)

## Amaç
Auth + Applications modüllerinin Mongo bağımlılığını kaldırmak için kullanılan Mongo erişim noktalarını ve koleksiyonları listeler.

## Mongo Bağlantı Noktaları
- **Client init**: `app/mongo.py` (`get_mongo_client`, `get_db_name`)
- **Dependency**: `app/dependencies.py` (`get_mongo_db`, `get_current_user`)
- **Runtime**: `server.py` `request.app.state.db`

## Koleksiyon / Modül Envanteri (P0 odaklı)
### Auth / Users
- **users**: login/register/me, admin users, seed kullanıcıları
- **admin_invites**: admin invite akışları
- **audit_logs**: auth/role değişimi logları

### Applications (Support)
- **support_applications** (legacy): P0’da tamamen kaldırılacak
- **notifications**: in-app “Başvurunuz alındı” mesajları

## Diğer Mongo Kullanımları (P1+)
- **categories**, **attributes**, **menu_top_items**
- **vehicle_listings**, **reports**
- **countries**, **system_settings**
- **plans**, **invoices**, **tax_rates**
- **moderation queue** (listings/flags)
- **messaging** (P2)

## Code References
- `backend/server.py` → Mongo CRUD (auth/users, applications, listings, reports, invoices)
- `backend/app/dependencies.py` → auth context
- `backend/app/mongo.py` → client config

## Aksiyon
- P0’da **auth/users + applications** Mongo erişimleri kapatılacak.
- P1/P2’de moderation ve messaging Mongo erişimleri kaldırılacak.
