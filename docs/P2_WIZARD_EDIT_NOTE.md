# P2 Notu — Kategori Sihirbazı Edit (Kilidi Aç)

## Amaç
Tamamlanan adımı tekrar düzenlemek için kontrollü bir “Edit” akışı.

## Önerilen Teknik Yaklaşım (P0 sonrası)
- Edit tıklandığında **PATCH**: `wizard_progress.state = draft` ve ilgili adımın kilidi açılır.
- `expected_updated_at` ile eşzamanlılık (optimistic lock) korunur.
- Edit sonrası **Next** disabled; kullanıcı “Tamam” ile yeniden server’a yazar.
- UI state sadece PATCH response üzerinden güncellenir (backend authoritative).

## Notlar
- Edit sırasında hiyerarşi değişirse alt adımlar otomatik “draft”a döner.
- Gerekirse `wizard_progress.last_completed_step` gibi alan eklenebilir.
