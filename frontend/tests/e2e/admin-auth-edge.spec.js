const { test, expect } = require('@playwright/test');

const adminCreds = { email: 'admin@platform.com', password: 'Admin123!' };

const loginAdmin = async (page) => {
  await page.goto('/admin/login');
  await page.getByTestId('login-email').fill(adminCreds.email);
  await page.getByTestId('login-password').fill(adminCreds.password);
  await page.getByTestId('login-submit').click();
};

test('FAZ-7 auth edge: expired token health-check', async ({ page }) => {
  await page.route('**/api/admin/session/health', (route) => {
    route.fulfill({
      status: 401,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'expired' }),
    });
  });

  const healthResponsePromise = page.waitForResponse((res) => (
    res.url().includes('/api/admin/session/health') && res.status() === 401
  ));

  await loginAdmin(page);
  await healthResponsePromise;

  await expect(page).toHaveURL(/\/admin\/login/);
  await expect(page.getByTestId('login-email')).toBeVisible({ timeout: 60000 });
});

test('FAZ-7 auth edge: multi-tab logout sync', async ({ browser }) => {
  const context = await browser.newContext();
  const page1 = await context.newPage();
  await loginAdmin(page1);

  await page1.goto('/admin/categories');
  await expect(page1.getByTestId('categories-page')).toBeVisible({ timeout: 60000 });

  const page2 = await context.newPage();
  await page2.goto('/admin/categories');
  await expect(page2.getByTestId('categories-page')).toBeVisible({ timeout: 60000 });

  await page1.getByTestId('logout-btn').click();
  await expect(page2.getByTestId('login-email')).toBeVisible({ timeout: 15000 });

  await context.close();
});
