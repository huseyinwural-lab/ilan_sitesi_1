# FAZ-U5.1: Emlak Kategori Mimarisi (AB Uyumlu)

## 1. Hiyerarşi Stratejisi
**Materialized Path** yapısı kullanılacak. Derinlik: 4 Seviye.

### Yapı
*   **Level 1 (Modül)**: Emlak
*   **Level 2 (Segment)**: Konut, Ticari, Günlük Kiralık, Arsa, Projeler
*   **Level 3 (İşlem Tipi)**: Satılık, Kiralık
*   **Level 4 (Alt Tip)**: Daire, Villa, Ofis, Mağaza...

## 2. Kategori Ağacı (Seed Planı)

### 2.1. KONUT (Residential)
*   **Satılık**
    *   Daire (Apartment)
    *   Müstakil Ev (Detached House)
    *   Bina (Building)
    *   Çiftlik Evi (Farm House)
    *   Yazlık (Summer House)
*   **Kiralık**
    *   (Aynı alt tipler)

### 2.2. TİCARİ (Commercial)
*   **Satılık & Kiralık**
    *   Ofis & Büro (Office)
    *   Mağaza & Dükkan (Retail)
    *   Depo (Warehouse)
    *   Fabrika (Factory)
    *   Otopark (Parking)
    *   Arazi / Arsa (Commercial Land) - *Not: Arsa ayrı L2 de olabilir, burada ticari altına aldık.*

### 2.3. GÜNLÜK KİRALIK (Short-term)
*   *Özel Durum*: İşlem tipi sabittir (Kiralık).
    *   Daire
    *   Villa
    *   Oda

## 3. Attribute Setleri (Özellikler)

### 3.1. Ortak (Konut & Ticari)
*   `m2_gross` (Brüt m²)
*   `m2_net` (Net m²)
*   `heating_type` (Isıtma)
*   `building_age` (Bina Yaşı)

### 3.2. Konut Özel
*   `room_count` (Oda Sayısı: 1+1, 2+1...)
*   `floor_location` (Bulunduğu Kat)
*   `bathroom_count` (Banyo Sayısı)
*   `balcony` (Balkon: Var/Yok)
*   `energy_class` (Enerji Sınıfı: A+++ - G) **[AB Zorunlu]**

### 3.3. Ticari Özel
*   `vat_included` (KDV Dahil mi?) **[AB Zorunlu]**
*   `commercial_type` (İşletme Tipi)

## 4. Validasyon Kuralları
*   **Energy Class**: DE/AT/FR ülkelerinde "Satılık Konut" için zorunlu.
*   **Deposit**: "Kiralık" işlemleri için opsiyonel alan.
