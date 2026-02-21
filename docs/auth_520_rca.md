# RCA — /api/auth/login 520

## Özet
Preview ortamında `/api/auth/login` **520** dönüyordu. Kaynak, backend’in DB bağlantısı kuramadığı için login endpointinin **500** üretmesi ve edge katmanda 520 olarak yüzeye çıkmasıydı.

## Belirti / Kanıt
- `backend.out.log`: `/api/auth/login` → **500 Internal Server Error**
- `backend.err.log`: `asyncpg` / `psycopg2` bağlantı hataları (localhost:5432)
- `/api/health`: `degraded` → DB bağlantısı başarısız

## Kök Neden
1) **Postgres servisinin çalışmaması** (localhost:5432 bağlantı reddi)
2) `.env.local` içinde **DATABASE_URL** yanlış kullanıcı/parola (`user:pass`)

## Düzeltmeler
- Postgres 15 kuruldu ve servis başlatıldı.
- `admin_user/admin_pass` role + `admin_panel` DB oluşturuldu.
- `.env.local` DATABASE_URL doğru değerle güncellendi.
- Backend yeniden başlatıldı.
- Alembic migrations başarıyla uygulandı (`upgrade heads`).

## Sonuç
- `/api/health` → **healthy**
- `/api/auth/login` → **200 OK** (token üretimi başarılı)

## Önleyici Aksiyon
- DB-ENV-GATE kuralı (preview/prod DATABASE_URL zorunluluğu)
- CI/CD deploy gate: DB bağlantısı + migration head eşleşmesi
