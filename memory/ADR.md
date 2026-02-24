# Architecture Decision Records (ADR)

**Son güncelleme:** 2026-02-23

Bu doküman tüm mimari kararların tek kaynağıdır. PRD.md yalnızca ADR referansı içerir.

---

## ADR-STRUCT-001 — ADR ayrı dosyada tutulacak

**Karar:** Tüm mimari kararlar `/app/memory/ADR.md` içinde toplanacak.

**Gerekçe:** PRD iş gereksinimi, ADR teknik karar dokümanıdır.

**Etkileri / trade-off:**
- (+) Karar takibi ve revizyon yönetimi kolaylaşır
- (-) Ek dokümantasyon disiplini gerekir

**Risk & Önlem:** ADR güncellenmezse drift oluşur → Her faz kapanışında ADR kontrolü zorunlu.

---

## ADR-MEDIA-002 — Avrupa için CDN zorunluluğu (Performans hedefleri dahil)

**Karar:** Tüm ilan görselleri CDN üzerinden servis edilecek (Cloudflare/CloudFront sınıfı edge). Belirtilen p95 hedefleri başarı kriteridir.

**Gerekçe:** DE/AT/CH/FR hedefinde tek region servis gecikme ve terk oranını artırır.

**Performans hedefleri (p95):**

**Warm Cache (CDN hit)**
- DE: ≤ 150ms
- AT: ≤ 150ms
- CH: ≤ 170ms
- FR: ≤ 170ms

**Cold Cache (Origin fetch)**
- DE: ≤ 450ms
- AT: ≤ 450ms
- CH: ≤ 500ms
- FR: ≤ 500ms

**Cache kontrol politikası:**
- **Immutable dosya isimlendirme** (content-hash)
- **Long TTL** (immutable + max-age=31536000 önerilir)

**Etkileri / trade-off:**
- (+) Düşük gecikme, yüksek cache hit, daha iyi UX
- (-) Ek maliyet ve cache invalidation disiplini ihtiyacı

**Varsayımlar:** Object storage (S3 uyumlu) mevcut veya sağlanabilir.

**Risk & Önlem:** Yanlış cache politikası “eski görsel” gösterebilir → content-hash dosya adı + immutable caching.

---

## ADR-MEDIA-003 — Görsel pipeline standardı (Mermaid zorunlu)

**Karar:** Upload sonrası görseller WebP’ye çevrilir + resize + watermark uygulanır; ham orijinal ayrı saklanır (opsiyonel).

**Gerekçe:** Performans + marka koruma + tutarlı kalite.

**Etkileri / trade-off:**
- (+) Daha hızlı sayfa yükleme
- (-) İşleme kuyruğu/iş gücü gerektirir

**Risk & Önlem:** İşleme gecikmesi → “processing” state + retry.

**Görsel servisleme akışı (Markdown):**
Upload → Process (WebP + watermark + resize) → Object Storage → CDN cache → Client

```mermaid
graph LR
  A[Upload] --> B[Process: WebP + resize + watermark]
  B --> C[Object Storage (S3-uyumlu)]
  C --> D[CDN Cache (Edge)]
  D --> E[Client]
  B --> F[Orijinal Görsel Arşivi (opsiyonel)]
```

---

## ADR-FLOW-006 — Referans görsel akışı davranış kilidi

**Karar:** 5 görseldeki kategori seçimi akışı tek doğru akıştır. Alternatif akış üretilmez.

**Sıralama (kilitli):**
1) Modül kartları (Emlak/Vasıta/...)
2) L1 liste
3) L2/L3 drill-down
4) Alt tip seçimi paneli

**UI davranış kilidi:**
- Kategori tamamlanmadan “ileri/Devam” pasif
- Her drill-down adımı URL ile temsil edilir
- Geri tuşu state kaybetmez
- Seçim tamamlanınca otomatik **Çekirdek Alanlar** adımına geçiş

**Gerekçe:** “Askıda/amatör” algısını ortadan kaldırmak; deterministik UX.

**Etkileri / trade-off:**
- (+) UX tutarlılığı, daha az kullanıcı hatası
- (-) Esneklik azalır (bilinçli tercih)

---

## ADR-DOC-002 — Pipeline diyagram zorunlu

**Karar:** Kritik mimari akışlar sadece metinle değil Mermaid diyagramla da dokümante edilecek.

**Gerekçe:** Yanlış yorum riskini azaltmak.

**Etkileri / trade-off:**
- (+) Netlik artar
- (-) Dokümantasyon süresi artar

---

## ADR-CDN-001 — CDN sağlayıcı seçimi

