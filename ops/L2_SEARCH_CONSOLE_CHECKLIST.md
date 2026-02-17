# Search Console Checklist (L2)

## 1. Domain Verification
- [ ] Verify ownership via DNS TXT record.
- [ ] Add both `https://platform.com` and `https://www.platform.com`.

## 2. International Targeting
- [ ] Check "International Targeting" report.
- [ ] Verify `hreflang` tags on `/de/` and `/tr/` pages.
    *   Expected: `de-DE` -> Germany
    *   Expected: `tr-TR` -> Turkey

## 3. Sitemap
- [ ] Submit `sitemap-index.xml`.
- [ ] Verify `sitemap-de.xml` processed > 0 URLs.
- [ ] Check for "Coverage" errors (404s, 500s).

## 4. Core Web Vitals
- [ ] Check Mobile Usability report.
- [ ] LCP < 2.5s (Green).
- [ ] CLS < 0.1 (Green).
