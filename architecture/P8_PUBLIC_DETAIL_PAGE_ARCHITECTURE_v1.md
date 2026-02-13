# P8 Public Detail Page Architecture

**Document ID:** P8_PUBLIC_DETAIL_PAGE_ARCHITECTURE_v1  
**Date:** 2026-02-13  
**Status:** 🚀 KICKOFF  

---

## 1. Route Standard
Standardized URL structure for SEO and User Experience.

**Pattern:** `/ilan/{slug}-{id}`  
**Example:** `/ilan/sahibinden-temiz-bmw-320i-2023-f34a1b`

- **Slug:** Normalized title (lowercase, dash-separated, tr-chars converted).
- **ID:** Last segment, UUID or ShortID (we use UUID, maybe allow short hash matching).
- **Redirect:** If slug changes but ID matches -> 301 Redirect to canonical slug.

---

## 2. Page Components

### 2.1. Hero Section
- **Gallery:** Image slider (desktop: grid + modal, mobile: swipe).
- **Key Info:** Title, Price, Currency, Date, Location.
- **Actions:** Call/Message (Sticky on mobile), Favorite, Share.

### 2.2. Details Tab/Grid
- **Description:** HTML/Markdown rendered content.
- **Attributes:** Grouped by category (e.g., "Engine", "Interior").
- **MDM Data:** Clickable Make/Model links (Internal linking).

### 2.3. Sidebar / Sticky (Desktop)
- **Seller Card:** Name, Role (Dealer/Owner), Contact Button.
- **Safety Tips:** Static warning block.

---

## 3. Error Handling

### 3.1. 404 Not Found
- Case: ID does not exist in DB.
- Action: Render friendly 404 page + "Similar Listings" widget.
- HTTP Status: 404.

### 3.2. 410 Gone (Expired/Sold)
- Case: ID exists but `status != active`.
- Action: 
  - Render "This listing is no longer active" banner.
  - Show limited listing details (Title, Image).
  - Show "Similar Listings" prominently.
- HTTP Status: 410 (Tells Google to de-index).

---

## 4. Localization
- **Labels:** All attribute keys/values translated via FE dictionary or API response.
- **Currency:** Formatted per locale.
- **Date:** Relative (e.g., "2 days ago") for recent, absolute for older.

---

## 5. Security Guardrails
- **XSS:** Sanitize description HTML.
- **Contact:** Hide phone number behind "Show Number" click (Click tracking).