**Karar:** Cloudflare hedeflenecek (Images/Cache + Analytics).

**Gerekçe:** Avrupa edge kapsaması güçlü, cache/analytics metrikleri erişilebilir, operasyonel kurulum hızlı.

**Etkileri / trade-off:**
- (+) DE/AT/CH/FR düşük gecikme hedefi için uygun
- (-) Sağlayıcıya bağımlılık → adapter katmanı ile yumuşatılır

**Varsayımlar:** Görsel servisleme Cloudflare üzerinden yönlendirilebilir (DNS/CDN katmanı).

---

## ADR-OBS-CDN-001 — Cloudflare Metrics Adapter (Health Panel)

**Karar:** Health panelde Cloudflare metrikleri gerçek entegrasyon ile izlenecek (feature-flag + cache TTL).

**Adapter yaklaşımı (okuma seti):**
- **Endpoint:** `https://api.cloudflare.com/client/v4/graphql`
- **Cache Hit Ratio:** `httpRequests1hGroups.sum.requests` + `sum.cachedRequests`
- **Origin Fetch (miss):** `httpRequests1hGroups` + `responseCached: Uncached`
- **Image Latency p95:** `httpRequests1hGroups.quantiles.edgeTimeToFirstByteMsP95` + `contentTypeMap_edgeResponseContentTypeName: "image"`
- **Warm/Cold ayrımı:** `responseCached: Cached` ve `responseCached: Uncached`

**Kontroller:**
- Feature flag default kapalı (`CLOUDFLARE_ANALYTICS_ENABLED=false`)
- Cache TTL: 60s
- Credential’lar sadece secret manager

**Etkileri / trade-off:**
- (+) Performans denetimi ölçülebilir
- (-) Credential ve rate-limit yönetimi gerekir

---

## ADR-CAT-002 — Manuel kategori yönetimi korunacak

**Karar:** Kategori sistemi seed bağımlı değil; admin manuel CRUD ana yöntem.

**Gerekçe:** Operasyonel esneklik ve veri bağımsız test.

**Etkileri / trade-off:**
- (+) Seed hatalarından bağımsız çalışma
- (-) Operasyon disiplini gerektirir

**Risk & Önlem:** Yanlış hiyerarşi → parent/module/country validasyonu.

---

## ADR-COMPAT-001 — Eski yapı korunarak genişletme

**Karar:** Yeni wizard ve akış geliştirmeleri mevcut DB şemasını bozmayacak.

**Gerekçe:** Stabil çalışan parçaların yeniden yazımı risklidir.

**Etkileri / trade-off:**
- (+) Daha az teknik borç
- (-) Refactor alanı sınırlı

---

## ADR-P0-CLOSE — P0 resmi kapanış ve 520-scan regresyon kilidi

**Karar:** P0 “CLOSED” kabul edilir; 520 tarama paketi release kapısıdır.

**Gerekçe:** Mongo 0-iz ve 520=0 sürdürülebilir olmalı; regresyon en büyük operasyonel risk.

**Etkileri / trade-off:**
- (+) Üretim stabilitesi artar
- (+) Sonraki fazlarda debug maliyeti düşer
- (-) Release süresine zorunlu kontrol adımı eklenir

**Varsayımlar:** CI/ops pipeline’a 520-scan komut seti eklenebilir.

**Risk & Önlem:** Tarama paketi eksik endpoint kapsayabilir → endpoint listesi RBAC_ENDPOINT_MAP ile senkron tutulur.

---

## ADR-RBAC-FREEZE-V1 — RBAC değişiklikleri kontrollü

**Karar:** RBAC allowlist/matrix “FREEZE v1” ile kilitlenir; değişiklikler diff + onay gerektirir.

**Gerekçe:** Yetki regresyonu güvenlik açığıdır; kontrollü değişim şart.

**Etkileri / trade-off:**
- (+) Deny-by-default garantisi
- (-) Yetki değişikliği hızı düşer

**Risk & Önlem:** Yeni endpoint eklenip map’e yazılmazsa erişim bozulur → “map coverage” kontrolü eklenir.

---

## ADR-CAT-UI-003 — Manuel kategori yönetimi UI yaklaşımı

**Karar:** “Manuel ekleme” için mevcut Admin Kategoriler UI genişletilecek; yeni modal açılmayacak.

**Gerekçe:** En düşük riskli yol; kullanıcı alışkanlığı korunur.

**Etkileri / trade-off:**
- (+) Hızlı ve bakımı kolay
- (-) Çok adımlı hiyerarşi girişinde UX biraz daha operasyonel kalır

