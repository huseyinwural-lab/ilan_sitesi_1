# P20: Offline & Caching Policy

## 1. Strategy: "Stale-While-Revalidate"
The app should feel instant. We show cached data immediately, then fetch fresh data in background.

## 2. HTTP Cache Headers
The Backend will send standard `Cache-Control` headers to guide the Mobile Networking client (Dio/Http).

| Endpoint | Header | Rationale |
| :--- | :--- | :--- |
| `/feed` | `max-age=60` | Feeds change often, but 1 min staleness is acceptable. |
| `/listing/{id}` | `max-age=300` | Listing details change rarely. 5 min cache. |
| `/static/config` | `max-age=86400` | Countries/Categories change daily. |

## 3. Local Persistence (App Side)
*   **Technology**: Hive (NoSQL).
*   **Scope**:
    *   **Home Feed**: Cache first page (20 items).
    *   **Listing Detail**: Cache visited items (LRU, max 50).
    *   **Favorites**: Always offline accessible.

## 4. Offline Actions
Since "Post Ad" is out of scope, the only write action is **"Add to Favorite"**.
*   **Queue**: Optimistic UI update -> Add request to "Sync Queue" -> Retry when online.
