const { test, expect } = require('@playwright/test');

const adminCreds = { email: 'admin@platform.com', password: 'Admin123!' };

const loginAdmin = async (page) => {
  await page.goto('/admin/login');
  await page.getByTestId('login-email').fill(adminCreds.email);
  await page.getByTestId('login-password').fill(adminCreds.password);
  await page.getByTestId('login-submit').click();
  await expect(page.getByTestId('nav-catalog-categories')).toBeVisible({ timeout: 60000 });
};

test('Dashboard smoke: cards + quick actions', async ({ page }) => {
  await loginAdmin(page);
  await page.goto('/admin');
  await expect(page.getByTestId('dashboard')).toBeVisible({ timeout: 60000 });

  await expect(page.getByTestId('dashboard-total-users-value')).toBeVisible();
  await expect(page.getByTestId('dashboard-active-countries-value')).toBeVisible();
  await expect(page.getByTestId('dashboard-active-modules-value')).toBeVisible();

  await page.getByTestId('quick-action-users').click();
  await expect(page.getByTestId('users-page')).toBeVisible({ timeout: 60000 });

  await page.goto('/admin');
  await page.getByTestId('quick-action-audit').click();
  await expect(page.getByTestId('audit-logs-page')).toBeVisible({ timeout: 60000 });
});
