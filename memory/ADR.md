# Architecture Decision Records (ADR)

**Son güncelleme:** 2026-02-24

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

## ADR-STRIPE-IDEMPOTENCY-NOW — Stripe idempotency testi hemen

**Karar:** Test key mevcutsa Stripe idempotency testi hemen çalıştırılır.

**Gerekçe:** Monetizasyon tarafında regresyon riski yüksek; kapı kapatılmadan kanıt gerekir.

**Etkileri / trade-off:**
- (+) Finansal çift çekim riski minimize
- (-) Test key yoksa blocker kalır

**Varsayım:** Pod/env içinde geçerli Stripe test key sağlanır.

**Risk & Önlem:** Key yok/yanlış → test “BLOCKED” işaretlenir; diğer P0.1 akışları devam eder.

---

## ADR-2FA-TEST-USER — 2FA test kullanıcısı

**Karar:** 2FA açık kullanıcı yoksa user2@platform.com üzerinde 2FA etkinleştirilerek test yapılır.

**Gerekçe:** Mevcut kullanıcı beklemek yerine kontrollü test hesabı ile kanıt üretmek.

**Etkileri / trade-off:**
- (+) Tekrarlanabilir test
- (-) Test hesabı yönetimi gerekir

---

## ADR-RBAC-CI-HARD-GATE — RBAC coverage CI zorunlu

**Karar:** RBAC endpoint coverage CI’da zorunlu kontrol olur; map dışı endpoint release edilemez.

**Gerekçe:** “Map dışı endpoint” güvenlik açığı üretir; release kapısı olmalı.

**Etkileri / trade-off:**
- (+) Güvenlik regresyonu engellenir
- (-) Geliştirici akışında ek disiplin gerekir

---

## ADR-P0.1-SECURITY-HARDEN — Güvenlik sertleştirme kapısı

**Karar:** Stripe idempotency + rate limit + 2FA doğrulaması P1’e geçmeden tamamlanmalı.

**Gerekçe:** Monetizasyon ve auth katmanı güvenlik açısından kritik.

**Etkileri / trade-off:**
- (+) Finansal risk azalır
- (-) Kısa vadeli geliştirme yavaşlar

---

## ADR-24H-LOG-BASED-CLOSE — Log-based 24h monitoring kapanışı

**Karar:** Health-detail log bucket “last 24h” verisi kullanılarak rapor CLOSED yapılır.

**Gerekçe:** Operasyonel gerçekliği temsil ediyor; gerçek 24h beklemek gereksiz gecikme yaratır.

**Etkileri / trade-off:**
- (+) Faz kapanışı hızlanır
- (-) Canlı trafik varyasyonunu birebir ölçmeyebilir

**Risk:** Eksik veri → timestamp aralığı rapora açıkça yazılır.

---

## ADR-2FA-BACKUP-ENFORCE — Backup code tek kullanım

**Karar:** Backup code tek-kullanım enforce edilir ve kanıtlanır.

**Gerekçe:** Hesap ele geçirme riskini azaltır; compliance açısından net.

**Etkileri:**
- (+) Güvenlik artar
- (-) Kullanıcı destek talepleri artabilir

---

## ADR-RBAC-CI-VISIBILITY — PR comment görünürlüğü

**Karar:** RBAC coverage sonucu PR yorumuna otomatik eklenir.

**Gerekçe:** Reviewer görünürlüğü ve governance hızlanır.

**Etkileri:**
- (+) Operasyonel şeffaflık
- (-) PR yorum yoğunluğu (summary + failure detay ile sınırlanır)

---

## ADR-P0.1-CLOSEOUT-GATE — P0.1 kapanış kapısı

**Karar:** P0.1 kapanışı için zorunlu 3 kanıt: 
(a) Stripe idempotency evidence, 
(b) 2FA backup code tek-kullanım evidence, 
(c) Log-based 24h monitoring report CLOSED.

**Gerekçe:** Güvenlik + ödeme + operasyonel stabilite aynı kapıda kilitlenmeli.

**Etkileri / trade-off:**
- (+) Go-live/regresyon riski düşer
- (-) 24h koşusu bitmeden kapanış gecikir

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


---

## ADR-MODERATION-FREEZE-REASON — Freeze için reason alanı

