# P1 Security UI Checklist

## CSP Header
- Endpoint: `/api/health/db`
- Header: `Content-Security-Policy: default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'`

## XSS Sanitize (Rich Text)
- /bilgi/:slug içeriği `whitespace-pre-line` ile düz metin render eder.
- HTML injection render edilmez (React escapes).

## Upload MIME  Size Limit
- Test: `/admin/site/header/logo` için `.txt` upload
- Sonuç: **400** `Unsupported image type`

## Public Asset Path Traversal
- Test: `/api/site/assets/../../etc/passwd`
- Sonuç: **404** (path normalization engeli)

## Notlar
- Header logo upload: PNG/SVG only + 2MB limit.