---

## ADR-RE-LEVELS-001 — Emlak hiyerarşi standardı

**Karar:** Emlak 4 seviye + alt tip (Satılık/Kiralık/Günlük) standardı uygulanacak.

**Gerekçe:** Referans akış (Sahibinden mantığı) ile birebir uyum ve wizard deterministikliği.

**Örnek şablon:**
- **L1:** Emlak
- **L2:** Konut | İş Yeri | Arsa | Bina | Devre Mülk | Turistik Tesis
- **L3 (Konut):** Daire | Müstakil Ev | Villa | Residence | Yazlık
- **Alt Tip:** Satılık | Kiralık | Günlük Kiralık

**Etkileri / trade-off:**
- (+) Kullanıcı akışı netleşir, “askıda kalma” biter
- (-) Kategori modelinde metadata disiplini gerekir

---

## ADR-FALLBACK-001 — Kategori yoksa davranış

**Karar:** Fallback metni “Kategori bulunamadı – yöneticiye başvurun.” ve güvenli geri dönüş CTA’sı.

**Gerekçe:** Boş veri durumunda bile profesyonel davranış; hata yerine yönlendirme.

**Etkileri / trade-off:**
- (+) Kullanıcı kaybı azalır
- (-) Admin operasyonuna bağımlılık görünür olur

---

## ADR-SEC-CF-003 — Cloudflare kimlik bilgileri paylaşımı

**Karar:** Account/Zone ID ve token dahil tüm Cloudflare değerleri Secret Manager üzerinden sağlanır; chat üzerinden paylaşım yok.

**Gerekçe:** Güvenlik ve sızıntı riski.

**Etkileri / trade-off:**
- (+) Güvenli operasyon
- (-) Ops aksiyonu gerektirir

---

## ADR-CONFIG-001 — Feature flag konfigürasyonu

**Karar:** CF_METRICS_ENABLED config olarak .env üzerinden yönetilir; secret manager sadece gizli değerler içindir.

**Gerekçe:** Flag secret değil; ortam bazlı hızlı kontrol gerekir.

**Etkileri / trade-off:**
- (+) Kolay aç/kapa
- (-) Yanlışlıkla prod’da açılabilir → default false + ops prosedürüyle önlenir

---

## ADR-OBS-CDN-002 — Ülke bazlı CDN kırılımı zorunlu

**Karar:** Health panelde CDN metrikleri DE/AT/CH/FR kırılımıyla gösterilecek.

**Gerekçe:** Avrupa hedefi ülke bazlı performans denetimi gerektirir.

**Etkileri / trade-off:**
- (+) Gerçek operasyonel görünürlük
- (-) Analytics sorgu karmaşıklığı artar

**Risk & Önlem:** Country geo verisi eksik olabilir → fallback global metrik göster.

---

## ADR-RE-ACCEPT-002 — Emlak PASS zorunlu

**Karar:** Referans akış “Emlak modülü” için PASS olmadan ilan verme akışı tamamlanmış sayılmaz.

**Gerekçe:** Emlak en kompleks modül; burada çalışan akış diğer modüller için referans olur.

**Etkileri / trade-off:**
- (+) Kalite standardı yükselir
- (-) Seed/veri operasyonuna bağımlılık

---

## ADR-UX-ROADMAP-002 — Tema uygulaması çekirdek mimariyi etkilemez

**Karar:** Theme değişimi yalnız UI katmanında uygulanır; wizard/state/backend etkilenmez.

**Gerekçe:** Stabil core korunmalı.

**Etkileri / trade-off:**
- (+) Düşük riskli görsel dönüşüm
- (-) Component override disiplinine ihtiyaç

---

## ADR-CAT-OPS-004 — Emlak kategori giriş yöntemi

**Karar:** Emlak hiyerarşisi manuel admin UI ile girilir; otomatik bulk doldurma yapılmaz.

**Gerekçe:** “Manuel girişli olacak, eski yapı korunacak” hedefi.

**Etkileri / trade-off:**
- (+) Operasyonel kontrol, şema disiplini
- (-) Zaman alır

---

## ADR-CONFIG-002 — Cloudflare ID’ler Admin UI üzerinden girilebilir

**Karar:** CLOUDFLARE_ACCOUNT_ID ve CLOUDFLARE_ZONE_ID admin panelinden manuel girilebilir.

**Gerekçe:** Ops bağımlılığını azaltmak, hızlı aktivasyon.

**Etkileri / trade-off:**
- (+) Hızlı test ve preview aktivasyonu
- (-) Yanlış giriş riski → canary validation zorunlu

