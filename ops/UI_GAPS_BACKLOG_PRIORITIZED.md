# UI_GAPS_BACKLOG_PRIORITIZED

Bu backlog FAZ-UI-CHECK-02 çıktılarındaki gap’leri birleştirir.

## 🔴 Kritik
1) **User Panel auth guard eksik** (FIXED)
- Problem: `/account/*` route’ları ProtectedRoute ile korunmuyordu.
- Etki: Yetkisiz erişim / veri sızıntısı riski.
- Uygulanan fix: App.js’de `/account` altında ProtectedRoute eklendi.
- Kabul: login olmadan /account redirect /auth/login.

2) **Public Search FAIL — /api/v2/search endpoint uyumsuzluğu (Release Blocker)**
- Problem: Public Search UI `/api/v2/search` çağırıyor, server.py bunu expose etmiyor.
- Etki: Public Search FAIL, growth/SEO ve core funnel kırık.
- Önerilen fix: Backend router entegrasyonu / uyumlu search endpoint tasarımı (refactor gerektirebilir).
- Kabul kriteri: `/api/v2/search` stabil, smoke PASS, pagination/sort deterministik.

3) **Rate limit/brute force yok (login + upload + reveal + message)**
- Problem: Backend’de rate limit görünmüyor.
- Etki: abuse/DoS, brute force.
- Fix: minimal rate limiter (IP+endpoint) + login throttle.
- Kabul: N deneme sonrası 429.

4) **Moderation aksiyonları: audit zorunluluğu + reason enum zorunluluğu (Release Blocker)**
- Problem: Moderation state change event’leri için audit zorunluluğu ve Red/Düzeltme reason enum standardı tanımlı değil.
- Etki: denetlenebilirlik/hukuki risk; itiraz süreçleri zayıf.

## 🟠 Orta
7) **Moderation Queue ayrımı (INDIVIDUAL / DEALER) + Dealer info panel**
- Problem: Queue ayrımı ve dealer bağlam paneli standardı yok.
- Etki: operasyon verimliliği düşer, SLA/önceliklendirme zayıflar.
- Önerilen fix: Queue filtreleri + dealer bağlam paneli (ticari bilgiler, geçmiş) + ayrı kuyruk görünümü.
- Kabul kriteri: individual/dealer queue filtrelenebilir; dealer listing’lerinde bağlam paneli görünür.

- Önerilen fix: Moderation aksiyonlarında (approve/reject/request-fix) reason enum zorunlu + her aksiyonu audit log’a yaz.
- Kabul kriteri: reason boş geçilemez; audit log’da mode+country_scope+reason ile event kaydı oluşur.

5) **Dealer public profil yok**
- Problem: Public dealer profil route yok.
- Etki: ticari büyüme/SEO eksik.
- Fix: gap olarak işaretle (bu fazda refactor yok).

6) **Moderation workspace route + backend yok**
- Problem: ModerationQueue UI var ama route/backend eksik.
- Etki: operasyonel moderasyon yapılamaz.

## 🟠 Orta
8) Admin finance blokları eksik (invoices/tax/audit route eksikleri)
9) Admin dealer list/onboarding eksik
10) Public detail structured data/canonical/hreflang gap

## 🟡 İyileştirme
11) Admin sidebar collapse tooltip standardı
12) Breadcrumb label mapping genişletme

> Not: Bu fazda yalnızca gap/backlog üretimi ve küçük düzeltmeler yapılır; büyük portal ayrıştırması sonraki faz.
