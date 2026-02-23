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
