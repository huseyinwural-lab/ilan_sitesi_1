# Dealer Listings Bulk Actions Evidence (FAZ-DL2)

Tarih: 2026-02-21

## Kapsam
- Dealer Listings ekranında bulk seçim (checkbox + select-all) ve aksiyon barı (archive / soft delete / restore)
- Varsayılan filtre: status=active, sıralama: created_at desc
- Bulk işlem sonrası otomatik refresh + toast mesajları
- Restore yalnızca archived → active geçişine izinli

## API Güncellemeleri
- GET /api/dealer/listings?status=active|draft|archived|all
- POST /api/dealer/listings/bulk
  - request: { ids: [..], action: archive|delete|restore }
  - response: { updated, deleted, failed }

## UI Kanıtı
- Toolbar: filtre + seçili sayaç + bulk aksiyon butonları
- Table: select-all + satır checkbox'ları

## Test Notu
- Preview ortamında /api/auth/login çağrısı 520 döndüğü için uçtan uca test tamamlanamadı.
- UI doğrulaması için login denemesi yapıldı; backend hata nedeniyle giriş başarısız.
