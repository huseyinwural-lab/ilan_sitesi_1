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

