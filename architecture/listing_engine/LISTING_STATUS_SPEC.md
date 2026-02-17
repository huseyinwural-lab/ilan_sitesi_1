# Listing Status Specification

## 1. Status Set (Enum)

| Status | Açıklama | Görünürlük |
| :--- | :--- | :--- |
| `DRAFT` | Kullanıcı henüz yayınlamadı. | Sadece Sahibi |
| `PENDING_MODERATION` | Yayına gönderildi, onay bekliyor. | Sahibi + Admin |
| `ACTIVE` | Yayında, herkes görebilir. | Public |
| `REJECTED` | Moderasyon reddetti. | Sahibi + Admin |
| `SUSPENDED` | Kural ihlali nedeniyle durduruldu. | Sahibi + Admin |
| `EXPIRED` | Süresi doldu (30 gün). | Sahibi |
| `SOLD` | Satıldı olarak işaretlendi. | Public (Arşiv) |
| `DELETED` | Soft delete (Çöp kutusu). | Admin (Audit) |

## 2. Kurallar
*   **Draft**: Zorunlu alanlar eksik olabilir.
*   **Active**: Zorunlu alanlar tam olmalı.
*   **Rejected**: Red nedeni (`rejected_reason`) dolu olmalı.