**Karar:** Freeze için opsiyonel `moderation_freeze_reason` alanı tutulur ve audit log’a yazılır.

**Gerekçe:** Operasyonel şeffaflık ve izlenebilirlik.

**Etkileri / trade-off:**
- (+) Incident sonrası analiz kolaylaşır
- (+) Banner bilgilendirici olur
- (-) UI karmaşıklığı minimal artar

**Risk & Önlem:** Hassas bilgi yazılmamalı → kısa serbest metin uyarısı eklenir.

---

## ADR-MODERATION-ENFORCEMENT-DOUBLE-GUARD — UI + backend çift koruma

**Karar:** Moderation Freeze, UI disable + backend 423 Locked birlikte çalışır.

**Gerekçe:** Defense-in-depth, istemci manipülasyonu riskini azaltır.

**Etkileri / trade-off:**
- (+) Manipülasyon riski düşer
- (-) Ek test gerektirir

---

## ADR-PENDING-LISTING-GENERATION — Pending listing üretimi

**Karar:** Pending listing üretimi test kullanıcı publish akışı ile yapılır.

**Gerekçe:** Sistem uçtan uca doğrulanır; queue’ya düşme garantilenir; seed/manüel create sapmaları önlenir.

**Etkileri / trade-off:**
- (+) Gerçek üretim akışı kanıtlanır
- (+) Moderation pipeline parity doğrulanır
- (-) Test kullanıcı kredisi/erişimi gerektirir

**Risk & Önlem:** Hesap yoksa fallback: admin panelde create (evidence’de “fallback” etiketiyle).

---

## ADR-EVIDENCE-NAMING — Evidence dosya adı standardı

**Karar:** Evidence dosya adı `/app/memory/MODERATION_FREEZE_EVIDENCE.md`.

**Gerekçe:** Memory/evidence konvansiyonu ile uyumlu, araması kolay.

**Etkileri / trade-off:**
- (+) Denetim/closeout izlenebilirliği artar
- (-) Yok

---

## ADR-EXPORT-HISTORY-FIELDS — Export History alanları

**Karar:** Export history tabloda minimum alanlar `requested_at`, `status`, `download_link`, `expires_at` gösterilecek.

**Gerekçe:** 30 gün retention ile kullanıcıya net son tarih göstermeden UX eksik kalır.

**Etkileri / trade-off:**
- (+) Kullanıcı beklentisi yönetilir
- (+) Destek talepleri azalır
- (-) Ek kolon + test güncellemesi


---

## ADR-UH1-EXECUTION-MODE — Doc-first + aynı sprint implementasyon

**Karar:** UH1 yürütme modu doc-first, aynı sprintte UI implementasyonu.

**Gerekçe:** Altyapı stabil; hızlı kullanıcı çıktısı + disiplinli dokümantasyon.

**Etkileri / trade-off:**
- (+) Hızlı çıktı
- (-) Doküman disiplini bozulursa kalite düşer

**Risk & Önlem:** Scope creep → UH1 backlog dışı iş alınmaz.

---

## ADR-UH1-DATA-SOURCE — KPI gerçek API + deterministic fallback

**Karar:** KPI verileri mevcut API’lerden; API yoksa 0 + “Veri hazırlanıyor”.

**Gerekçe:** Prod davranışı erken görünür.

**Etkileri / trade-off:**
- (+) Sürpriz azalır
- (-) API eksikleri görünür

---

## ADR-UH1-REASON-SOURCE — Moderation reason listing payload

**Karar:** Moderation reason tek kaynak listing payload içindeki `moderation_reason`.

**Gerekçe:** Ek çağrı yok, performans/karmaşıklık azalır.

**Etkileri / trade-off:**
- (+) Daha hızlı sayfa
- (-) Moderation detayları sınırlı

---

## ADR-UH1-ROUTE — Consumer dashboard route

**Karar:** Consumer dashboard `/account` olarak sabitlenir. Güvenlik `/account/security`.

**Gerekçe:** Basit, tutarlı navigasyon.

**Etkileri / trade-off:**
- (+) Net yönlendirme
- (-) Legacy linkler redirect ister

---

## ADR-UH1-COLOR-TOKENS — Color tokens v1

**Karar:** CTA #F57C00, header #1B263B, text #415A77, bg #F8F9FA + semantic tokens.

