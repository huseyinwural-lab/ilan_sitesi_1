# P0 Kapsam Bildirimi — Admin Kategori Sihirbazı

## Scope Freeze (P0)
Bu P0 döngüsünde sadece aşağıdaki çıktılar teslim edilir; P1/P2 başlatılmaz.

### Kapsam İçi (P0)
1) **Kategori sihirbazı akış düzeltmesi** (ADR #432/#435)
   - Tamam → PATCH (her adımda server’a yazma)
   - Next gating + tooltip: “Önce bu adımı tamamlayın.”
   - Akış sırası: Kategori → Çekirdek Alanlar → Parametre Alanları (enforced)
2) **Backend authoritative state**
   - wizard_progress yalnızca server response ile güncellenir
3) **E2E test paketi** (Frontend + Backend)
4) **Preview DB env workaround dokümantasyonu**
   - Sadece preview’da backend/.env geçici kabul; prod/stage yasak

### Kapsam Dışı (P1/P2)
- “İlan ver / kategori seçimi”
- Public Search & Moderation Mongo→PostgreSQL göçü
- “Edit (kilidi aç)” akışı (P2 plan/teknik not)

## Kapanış Kriteri
- Tamam → PATCH çalışıyor, server response UI state’i belirliyor
- Next gating/tooltip doğru
- E2E PASS
- Preview workaround ops notu yayınlandı
