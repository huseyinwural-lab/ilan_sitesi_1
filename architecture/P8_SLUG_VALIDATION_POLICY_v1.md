# P8 Slug Validation & Canonical Policy

**Document ID:** P8_SLUG_VALIDATION_POLICY_v1  
**Date:** 2026-02-13  
**Status:** 🔒 APPROVED  

---

## 1. Problem Statement
URLs contain a descriptive slug for SEO (e.g., `/ilan/temiz-bmw-320i-uuid`). Since the listing title can change, the slug in the URL might become outdated. Accessing a listing with an old slug should not duplicate content (split SEO authority) or 404.

## 2. Policy

### 2.1. ID Authority
The **UUID** at the end of the URL is the single source of truth.
Format: `...-{uuid}` (Last 36 characters).

### 2.2. Canonical Redirect (301 behavior)
If the URL slug does not match the current canonical slug from the API:
- **Action:** Client-side redirect (using `navigate(..., { replace: true })`).
- **Effect:** Browser history is updated, URL bar reflects the correct slug.
- **SEO Benefit:** Search engines see the canonical link tag and eventually update their index.

**Example:**
- Request: `/ilan/old-title-12345`
- API Return: Slug = `new-title`
- Action: Redirect to `/ilan/new-title-12345`

### 2.3. 404 Not Found
If the UUID does not exist in the database:
- **Action:** Render 404 Component.
- **Status:** HTTP 404 (via SSR or status code simulation in CSR).

### 2.4. 410 Gone (Inactive)
If the UUID exists but `status != active`:
- **Current MVP:** Allow viewing but show "Sold/Inactive" banner (or just render if API allows).
- **Future:** Return specific 410 UI blocking interaction.

---

## 3. Implementation Verification
- **Test:** Open a valid listing, change the slug part of the URL manually, press Enter.
- **Expected:** Page loads, then URL immediately updates to the correct slug without reloading the page content (React Router replace).
