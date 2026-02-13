# P8 Rendering Strategy Decision

**Document ID:** P8_RENDERING_STRATEGY_DECISION_v1  
**Date:** 2026-02-13  
**Status:** 🔒 APPROVED  

---

## 1. Decision
**Strategy:** Client-Side Rendering (CSR) with Dynamic Meta Tags.  
**Tools:** React (SPA) + `react-helmet-async`.

---

## 2. Rationale

### 2.1. Why not SSR (Next.js)?
- **Complexity:** Migrating the current `create-react-app` based SPA to Next.js is a significant architectural change (routing, data fetching, build pipeline).
- **Time-to-Market:** Focus is on functionality (Search, Detail, SEO Basics).
- **Infrastructure:** Current setup (Nginx + Static Build) is simple and cost-effective.

### 2.2. Is CSR enough for SEO?
- **Googlebot:** Can render and index JavaScript-heavy sites effectively in 2026.
- **Dynamic Tags:** `react-helmet-async` injects title/meta tags into the DOM at runtime, which crawlers can read.
- **Trade-off:** First contentful paint (FCP) might be slower than SSR, and some niche crawlers (e.g., older social scrapers) might miss meta tags without a prerender service (like Prerender.io). However, for MVP, this is acceptable.

---

## 3. Implementation Plan
1. Install `react-helmet-async`.
2. Wrap App in `HelmetProvider`.
3. Create generic `SEO` component.
4. Implement in `SearchPage` (dynamic title) and `DetailPage` (full schema).

---

## 4. Future Roadmap
- **Phase P9+:** Evaluate migrating to Next.js or implementing Pre-rendering if SEO performance lags.
