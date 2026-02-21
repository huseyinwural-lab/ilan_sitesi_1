# VERIFICATION_TOKEN_RETENTION_POLICY

## Amaç
Email verification token tablosunun büyümesini kontrol altında tutmak ve replay riskini azaltmak.

## Kural (ADR-FINAL-11)
- **expired + consumed** → 24 saat sonra sil
- **expired + not consumed** → 7 gün sonra sil (kısa audit amaçlı tutulur)

## Kapsam
- `email_verification_tokens`
- Token tek kullanımlık, TTL=15 dk, consumed_at zorunlu.

## Güvenlik Notu
- Cleanup sonrası replay mümkün olmamalı.
- Silme işlemi yalnızca expired kayıtları kapsar.
