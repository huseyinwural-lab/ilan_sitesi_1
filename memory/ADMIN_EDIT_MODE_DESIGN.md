# Admin Kategori Sihirbazı — Edit Kilidi Aç Tasarımı (P1)

## Yetki
- **super_admin** ve **country_admin** rolleri açabilir.
- Diğer roller için 403 (UI’da buton görünmez).

## Akış
1. Tamamlanmış adım kartında “Edit (Kilidi Aç)” butonu görünür.
2. Edit moduna girildiğinde:
   - Seçilen adım **editable** olur.
   - Bu adımdan sonraki tüm adımlar **dirty** olur (yeniden tamamlanma zorunlu).
3. Kullanıcı değişiklikleri kaydeder.
4. Dirty adımlar yeniden “Tamamlandı” yapılmadan üst adım kilitlenmez.

## Dirty Kuralı
- Upstream değişiklik varsa downstream adımların `wizard_progress` işaretleri temizlenir.
- Dirty adım = validation + “Tamam” zorunlu.

## Audit Log
- event_type: `categories.wizard.unlock`
- metadata: { category_id, unlocked_step, dirty_steps[], changed_fields[], actor_role }

## UI Notları
- Dirty adımlar görsel olarak uyarı etiketi alır (örn: “Tekrar Tamamla”).
- Edit modu aktifken kaydetme sonrası “Yeniden Tamamla” CTA görünür.