**Risk & Önlem:** Hatalı ID → adapter error; canary zorunlu doğrulama.

---

## ADR-SEC-CONFIG-002 — Config şifreli saklama

**Karar:** Admin üzerinden girilen ID’ler encrypted olarak saklanır.

**Gerekçe:** Hassas yapı bilgisi.

**Etkileri / trade-off:**
- (+) Güvenlik
- (-) Key management gerektirir

---

## ADR-OBS-CF-004 — Config source görünürlüğü

**Karar:** Health panel config kaynağını gösterir (secret/db/env).

**Gerekçe:** Debug ve operasyonel şeffaflık.

**Etkileri / trade-off:**
- (+) Hızlı sorun tespiti
- (-) Ek endpoint alanı

---

## ADR-UI-CONFIG-001 — Cloudflare konfigürasyonu kart bazlı

**Karar:** Cloudflare ayarları mevcut System Settings içinde kart olarak yer alacak.

**Gerekçe:** Entegrasyon mantıksal olarak “system integration” kategorisinde.

**Etkileri / trade-off:**
- (+) Dağınık sayfa oluşmaz
- (-) Settings sayfası büyür (kabul)

---

## ADR-SEC-ENC-001 — Konfigürasyon şifreleme anahtarı

**Karar:** CONFIG_ENCRYPTION_KEY env zorunlu (32-byte base64).

**Gerekçe:** DB’de saklanan integration ID’leri plaintext olmamalı.

**Etkileri / trade-off:**
- (+) Güvenlik
- (-) Key yönetimi gerektirir

**Risk & Önlem:** Key kaybı → config decrypt edilemez → rotation prosedürü dokümante edilecek.

---

## ADR-OBS-CANARY-001 — Canary enum standardı

**Karar:** Canary sonuçları enum ile gösterilecek: OK / AUTH_ERROR / SCOPE_ERROR / NO_DATA / RATE_LIMIT / CONFIG_MISSING.

**Gerekçe:** Debug netliği.

**Etkileri / trade-off:**
- (+) Operasyonel şeffaflık
- (-) UI karmaşıklığı hafif artar

---

## ADR-CONFIG-SEC-001 — Encryption Key Hard Gate

**Karar:** CONFIG_ENCRYPTION_KEY olmadan config yazılamaz.

**Gerekçe:** Production güvenlik standardı.

**Etkileri:**
- (+) Config sızıntısı engellenir
- (-) Setup aşamasında blokaj yaratır

---

## ADR-OBS-ERR-002 — Teknik hata sebepleri UI’da gösterilmeli

**Karar:** “Kaydedilemedi” yerine spesifik sebep gösterilecek.

**Gerekçe:** Ops debug hızlanır.

**Etkileri:**
- (+) Debug süresi azalır
- (-) Enum yönetimi gerekir

---

## ADR-CANARY-003 — Canary enum standardizasyonu

**Karar:** Canary enum sadece: OK | CONFIG_MISSING | SCOPE_ERROR | API_ERROR.

**Gerekçe:** İzlenebilirlik standardı.

**Etkileri:**
- (+) Basit raporlama
- (-) Detaylar log reason alanında

---

## ADR-OPS-ENC-001 — Encryption key ops sorumluluğunda

**Karar:** CONFIG_ENCRYPTION_KEY preview dahil ops tarafından sağlanır.

**Gerekçe:** Anahtar yönetimi güvenlik sorumluluğu.

**Etkileri / trade-off:**
- (+) Güvenli yönetim
- (-) Ops bağımlılığı

---

## ADR-CANARY-LOCK-001 — Canary enum kilidi

**Karar:** OK | CONFIG_MISSING | SCOPE_ERROR | API_ERROR dışına çıkılmaz.

**Gerekçe:** UI/raporlama karmaşıklığını azaltır.

---

## ADR-LOG-STD-001 — Startup log standardı

**Karar:** Startup’ta `CONFIG_ENCRYPTION_KEY loaded=true/false` satırı zorunlu.

**Gerekçe:** Hızlı teşhis.

---

## ADR-UX-CF-001 — Teknik enum UI’dan ayrıştırılacak

**Karar:** CONFIG_MISSING, cf_metrics_disabled gibi teknik durumlar ana UI metninde gösterilmeyecek; yalnız tooltip/expand altında gösterilecek.

**Gerekçe:** Teknik enumlar “sistem bozuk” algısı yaratır.

**Etkileri / trade-off:**
- (+) Daha net UX
- (-) Teknik detay görmek için ek tıklama gerekir

