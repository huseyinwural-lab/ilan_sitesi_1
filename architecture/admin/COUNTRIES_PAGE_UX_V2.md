# COUNTRIES_PAGE_UX_V2

## Amaç
Countries sayfasını “card grid” görünümünden çıkarıp operasyonel bir **yönetim ekranına** dönüştürmek.

## Değişiklikler
- Card → table/list yönetim görünümü
- Enabled toggle switch
- “Edit” CTA
- Sadece 4–5 kritik alan görünür:
  - Country code
  - Name
  - Enabled
  - Default currency
  - Default language
- Detay alanlar drawer/modal:
  - Date format, number format
  - Units (distance/area/weight)
  - Support email vb.

## Kullanıcı Akışı
- Toggle ile enable/disable hızlı aksiyon
- Edit ile detay drawer açılır → kaydet

## Kabul Notu
- Toggle aksiyonu anında PATCH çağırır ve listeyi günceller.
