# ROADMAP
**Son güncelleme:** 2026-03-03 18:55:00 UTC

## P0 (Aktif)
- Middleware kaynaklı `RuntimeError: No response returned` kök neden analizi ve kalıcı fix
- Meilisearch settings timeout/retry stabilizasyonu (ops alarmlarını azaltma)
- Kurumsal portal row2/row4 yeni menü davranışı için son kullanıcı UAT (piksel + içerik tamlık onayı)

## P1 (Sıradaki)
- Permission **What-if Simulator** (save öncesi etki önizleme)
- Permission değişikliklerinde **4-eyes approval** (ikinci admin onayı)
- User/Dealer flow formal validation turu (permission + yeni kurumsal layout sonrası)
- Audit/Permissions preset filtre setleri (Ops/Fraud/Compliance)

## P2 (Backlog)
- Gelişmiş finans analitikleri + conversion funnel + A/B test altyapısı
- Policy snapshot & one-click rollback (permission set versiyonlama)

## P3 (Enterprise Scale)
- SRE pack (SLO/SLA dashboard), DR/backup drill, security/cost audit paketleri

## Next Action Items
- FAZ 1 sonrası kalan P0 operasyon hatalarını kapat (`No response returned`, meili settings)
- Kurumsal portalın yeni 11 modüllü row2 yapısı için kullanıcıdan final onayı al
- Hesabım alt modüllerinde kullanıcıdan istenen ekstra metin/alan düzeltmelerini kapat
- What-if simulator için veri modeli/endpoint kontratını netleştir
- 4-eyes approval akışı için approval queue + audit event şemasını planla
