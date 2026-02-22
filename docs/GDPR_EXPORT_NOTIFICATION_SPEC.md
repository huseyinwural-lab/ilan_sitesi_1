# GDPR_EXPORT_NOTIFICATION_SPEC

## Amaç
GDPR data export sonrası kullanıcıya kanıtlanabilir güvenlik bildirimi.

## Davranış
- Export tamamlanınca `gdpr_export_completed` audit log.
- In-app notification oluşturulur (severity: warning).
- Notification log: `gdpr_export_notification_sent`.

## Bildirim Metni
"Veri dışa aktarma tamamlandı. Hesabınızdan bir veri erişimi gerçekleşti."

## Kanal
- **In-app** (SendGrid gelince email genişletilecek)

## UI
- Notifications ekranında görünür.
