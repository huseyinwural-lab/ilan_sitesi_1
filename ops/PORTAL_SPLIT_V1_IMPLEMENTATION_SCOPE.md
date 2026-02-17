# PORTAL_SPLIT_V1_IMPLEMENTATION_SCOPE

## Scope Lock

### Sadece yapılacaklar
1) Route’ların portal modüllerine taşınması
2) Lazy chunk split (CRA + CRACO)
3) PortalGate (pre-layout guard)
4) Login ayrımı
   - `/login`
   - `/dealer/login`
   - `/admin/login`
5) Demo credentials prod’da gizleme (ENV kontrol)

### Yapılmayacaklar
- Büyük UI yeniden tasarım
- Admin/Dealer menü IA değişikliği (sadece izolasyon)
- Veri modeli refactor

### Placeholder standardı
- Portal içi eksik sayfalar “Yakında” standardına uygun placeholder olacak.

## Kabul kriteri (özet)
- Wrong role’da ilgili chunk indirilmez
- Admin shell leakage = blocker