---

## ADR-UX-CF-002 — Tek durum mesajı kuralı

**Karar:** Kart üzerinde aynı anda tek blokaj mesajı gösterilecek; öncelik sırası sabit.

**Gerekçe:** Çakışan mesajlar kullanıcıyı yanıltıyor.

**Etkileri / trade-off:**
- (+) Netlik artar
- (-) İkincil uyarılar tooltip ile görünür

---

## ADR-UX-CF-003 — Guard durumunda canary kapalı

**Karar:** Encryption key yokken canary çalıştırılamaz (disabled).

**Gerekçe:** Test edilemeyecek akışları kullanıcıya sunmamak.

**Etkileri / trade-off:**
- (+) Gereksiz hata trafiği azalır
- (-) “Deneyeyim” yaklaşımı engellenir

---

## ADR-CANARY-LOCK-001 — Canary enum kilidi

**Karar:** Canary enum sadece OK | CONFIG_MISSING | SCOPE_ERROR | API_ERROR.

**Gerekçe:** Basit izleme standardı.

---

## ADR-OPS-PHASEA-001 — Phase A kapanış kriteri (Cloudflare Ops Inject)

**Karar:** Phase A kapanış kriteri = env/secret inject + backend restart + health-detail canary OK + admin UI canary OK + kanıt dosyaları.

**Gerekçe:** Kod hazır olsa bile operasyonel doğrulama yoksa faz kapanmış sayılmaz.

**Etkileri / trade-off:**
- (+) Prod benzeri doğrulama kanıtı oluşur
- (+) RBAC’a geçişte belirsizlik kalmaz
- (-) Restart gerektirir (kısa kesinti riski)

**Varsayımlar:** Cloudflare entegrasyonu token ile çalışır ve token sağlanabilir.

**Risk & Önlem:** Secret sızıntı riski → yalnızca env/secret manager, UI maskeli gösterim.

---

## ADR-SEC-CF-004 — Cloudflare kimlik bilgileri env/secret + UI maskeli

**Karar:** Cloudflare kimlik bilgileri env/secret üzerinden yönetilir; Admin UI yalnızca maskeli gösterir.

**Gerekçe:** Güvenlik ve izlenebilirlik.

**Etkileri / trade-off:**
- (+) Sızıntı riski düşer
- (-) Ops bağımlılığı artar

---

## ADR-RBAC-001 — Deny-by-default + Allowlist RBAC

**Karar:** Phase B RBAC yaklaşımı deny-by-default + explicit allowlist + audit log (RBAC_DENY / RBAC_POLICY_MISSING).

**Gerekçe:** Yanlışlıkla açık kalan endpoint riskini minimize etmek.

**Etkileri / trade-off:**
- (+) Güvenlik artar, saldırı yüzeyi daralır
- (-) İlk kurulumda endpoint/rol haritalama yükü artar

---

## ADR-RBAC-002 — Kanonik rol seti (Freeze v1)

**Karar:** Başlangıç rol seti = SUPER_ADMIN, ADMIN, MODERATOR, SUPPORT, DEALER_ADMIN, DEALER_USER, CONSUMER.

**Gerekçe:** Admin/portal ayrımı için minimum rol seti.

**Etkileri / trade-off:**
- (+) Rol karmaşıklığı sınırlı kalır
- (-) Legacy roller için eşleme yönetimi gerekir

---

## ADR-DATALAYER-001 — SQL Tek Kaynak (Mongo Tasfiye)

**Karar:** Mongo tamamen tasfiye; tüm okuma/yazma SQL üzerinden yapılacak.

**Gerekçe:** 520 kök sebebi Mongo bağımlılığı; operasyonel güvenilirlik için tek veri katmanı.

**Etkileri / trade-off:**
- (+) Deterministik davranış, bakım maliyeti düşer
- (-) İlk yatırım maliyeti (şema + migrasyon + refactor)

---

## ADR-DATALAYER-002 — Keskin Cutover (Dual-run yok)

**Karar:** Mongo→SQL geçişte dual-read/write yapılmayacak.

**Gerekçe:** Tutarlılık hatası ve debug maliyeti yüksek.

**Etkileri / trade-off:**
- (+) Basit ve net sorumluluk
- (-) Cutover anında dikkat gerektirir

---

## ADR-DATALAYER-003 — P0 Öncelik: Admin 520 Zinciri

**Karar:** İlk dalga: admin system-settings + invite akışları ve bağımlılıkları.

**Gerekçe:** Admin panel stabilizasyonu RBAC/Audit için ön şart.

