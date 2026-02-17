# Vehicle Wizard v2 — Validation & Error Spec

## 1) Standard
- UI-side validation: anında hata, step ilerlemesini engeller (hard-block)
- Backend authoritative validation: publish sırasında kesin kontrol

## 2) i18n
- Hata mesajları i18n anahtarlarıyla tasarlanır.
- v2’de en az TR metinleri sağlanır.

## 3) Hata türleri
- Required field missing
- Invalid value format
- Make/model enforcement fail
- Photo quality policy fail

## 4) KM/Year sanity
- Anomali → warning + log (hard-block değil) (bkz sanity rules).
