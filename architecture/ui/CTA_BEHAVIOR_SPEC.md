# Primary CTA Davranış Şeması (UH1.2)

## CTA: “Hemen İlan Ver”
- **Normal:** aktif CTA
- **Quota dolu:** disabled + açıklama
- **Quota verisi yok:** 0 + “Veri hazırlanıyor” etiketi (buton aktif kalır)

## Quota Bilgisi
CTA altında görünür:
- “Kalan ücretsiz ilan hakkı: X”
- API yoksa `X=0` + “Veri hazırlanıyor” state
