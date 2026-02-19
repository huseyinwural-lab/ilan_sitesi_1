## P1 — Admin Header Health Badge

**Özet:** Admin header’da oturum sağlık durumu (session health) ve token süresini gösteren küçük bir badge.

### Kapsam
- Health-check sonucu (OK / Expired) görsel gösterim
- İsteğe bağlı: kalan süre (expires_at - server_time)
- RBAC: sadece admin rolleri

### Kabul Kriteri
- Sağlık durumu değiştiğinde badge güncellenir
- Token süresi dolduğunda otomatik logout tetiklenir