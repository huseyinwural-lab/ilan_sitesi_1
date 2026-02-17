# P26: Messaging Core Architecture (Schema V1)

## 1. Overview
The messaging system enables direct communication between Buyers and Sellers, scoped to a specific Listing.

## 2. Database Schema

### 2.1. Table: `conversations`
Represents a thread between two users regarding a specific item.

| Column | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | Unique ID |
| `listing_id` | UUID | Index | The item being discussed |
| `buyer_id` | UUID | Index | User starting the chat |
| `seller_id` | UUID | Index | Owner of the item |
| `status` | String | - | `active`, `archived`, `blocked` |
| `last_message_at` | DateTime | Index | For sorting inbox |
| `created_at` | DateTime | - | - |

**Unique Constraint**: `(listing_id, buyer_id)` - A buyer can only have one active conversation per listing.

### 2.2. Table: `messages`
Individual text payloads within a conversation.

| Column | Type | Index | Description |
| :--- | :--- | :--- | :--- |
| `id` | UUID | PK | - |
| `conversation_id` | UUID | FK | Parent thread |
| `sender_id` | UUID | - | Who wrote this |
| `body` | Text | - | Content (Encrypted/Plain based on policy) |
| `is_read` | Boolean | - | Read receipt status |
| `created_at` | DateTime | Index | Ordering |

## 3. Query Strategy
*   **Inbox Query**: `SELECT * FROM conversations WHERE (buyer_id = :me OR seller_id = :me) ORDER BY last_message_at DESC`
*   **Thread Query**: `SELECT * FROM messages WHERE conversation_id = :id ORDER BY created_at ASC`

## 4. Abuse Guard (V1)
*   **Rate Limit**: Max 5 new conversations per hour for new users.
*   **Block**: If `status == 'blocked'`, no new messages allowed.
