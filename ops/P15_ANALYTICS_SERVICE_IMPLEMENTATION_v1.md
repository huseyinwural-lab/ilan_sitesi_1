# P15 Analytics Service Implementation (v1)

**Amaç:** View Tracking Policy'nin kod karşılığı.

## 1. Servis Yapısı (`app/services/analytics_service.py`)

### Metodlar
*   `track_view(listing_id: str, request: Request, user_id: Optional[str])`
*   `_is_bot(user_agent: str) -> bool`
*   `_is_duplicate(listing_id, ip_hash) -> bool`

## 2. Bot Filtre Listesi
Aşağıdaki keyword'ler User-Agent stringinde aranır (Case-insensitive):
*   `bot`, `crawler`, `spider`, `googlebot`, `bingbot`, `slurp`, `duckduckgo`
*   `facebookexternalhit`, `twitterbot`
*   `curl`, `wget`, `python-requests`, `postman`
*   `headlesschrome`, `phantomjs`

## 3. Concurrency
*   `view_count` artırımı `listings` tablosunda `update(Listing).where(id=...).values(view_count=Listing.view_count + 1)` şeklinde atomic yapılmalıdır.
*   `listing_views` insert işlemi aynı transaction içinde olmalıdır.

## 4. Cache Invalidation
*   Eğer `Listing` detay endpoint'i cache'leniyorsa (Redis), view count değişimi cache'i geçersiz kılmamalıdır (veya sadece count ayrı bir endpointten alınmalıdır).
*   **Karar:** `view_count` dashboard'da gösterildiği için listing detail response'unda güncel olmalıdır. Ancak yüksek trafikli sitelerde view count genellikle "eventual consistent" olur.
*   **MVP:** Detail endpoint cache'i varsa temizle (TTL kısa tutulur).
