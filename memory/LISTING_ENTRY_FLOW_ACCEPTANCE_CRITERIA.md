# Listing Entry Flow Acceptance Criteria

**Son güncelleme:** 2026-02-23

Bu doküman `/ilan-ver/kategori-secimi` akışı için kabul kriterlerini kilitler.

---

## Referans Akış (5 görsel)
1) **Modül kartları** (Emlak/Vasıta/...)
2) **L1 liste**
3) **L2/L3 drill-down**
4) **Alt tip seçimi paneli**

**Seçim bitince:** otomatik **Çekirdek Alanlar** adımına geçiş.

---

## Tamamlanma Kriterleri (kilitli)
- **Modül seçimi:** Bir modül kartı seçilmeden L1 listesi açılmaz.
- **L1 seçimi:** L1 seçilmeden L2/L3 listesi aktifleşmez.
- **L2/L3 seçimi:** Drill-down tamamlanmadan alt tip paneli aktifleşmez.
- **Alt tip seçimi:** Alt tip seçilmeden “Devam/İleri” **pasif**.

---

## UI Davranış Kilidi
- **İleri butonu:** kategori tamamlanmadan pasif.
- **URL temsil:** her drill-down adımı URL query ile temsil edilir.
- **Geri tuşu:** state kaybı olmadan bir önceki adıma döner.
- **Otomatik geçiş:** alt tip seçimi tamamlanınca çekirdek alanlara yönlenir.

---

## Doğrulama Checklist’i
1) **UI route eşleşmesi**
   - `/ilan-ver/kategori-secimi?module=...&path=...`
   - URL path değiştikçe UI aynı state’e hydrate olur.

2) **Buton aktiflik koşulları**
   - Devam butonu yalnızca alt tip seçimi tamamlandığında aktif.

3) **Stepper/Seçim durumu**
   - Breadcrumb her adımda güncellenir.
   - Modül seçimi → L1 → L2/L3 → Alt tip sırası bozulmaz.

4) **Geri/İleri davranışı**
   - Browser back ile önceki step’e dönünce seçimler korunur.

---

## Referans Ekran Uyum Testi (zorunlu)
**Senaryo:**
1. `/ilan-ver/kategori-secimi` açılır.
2. Modül kartı seçilir (örn. Emlak).
3. L1 listeden bir kategori seçilir (örn. Konut).
4. L2/L3 drill-down üzerinden seçim devam eder.
5. Alt tip panelinde (Satılık/Kiralık/Günlük) seçim yapılır.
6. Sistem otomatik olarak **Çekirdek Alanlar** adımına yönlenir.

**Kabul kriteri:** Bu senaryo **PASS** olmadan değişiklik tamamlanmış sayılmaz.
