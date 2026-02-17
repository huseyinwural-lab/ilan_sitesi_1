# PORTAL_SPLIT_V1_APPROACH_DECISION

## Karar
**Yaklaşım (A): Route-based lazy loading + chunk split (CRA + CRACO).**

## Gerekçe
- Mevcut frontend altyapısı **CRA + CRACO**.
- Multi-entry (multi-page) yapılandırması CRA’da mümkün olsa da deploy/fallback karmaşıklığı yüksek.
- Bu fazın hedefi olan **“admin shell leakage = 0”** gereksinimi;
  - doğru **pre-layout guard** +
  - doğru **import boundary** +
  - doğru **lazy chunk split**
  ile düşük riskle karşılanabilir.

## Kapsam Notu
- Bu faz **mimari ayrıştırma** fazıdır: “no-refactor” kuralı geçersiz.
- Ancak multi-entry HTML (B) bu faz kapsamı dışıdır.

## Ölçülebilir Kabul Kriterleri (özet)
- `/admin/*` portal kodu ayrı chunk olarak yalnız admin portalına girince yüklenir.
- `/dealer/*` portal kodu ayrı chunk olarak yalnız dealer portalına girince yüklenir.
- Yanlış rolde bu chunk’lar **indirilmeyecek** (network kanıtı).
- Admin layout/shell DOM’a **hiç mount olmayacak** (pre-layout guard).
