# UI Style Guide — Tema Paleti

## Ana Kurumsal Renkler (Semantik)
- **Primary (Turuncu):** `#FF7000`  → `--color-primary`
- **Primary Dark:** `#E65A00` → `--color-primary-dark`
- **Secondary (Mavi):** `#007BFF` → `--color-secondary`
- **Secondary Dark:** `#0056D2` → `--color-secondary-dark`
- **Accent (Teal):** `#00A0B0` → `--color-accent`

## Metin & Arka Plan
- **Text Primary:** `#1B263B` → `--text-primary`
- **Text Secondary:** `#415A77` → `--text-secondary`
- **Text Inverse:** `#FFFFFF` → `--text-inverse`
- **Page Background:** `#F8F9FA` → `--bg-page`
- **Surface:** `#FFFFFF` → `--bg-surface`
- **Surface Muted:** `#F8F9FA` → `--bg-surface-muted`
- **Soft Surface:** `rgba(255,255,255,0.1)` → `--bg-surface-soft`
- **Warm Background:** `#F7C27A` → `--bg-warm`
- **Warm Border:** `#F0CDA8` → `--border-warm`
- **Border Subtle:** `#E2E8F0` → `--border-subtle`

## Dark Mode Karşılıkları
Dark modda renkler `.dark` altında semantik karşılıklarla tanımlanır:
- `--bg-page: #0F172A`
- `--bg-surface: #111827`
- `--text-primary: #F8FAFC`
- `--text-secondary: #94A3B8`
- `--border-subtle: #273449`
- `--bg-warm: #2B3342`

## Kullanım Örnekleri
- `bg-[var(--bg-surface)]`
- `text-[var(--text-primary)]`
- `border-[var(--border-subtle)]`
- `hover:bg-[var(--color-primary-dark)]`


## Layout Standartları
- **Header yükseklik:** 64px (desktop), 56px (mobile)
- **Footer minimum yükseklik:** 120px
- **Breakpoints:** xs <640px, sm 640–767, md 768–1023, lg 1024–1279, xl 1280+

## Kontrast (WCAG AA)
- Light/Dark modda metin-kontrastı AA hedefli.
- Textarea ve dropdown gibi bileşenlerde `--text-primary` ve `--bg-surface` kullanılır.
