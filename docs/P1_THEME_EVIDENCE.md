# P1 Theme Evidence

## Light/Dark Screenshots (Chrome)
- `theme-light-home.png`
- `theme-dark-home.png`
- `theme-light-footer-builder.png` (textarea + dropdown kontrast)
- `theme-dark-footer-builder.png` (textarea + dropdown kontrast)

## Admin Theme Toggle Test
- Theme toggle (topbar) ile dark mode geçişi doğrulandı.
- Refresh sonrası tema tercihi korunuyor.

## Persistence & FOUC
- `public/index.html` içinde theme-init script ile localStorage okuması yapılıyor.
- Theme seçimi `localStorage.theme` ile kalıcı.

## Manual Cross-Browser Test (Safari/Firefox)
> Not: Bu ortam Safari/Firefox koşamıyor. Aşağıdaki adımlar manuel doğrulama içindir.
1. Safari: / sayfasında light/dark geçişi + refresh sonrası persist kontrolü.
2. Firefox: /admin/site-design/footer sayfasında textarea + dropdown kontrastı.

