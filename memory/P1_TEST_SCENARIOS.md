# P1 Test Senaryoları

## Drill-down (Genel “İlan Ver”)
1. **Modül seçimi → kategori sütunları**
   - /ilan-ver/kategori-secimi açılır
   - Modül seçimi yapılır, L1 sütunu yüklenir
   - L1 → L2 → L3 seçimleri ile leaf kategoriye ulaşılır
   - “Devam” butonu görünür ve /account/create/listing-wizard açılır

2. **Arama akışı**
   - Modül seçilmeden arama girişinin disabled olması
   - Modül seçildikten sonra arama sonuçlarının gelmesi
   - Arama sonucu seçimi ile path doldurulması ve leaf seçim kontrolü

3. **Modül değişimi**
   - Modül değiştirildiğinde önceki path ve seçimlerin sıfırlanması

4. **Analytics event’leri**
   - step_select_module
   - step_select_category_L1/L2/L3
   - Event payload: module, category_id, level, country

## Admin “Edit Kilidi Aç” (tasarım doğrulama)
1. **Yetki kontrolü**
   - super_admin ve country_admin erişebilir
   - Diğer roller erişemez (403)

2. **Edit mode + dirty zinciri**
   - Üst adım açılınca downstream adımlar dirty olur
   - Dirty adım yeniden tamamlanmadan “Tamamlandı” statüsüne dönemez

3. **Audit log**
   - Edit açan kullanıcı, değişen alanlar, dirty olan adımlar loglanır
