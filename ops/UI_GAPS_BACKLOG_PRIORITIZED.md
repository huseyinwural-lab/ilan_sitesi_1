# UI_GAPS_BACKLOG_PRIORITIZED

Bu backlog FAZ-UI-CHECK-02 çıktılarındaki gap’leri birleştirir.

## 🔴 Kritik
1) **User Panel auth guard eksik**
- Problem: `/account/*` route’ları ProtectedRoute ile korunmuyor.
- Etki: Yetkisiz erişim / veri sızıntısı riski.
- Önerilen fix: App.js’de /account altında ProtectedRoute ekle.
- Kabul: login olmadan /account redirect /auth/login.

2) **Rate limit/brute force yok (login + upload + reveal + message)**
- Problem: Backend’de rate limit görünmüyor.
- Etki: abuse/DoS, brute force.
- Fix: minimal rate limiter (IP+endpoint) + login throttle.
- Kabul: N deneme sonrası 429.

3) **Dealer public profil yok**
- Problem: Public dealer profil route yok.
- Etki: ticari büyüme/SEO eksik.
- Fix: gap olarak işaretle (bu fazda refactor yok).

4) **Moderation workspace route + backend yok**
- Problem: ModerationQueue UI var ama route/backend eksik.
- Etki: operasyonel moderasyon yapılamaz.

## 🟠 Orta
5) Admin finance blokları eksik (invoices/tax/audit route eksikleri)
6) Admin dealer list/onboarding eksik
7) Public detail structured data/canonical/hreflang gap

## 🟡 İyileştirme
8) Admin sidebar collapse tooltip standardı
9) Breadcrumb label mapping genişletme

> Not: Bu fazda yalnızca gap/backlog üretimi ve küçük düzeltmeler yapılır; büyük portal ayrıştırması sonraki faz.
