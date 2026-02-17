# P26: Realtime & Delivery Architecture

## 1. Transport Strategy
For the MVP of P26, we will use **Short Polling** (Interval: 10s) to reduce operational complexity (WebSocket servers require persistent connections and scaling challenges).

*   **Future (v2)**: WebSocket (Socket.io) or Server-Sent Events (SSE).
*   **Current (v1)**: `GET /messages/sync?after={timestamp}`.

## 2. Notification Counter Policy (Unread Badges)
To keep the "Inbox" badge accurate without heavy DB queries:

### 2.1. Redis Counter
*   Key: `unread:user:{user_id}`
*   Type: Integer
*   Action:
    *   **New Message**: `INCR unread:user:{recipient_id}`
    *   **Read Inbox**: `SET unread:user:{user_id} 0` (or decrement per thread)

### 2.2. Database Fallback
If Redis is lost, we count: `SELECT COUNT(*) FROM messages WHERE conversation_id IN (my_conversations) AND is_read = FALSE AND sender_id != :me`.

## 3. Push Integration
*   **Trigger**: `MessagingService.send_message`
*   **Action**:
    1.  Lookup `UserDevice` for recipient.
    2.  Send FCM Push.
    3.  Payload:
        ```json
        {
          "title": "Yeni Mesaj",
          "body": "Ahmet: Fiyat son ne olur?",
          "data": {
            "type": "chat",
            "conversation_id": "uuid"
          }
        }
        ```
