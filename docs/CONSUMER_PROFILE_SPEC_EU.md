# CONSUMER_PROFILE_SPEC_EU

## Amaç
GDPR uyumlu profil yönetimi.

## Alanlar
- Profil fotoğrafı (max 4MB, mime kontrol, EXIF temizleme)
- Ad / Soyad
- Görünen ad (display_name)
- Dil tercihi (de, fr, nl, it, en)
- Ülke seçimi (tek domain, çok ülke)

## Bileşenler
- Avatar upload + crop
- Profil formu
- Dil/ülke dropdown

## Empty state
- Profil fotoğrafı yok → placeholder avatar.

## Success/Error
- Save success toast
- Invalid mime/size → inline error

## RBAC
- consumer

## GDPR Notu
- Veri minimizasyonu; sadece zorunlu alanlar.
