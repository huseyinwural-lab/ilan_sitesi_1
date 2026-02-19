## FAZ-7 Admin Login E2E Smoke

- **Test dosyası:** `/app/frontend/tests/e2e/admin-login.spec.js`
- **Playwright config:** `/app/frontend/playwright.config.js`
- **Çalıştırma:** `PLAYWRIGHT_BASE_URL=<preview-url> npx playwright test`

### Adımlar
1) /admin/login → admin giriş
2) Dashboard render
3) Kategoriler sayfası route doğrulaması

### Kabul Kriteri
- Login → Dashboard → Kategoriler akışı PASS