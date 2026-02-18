## Master Data → Search Entegrasyonu

### Public Filter Kaynakları
- **Categories:** `GET /api/categories?country=XX&module=vehicle`
- **Makes:** `GET /api/v1/vehicle/makes?country=XX`
- **Models:** `GET /api/v1/vehicle/models?make=slug&country=XX`

### Search Endpoint Filtreleri
- `GET /api/v2/search?country=XX&category=...&make=...&model=...`
- Sadece **active_flag=true** kayıtlar filtre seçeneklerinde görünür.

### Notlar
- Soft-delete edilen master data filtre seçeneklerinde görünmez.
- Country context zorunlu.
