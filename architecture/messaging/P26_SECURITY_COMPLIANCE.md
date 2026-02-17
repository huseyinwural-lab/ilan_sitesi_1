# P26: Security & Compliance (Messaging)

## 1. Retention Policy
To minimize liability and storage costs:
*   **Active Messages**: Stored for 180 days.
*   **Archived Messages**: Stored for 365 days (Cold storage).
*   **Deleted Messages**: Soft delete immediately, Hard delete after 30 days.

## 2. Encryption Strategy (V1 - Server Side)
*   **Transit**: TLS 1.2+ (Standard).
*   **At Rest**: Database volume encryption (AWS EBS / Kubernetes Storage Class).
*   **Application Level**: Not implemented for MVP (Searchability required for Moderation).

## 3. GDPR Data Export
Users have the right to download their chat history.
*   **Endpoint**: `GET /messages/export`.
*   **Format**: JSON.
*   **Scope**: All messages where `sender_id` or `recipient_id` matches User.
