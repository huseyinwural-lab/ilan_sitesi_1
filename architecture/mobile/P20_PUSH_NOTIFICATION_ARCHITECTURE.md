# P20: Push Notification Architecture

## 1. Overview
We will use **Firebase Cloud Messaging (FCM)** as the cross-platform delivery service for iOS and Android.

## 2. Device Token Model
We need to store the mapping between `User` and `FCM Token`.

### 2.1. Schema: `user_devices`
| Column | Type | Notes |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `user_id` | UUID | FK -> Users |
| `token` | String | FCM Token (Unique) |
| `platform` | String | 'ios', 'android' |
| `device_id` | String | Hardware ID (for replacing old tokens) |
| `last_active_at` | DateTime | For cleanup |

## 3. Push Event Map (MVP)
Events that trigger a push notification:

| Event | Title Template | Body Template | Deep Link |
| :--- | :--- | :--- | :--- |
| **Price Drop** | Fiyat Düştü! 📉 | {listing_title} ilanının fiyatı {old} -> {new} oldu. | `/listing/{id}` |
| **New Message** | Yeni Mesaj 💬 | {sender_name}: {message_preview} | `/chat/{id}` |
| **Listing Status** | İlanın Yayında ✅ | {listing_title} artık yayında. | `/listing/{id}` |
| **Referral** | Tebrikler! 🎉 | Arkadaşın kayıt oldu. Kazancın hesabına eklendi. | `/affiliate` |

## 4. Sending Strategy
*   **Transactional**: Triggered immediately by backend events (e.g., `listing.update`).
*   **Batching**: Not needed for MVP, direct send via FCM API.
*   **Mocking**: For dev/test, we will log the notification to `stdout` instead of calling real FCM.

## 5. Token Management
*   **On Login**: Register/Update token.
*   **On Logout**: Delete token from DB to prevent sending pushes to wrong user.
*   **On Token Refresh**: Mobile app listens to FCM token refresh and updates backend.
