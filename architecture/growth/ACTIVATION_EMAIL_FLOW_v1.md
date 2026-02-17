# Activation Email Flow

## 1. Triggers & Templates

### 1.1. Welcome & Verify
*   **Trigger**: Signup.
*   **Subject**: "Hoş geldin! Hesabını doğrula."
*   **CTA**: Verify Email.

### 1.2. Abandoned Draft Nudge
*   **Trigger**: Draft created > 24h ago AND not published.
*   **Subject**: "İlanın yarım kaldı 🧐"
*   **Body**: "Berlin'deki daire ilanını tamamlamak için tıkla."
*   **Deep Link**: `/account/listings/{id}/edit`.

### 1.3. First Lead Celebration
*   **Trigger**: First `listing_contact_clicked` or `message_received`.
*   **Subject**: "Tebrikler! İlanın ilgi görüyor 🚀"
*   **Body**: "Bir alıcı ilanını inceledi. Cevap vermek için panele git."

## 2. Infrastructure
*   **Provider**: AWS SES / SendGrid (Mock for MVP).
*   **Worker**: Background job checking `listings` and `user_interactions`.
