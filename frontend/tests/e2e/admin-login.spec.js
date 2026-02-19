const { test, expect } = require('@playwright/test');

test('admin login smoke: dashboard -> categories', async ({ page }) => {
  await page.goto('/admin/login');
  await page.getByTestId('login-email').fill('admin@platform.com');
  await page.getByTestId('login-password').fill('Admin123!');
  await page.getByTestId('login-submit').click();

  await expect(page.getByTestId('admin-session-loading')).toBeVisible();
  await expect(page.getByTestId('nav-catalog-categories')).toBeVisible({ timeout: 60000 });

  await page.getByTestId('nav-catalog-categories').click();
  await expect(page.getByTestId('categories-page')).toBeVisible({ timeout: 30000 });
});