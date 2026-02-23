# UX & Theme Phase Hazırlık Envanteri

**Son güncelleme:** 2026-02-23

## UI Bileşen Envanteri (Özet)
- **Butonlar:**
  - Primary: `bg-blue-600 text-white` (ör. CTA/Devam)
  - Secondary: `border-slate-200 text-slate-700`
  - Danger/Warning: `bg-rose-50 text-rose-700` / `bg-amber-50 text-amber-700`
- **Form Alanları:**
  - Input: `border-slate-200 bg-white text-slate-900`
  - Select: `border-slate-200 bg-white`
  - Disabled: `bg-slate-100 text-slate-400`
- **Badge / Pill:**
  - Status: `bg-emerald-50 text-emerald-700`, `bg-rose-50 text-rose-700`
- **Kart / Panel:**
  - `border bg-white rounded-xl` (admin ve wizard panelleri)
- **Typography:**
  - Başlık: `text-2xl font-semibold` / `text-sm font-semibold`
  - Body: `text-sm text-slate-700`
  - Meta: `text-xs text-slate-500`
- **Renk Paleti (mevcut):**
  - Primary: Blue (600/50)
  - Success: Emerald (600/50)
  - Warning: Amber (600/50)
  - Danger: Rose (600/50)
  - Neutral: Slate (50-900)

## Theme Uygulaması Kırılma Riski Olan Alanlar
1) **Wizard akışları** (stepper/CTA pasifliği) — sınıf değişimleri state hissini bozabilir.
2) **Admin panel modal/overlay** — kontrast ve z-index uyumu kritik.
3) **Kategori seçim akışı** — breadcrumb ve fallback mesajları görünürlüğü.
4) **Health panel** — yoğun bilgi; renk kontrastı ve okunabilirlik şart.
5) **Form doğrulama** — error/success renkleri tutarlı kalmalı.

## Not
- Tema değişimi mimariyi değil yalnız UI katmanını etkiler.
- “Eski yapı korunarak modernize edilir” prensibi geçerlidir.
