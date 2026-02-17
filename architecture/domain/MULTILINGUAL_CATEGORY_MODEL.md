# Multilingual Category Model

## 1. Schema
The `Category` and `Attribute` tables already support JSONB for names.

## 2. API Contract
*   **Header**: `Accept-Language: de`
*   **Response**:
    ```json
    {
      "id": "...",
      "name": "Haus", // Localized
      "slug": "house" // Canonical
    }
    ```

## 3. Middleware
`LocaleMiddleware` extracts language from Header or URL prefix.
