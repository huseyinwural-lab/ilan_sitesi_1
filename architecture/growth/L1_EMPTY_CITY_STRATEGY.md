# FAZ-L1: Empty City Strategy

## 1. Problem
Landing pages with 0 results bounce users and hurt SEO.

## 2. Rules

### 2.1. Indexing (Robots)
*   **City with > 10 Listings**: `index, follow`.
*   **City with 1-9 Listings**: `noindex, follow` (Crawl links but don't index page).
*   **City with 0 Listings**: Returns 404 or Redirect to Region/Country page.

### 2.2. User Experience
If a user searches for "Bonn" (0 results):
1.  **Message**: "No listings in Bonn yet."
2.  **Fallback**: "Here are listings in **North Rhine-Westphalia** (Region) instead."
3.  **Action**: "Notify me when listings appear in Bonn."

## 3. Implementation
*   **SEO Routes**: Check counts before rendering metadata.
*   **Search API**: Logic to expand radius automatically if 0 results? -> Deferred to V2.
