# ADMIN_COUNTRY_PARAM_VALIDATION_POLICY

## Genel Kurallar
- `country` paramı **ülke code** olmalıdır (örn: `DE`).
- Backend doğrulaması zorunludur.

## Mode Kuralları
- Global mode: `country` paramı yok.
- Country mode: `country` paramı var.

## Validation
- Country mode’da:
  - `country` yoksa: UI redirect (son seçilen ülkeye)
  - `country` geçersizse: backend `400 Invalid country parameter`

## Redirect Fallback
- Country param silinirse:
  - Country mode’da: `?country=last_selected_country` ile zorunlu redirect
  - last_selected yoksa: ülke seçimi akışı (modal/sayfa)

## Disabled Country (MVP)
- Bu iterasyonda disabled country erişimi **admin için serbest** bırakılır.
- Eğer istenirse sonraki iterasyonda disabled => 403 yapılabilir.
