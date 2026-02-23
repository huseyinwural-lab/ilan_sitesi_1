# P0 Scope Freeze — Premium Otomobil İlan Wizard

## Kapsam İçi
1) **Premium otomobil ilan UX (B hedefi)**
   - Marka odaklı görsel akış + hızlı seçim + minimum sürtünme
   - Segment‑aware çekirdek alanlar
2) **6/7 adımlı premium wizard standardı**
   - Kategori/Segment → Marka → Model → Yıl/Versiyon → Çekirdek Alanlar → Özellikler/Medya → Önizleme
   - Tamam→persist + Next gating
3) **Marka/Model görsel seçimi**
   - Logo’lu grid (placeholder), arama, popüler pin
4) **Yıl/Trim stratejisi**
   - Yıl zorunlu, trim dataset varsa opsiyonel
5) **Çekirdek alanlar sadeleştirme**
   - Fiyat (FIXED/HOURLY), Km, Yakıt, Vites, Çekiş, Kasa, Renk, Hasar/Takas, Konum
6) **Özellikler/Medya**
   - Attribute grupları + min foto + drag‑drop + kapak + EXIF temizleme
7) **SEO route**
   - /vasita/otomobil/{make}/{model} (+ opsiyonel year param)
8) **Performans**
   - Popülerler ilk yük + search + local cache
9) **E2E test kapsamı**
   - Marka→Model→Yıl gating, refresh/persist

## Kapsam Dışı (P2)
- HOURLY ayrı filtre
- Trim manuel giriş