**Gerekçe:** Aksiyon vurgusu + kurumsal stabilite.

**Risk & Önlem:** Kontrast → WCAG AA kontrolü.

---

## ADR-UH1-SCROLLABLE-REMOVAL — Nested scroll kaldırma

**Karar:** Dashboard’da nested scroll yok; tek ana sayfa scroll.

**Gerekçe:** UX karmaşasını azaltır.

---

## ADR-UH1-STATUS-TRANSPARENCY — Status görünürlüğü

**Karar:** Listing status + moderation reason her zaman görünür.

**Gerekçe:** Destek yükü azalır.

---

## ADR-UH1-QUOTA-VISIBILITY — Quota bilgisi gizlenmez

**Karar:** Kalan ücretsiz ilan hakkı dashboard’da gösterilir.

**Gerekçe:** Monetization şeffaflığı.


---

## ADR-UH1-CLOSEOUT-EVIDENCE — Evidence Matrix standardı

**Karar:** UH1 closeout için screenshot + curl log + route doğrulama zorunlu.

**Gerekçe:** UI fazları görsel kanıt olmadan kapatılmayacak.

**Etkileri / trade-off:**
- (+) Audit izlenebilirliği
- (-) Dokümantasyon süresi artar

---

## ADR-ADMIN-FINAL-NEXT — Sonraki faz Admin Operasyonel Finalizasyon

**Karar:** Public tasarım öncesi Admin operasyonel finalizasyon başlatılır.

**Gerekçe:** Gelir, risk ve moderation merkezi Admin’dir.

**Etkileri / trade-off:**
- (+) Sistem kontrolü artar
- (-) Public dönüşüm gecikir

---

## ADR-UH1-QUICK-PREVIEW-P1 — Quick Preview modal P1

**Karar:** Quick Preview modal P1 enhancement olarak planlanır.

**Gerekçe:** Değer üretir ama core değil.

**Etkileri / trade-off:**
- (+) Etkileşim artar
- (-) Dashboard karmaşıklığı artabilir


---

## ADR-AF-DEPENDENCY-FIRST — Dependency analizi önce

**Karar:** Sprint 1 başlamadan önce dependency map + gap list + implementation order hazırlanır.

**Gerekçe:** Guard/permission/audit bağımlılıkları erken görünür.

**Etkileri / trade-off:**
- (+) Blokajlar sprint başında görünür
- (-) Ticket’lara başlama gecikir

---

## ADR-AF-QUICK-PREVIEW-ACTIONS — Quick Preview aksiyonları

**Karar:** Quick Preview’a yalnızca “Düzenle” + “Yayından Kaldır” eklenir.

**Gerekçe:** Minimal ama fonksiyonel; dashboard sade kalır.

**Guard:** Ownership + status=published, unpublish confirmation modal.

---

## ADR-AF-ADMIN-FINAL-SCOPE — Admin Final Sprint 1

**Karar:** Sprint 1 sadece monetization/risk/verification/moderation/finance kapsar.

**Gerekçe:** Operasyonel kilitleme öncelikli.


---

## ADR-AF-MIGRATION-IMPACT-FIRST — Migration impact analizi zorunlu

**Karar:** AF Sprint 1 implementasyonundan önce migration impact analizi hazırlanır.

**Gerekçe:** Constraint eklemek canlı veride risklidir; rollback güvenliği gerekir.

**Etkileri / trade-off:**
- (+) Veri bütünlüğü korunur
- (-) Sprint başlangıcı gecikebilir

---

## ADR-AF-ROLLBACK-MANDATORY — Rollback zorunlu

**Karar:** Her migration için down script zorunlu; rollback’siz deploy yasak.

**Gerekçe:** Operasyonel güvenlik.


---

## ADR-MIGRATION-DRY-RUN-MANDATORY — Dry-run zorunlu release gate

**Karar:** Her production migration öncesi dry-run PASS zorunlu.

**Gerekçe:** Veri bütünlüğü riski sıfırlanmalı; rollback ihtiyacı azalmalı.

**Etkileri / trade-off:**
- (+) Production güvenliği artar
- (-) Deploy süresi uzar

**Risk / Önlem:** Script outdated → impact analizi ile senkron zorunlu.
