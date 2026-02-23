# Admin Category Wizard — Edit Mode State Sync (P0)

## Repro Senaryosu
1. Admin olarak **/admin/categories** sayfasına gir.
2. Tamamlanmış bir kategori için **Düzenle** aç.
3. Üst adım (örn. **Çekirdek Alanlar**) için **Edit** butonuna tıkla.
4. Bir alan değiştir, ardından **Tamam** ile kaydet.
5. Beklenen: downstream adımlar (**Parametre**, **Detay**, **Modüller**, **Önizleme**) “dirty” işareti almalı.
6. Hata: UI dirty işaretlerini göstermiyor veya eski state’e geri dönüyor.

## UI State Kaynakları (Mevcut)
- **Local State (useState):**
  - `wizardProgress` (wizard_progress), `editing`, `form`, `schema`, `hierarchyComplete`, `subcategories`, `levelSelections`, `levelCompletion`, `previewComplete`
- **Derived State:**
  - `dirtySteps`, `isStepDirty`, `isStepCompleted`, `publishValidation`, `autosaveSnapshot`
- **Server State:**
  - `/api/admin/categories` ve `/api/admin/categories/{id}` yanıtları (authoritative wizard_progress)

## Tek Kaynak Kararı (ADR-P0-EDITFIX-002)
- **Wizard step durumları (dirty/completed/locked)** için **tek kaynak backend `wizard_progress`**.
- UI yalnızca backend response’tan gelen `wizard_progress` ile render edilir.
- Local hesap/optimistic update yalnızca request göndermek için (payload) kullanılır; render’da authoritative response esas alınır.

## Kök Neden (İzole)
- Aynı isimli **`handleHierarchyEdit`** fonksiyonunun iki kez tanımlanması -> unlock akışı yerine reset akışı çalışıyor, dirty chain kayboluyor.
- Wizard state’in **birden fazla noktadan local set edilmesi** (optimistic) -> stale UI ve drift.

## Düzeltme Yaklaşımı
- `applyCategoryFromServer` ile **server response tek seferde** UI store’a yazıldı.
- `normalizeWizardProgress` ile response tek formatta işlendi.
- Save/Unlock başarısız olursa `restoreSnapshot` ile state rollback.
