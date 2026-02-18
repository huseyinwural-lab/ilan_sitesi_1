## Admin Menü RBAC Matrisi (v2)

| Menü / Rol | super_admin | country_admin | moderator | finance | support |
| --- | --- | --- | --- | --- | --- |
| Dashboard | ✅ | ✅ | ❌ | ✅ | ❌ |
| Yönetim (admin users/roles/rbac) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Kullanıcı Yönetimi / Üyeler | ✅ | ✅ | ❌ | ❌ | ✅ |
| İlan & Moderasyon | ✅ | ✅ | ✅ | ❌ | ✅ (Şikayetler) |
| Katalog & İçerik (Kategoriler) | ✅ | ✅ | ✅ | ❌ | ❌ |
| Katalog & İçerik (Özellikler) | ✅ | ✅ | ❌ | ❌ | ❌ |
| Araç Verisi | ✅ | ✅ | ❌ | ❌ | ❌ |
| Finans | ✅ | ❌ | ❌ | ✅ | ❌ |
| Sistem | ✅ | ✅ | ❌ | ❌ | ❌ |

Not: country_admin tüm domainlere country-scope ile erişir; admin kullanıcı/rol yönetimi sadece super_admin’dadır.
