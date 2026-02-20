# Environment Variables Standard

Bu doküman preview ve prod ortamlarında **zorunlu** environment değişkenlerini tanımlar. Değerler **secret** olarak yönetilmelidir.

## Zorunlu Değişkenler

- **DATABASE_URL** (required)
  - Açıklama: Postgres bağlantı URL’si
  - Örnek: `postgresql://USER:PASSWORD@HOST:PORT/DBNAME`

- **DB_POOL_SIZE** (required)
  - Açıklama: Connection pool temel boyutu
  - Örnek: `5`

- **DB_MAX_OVERFLOW** (required)
  - Açıklama: Pool overflow limiti
  - Örnek: `5`

- **DB_SSL_MODE** (required)
  - Açıklama: SSL policy (preview için **require** zorunlu)
  - Kabul edilen değerler: `require`

## Politika Notları
- Preview ortamında **DB_SSL_MODE=require** zorunludur.
- DATABASE_URL yoksa uygulama **fail-fast** şekilde açılmamalıdır.
- Migration pipeline zorunludur; tablo oluşturma manuel yapılmaz.
