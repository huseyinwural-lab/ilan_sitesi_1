# Pricing Test User Seed (Ops)

## Amaç
Pricing kampanya CRUD + checkout akışı için test kullanıcılarını oluşturmak veya sıfırlamak.

## Kullanıcılar
- **Bireysel:** pricing_individual@platform.com / Pricing123!
- **Kurumsal:** pricing_corporate@platform.com / Pricing123!

## Çalıştırma
```bash
cd /app/backend
set -a && source .env && set +a
python3 scripts/seed_pricing_test_user.py --reset
```

## Notlar
- `--reset` mevcut kullanıcıyı günceller ve şifreyi yeniler.
- Production ortamında çalıştırmayın (script engeller).
