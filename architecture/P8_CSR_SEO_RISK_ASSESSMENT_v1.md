# P8 CSR SEO Risk Assessment

**Document ID:** P8_CSR_SEO_RISK_ASSESSMENT_v1  
**Date:** 2026-02-13  
**Status:** 🔒 APPROVED  

---

## 1. Executive Summary
We have chosen **Client-Side Rendering (CSR)** with `react-helmet-async` for the Public Detail Page. This document assesses the SEO risks associated with this architecture compared to Server-Side Rendering (SSR).

## 2. Risk Matrix

| Risk Factor | Impact | Probability | Mitigation Strategy |
|---|---|---|---|
| **Google Indexing** | Low | Low | Googlebot has rendered JS reliably since ~2019. `react-helmet` updates tags after mount. |
| **Social Sharing (OG Tags)** | High | Medium | Facebook/Twitter scrapers have limited JS execution capabilities. They might see the default `index.html` title/image instead of the dynamic listing data. |
| **Crawl Budget** | Medium | Low | JS rendering consumes more crawl budget. For 10k-50k pages, this is manageable. |
| **TTFB / Core Web Vitals** | Medium | Medium | CSR has slower First Contentful Paint (FCP) than SSR. We use skeleton loaders to improve perceived performance. |

## 3. Detailed Analysis

### 3.1. Social Scrapers
- **Problem:** When a user shares a link on WhatsApp or iMessage, the preview might show "Admin Panel" (default title) instead of "BMW 320i - 1.250.000 TL".
- **Workaround:** We can set a generic but appealing default meta tag set in `index.html` (e.g., "Turkey's Leading Classifieds Platform").
- **Solution (Post-MVP):** Implement a lightweight Node.js middleware (or Edge Function) that detects user-agents (`facebookexternalhit`, `twitterbot`) and serves a static HTML with meta tags pre-injected, while serving the React app to regular users.

### 3.2. Googlebot Behavior
- Google waits for the "load" event and network idle.
- Our `DetailPage` fetches data in `useEffect`. If the API is slow (>5s), Googlebot might timeout.
- **Requirement:** API p95 latency must be < 200ms to ensure reliable indexing.

## 4. Conclusion
The CSR approach is **acceptable for P8/Public Beta** to prioritize feature velocity.
**Trigger for Change:** If organic traffic is significantly lower than expected or social sharing preview complaints arise, we will implement **Dynamic Rendering (Prerendering)** for bots in P9.
