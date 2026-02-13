# Public Facet UI Style Guide

**Document ID:** PUBLIC_FACET_UI_STYLE_GUIDE_v1  
**Date:** 2026-02-13  
**Status:** 🔒 FROZEN  
**Scope:** Public Search Sidebar Facets  

---

## 1. Design Philosophy
Facet UI, yüksek yoğunluklu veri gösterimi (high data density) için optimize edilmiştir. Kullanıcı aynı anda onlarca filtreyi tarayabilir. Bu nedenle:
- **Kompaktlık:** Gereksiz boşluklar minimize edilir.
- **Okunabilirlik:** Label ve count ayrımı net olmalı.
- **Performans:** Render maliyeti düşük olmalı (hafif DOM).

---

## 2. Component Specifications

### 2.1. Checkbox Facet Item
Her bir filtre seçeneği (örn: "BMW (45)") aşağıdaki kurallara uymalıdır:

- **Layout:** Flex row, items-center.
- **Height:** 32px (Compact touch target).
- **Gap:** 8px (Checkbox ile text arası).
- **Font:** `text-sm` (14px), `font-medium`.
- **Colors:**
  - **Text:** `text-foreground` (Primary text color).
  - **Checkbox Border:** `border-input`.
  - **Checkbox Checked:** `bg-primary`, `text-primary-foreground`.
- **States:**
  - **Hover:** Satır arka planı `hover:bg-muted/50` (hafif gri).
  - **Disabled (Count 0):** `opacity-50`, `cursor-not-allowed`.
  - **Selected:** `font-semibold` olabilir.

### 2.2. Count Badge
Filtre yanındaki sayı:
- **Format:** Parantez içinde, örn. `(12)`.
- **Position:** Satırın en sağında veya label'ın hemen yanında (Layout'a göre değişir, sağa yaslı tercih edilir).
- **Style:** `text-xs`, `text-muted-foreground`.

### 2.3. Checkbox Styling (Performance Optimized)
Shadcn/Radix yerine CSS-only implementasyon:
```css
.custom-checkbox {
  appearance: none;
  width: 16px;
  height: 16px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background-color: transparent;
}
.custom-checkbox:checked {
  background-color: var(--primary);
  border-color: var(--primary);
  background-image: url("data:image/svg+xml,..."); /* Check icon */
}
```

### 2.4. Section Header
Facet gruplarının başlıkları (örn: "Marka", "Yakıt Tipi"):
- **Font:** `text-sm`, `font-semibold`.
- **Padding:** `py-3` (Yeterli tıklama alanı).
- **Icon:** Chevron down/up (sağda).

---

## 3. Interaction Patterns

### 3.1. "Show More" Behavior
- **Threshold:** İlk 5 opsiyon görünür.
- **Action:** "+ Daha fazla göster" linki (`text-xs`, `text-primary`).
- **Expansion:** Tıklandığında tüm liste açılır veya scrollable area (max-height: 240px) olur.

### 3.2. Search within Facet
- **Trigger:** Opsiyon sayısı > 10 ise.
- **Input:** Sticky top, `h-8`, `text-xs`.

---

## 4. Implementation Reference
Bu rehber, `FacetRenderer.js` içindeki `CheckboxFacet` bileşeni için bağlayıcıdır.
