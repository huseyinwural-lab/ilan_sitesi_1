# P14 Admin Authz Policy - Promotion (v1)

**Amaç:** Kampanya yönetiminde rol tabanlı erişim kontrolünü (RBAC) netleştirmek.

## Rol Matrisi

| Rol | Erişim Seviyesi | İzin verilen İşlemler |
| :--- | :--- | :--- |
| **Super Admin** | `Full Access` | Create, Update, Deactivate, Generate Coupons, View Redemptions |
| **Country Admin** | `Restricted Write` | Kendi ülkesi/para birimi için (Şimdilik Global yetki varsayımı ile Super Admin ile aynı veya kısıtlı) |
| **Finance** | `Read Only` | View Promotions, View Redemptions, Export Reports |
| **Support (Ops)** | `Read Only` | View Promotions, Check Coupon Status (Debug) |
| **Moderator** | `No Access` | Erişim yok |

## Uygulama Kuralı
Backend endpointlerinde `check_permissions` dependency'si şu şekilde kullanılacak:

*   **Write Endpoints:** `check_permissions(["super_admin"])` (MVP'de sadece Super Admin)
*   **Read Endpoints:** `check_permissions(["super_admin", "finance", "support"])`

## Ops Read Rolü
Destek ekibinin "Kuponum çalışmıyor" şikayetlerini inceleyebilmesi için `support` rolüne `GET` yetkileri tanımlanmıştır.
