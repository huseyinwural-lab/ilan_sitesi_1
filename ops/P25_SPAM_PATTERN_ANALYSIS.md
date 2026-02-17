# P25: Spam Pattern Analysis

## 1. Content Spam
*   **Duplicate Titles**: "Satılık Daire", "Satılık Daire", "Satılık Daire".
*   **Gibberish**: "asdfghjkl".
*   **Link Spam**: Descriptions containing `http://...`.

## 2. Behavioral Spam
*   **Message Blast**: Copy-pasting same message to > 10 sellers.
*   **Listing Blast**: Creating 50 listings in 1 hour.

## 3. Detection (SQL Rules)
*   `SELECT user_id, COUNT(*) FROM listings WHERE created_at > NOW() - INTERVAL '1 hour' GROUP BY user_id HAVING COUNT(*) > 10`
*   `SELECT sender_id, COUNT(DISTINCT listing_id) FROM messages WHERE body = :last_body`
