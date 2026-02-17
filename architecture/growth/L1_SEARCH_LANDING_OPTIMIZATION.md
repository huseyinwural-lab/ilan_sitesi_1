# FAZ-L1: Search Landing Optimization

## 1. Objective
Turn organic/direct traffic into "engaged users" (Clicking a listing).

## 2. Page Components

### 2.1. Hero Section (SEO Landing)
*   **Dynamic Header**: "Apartments for Sale in Berlin" (Matches Search Query).
*   **Sub-header**: "Browse 450 verified listings from trusted dealers."
*   **Search Bar**: Prominent, pre-filled with current location context.

### 2.2. Trust Signals (Sidebar/Header)
*   **Badge**: "Verified Platform" (Generic trust seal).
*   **Stats**: "120 New Listings Today".
*   **Testimonial**: Simple quote from a user/dealer (Static).

### 2.3. Listing Card Optimization
*   **Primary CTA**: Price (Large Font).
*   **Secondary CTA**: "View Details" button (explicit, not just clickable card).
*   **Premium Highlight**: Gold border for sponsored items.

### 2.4. Empty State Handling (See Empty City Strategy)
*   If < 5 results: Show "Nearby" listings automatically.
*   If 0 results: Show "Alert me" form.

## 3. Implementation
*   Updates apply to `SearchPage.js` and `seo_routes.py` (metadata).
