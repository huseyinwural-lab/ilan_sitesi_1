const { test, expect } = require('@playwright/test');

test('country compare filters and sorting', async ({ page }) => {
  await page.goto('/admin/login');
  await page.getByTestId('login-email').fill('admin@platform.com');
  await page.getByTestId('login-password').fill('Admin123!');
  await page.getByTestId('login-submit').click();

  await page.goto('/admin/country-compare');
  await expect(page.getByTestId('admin-country-compare-page')).toBeVisible({ timeout: 60000 });

  await page.getByTestId('country-compare-period-select').selectOption('7d');
  await expect(page.getByTestId('country-compare-period-label')).toContainText('Son 7 Gün');

  await page.getByTestId('country-compare-sort-select').selectOption('growth_total_listings_7d');
  await page.getByTestId('country-compare-sort-direction').click();

  await expect(page.getByTestId('country-compare-table')).toBeVisible();
});

test('country compare revenue visibility for super admin', async ({ page }) => {
  await page.goto('/admin/login');
  await page.getByTestId('login-email').fill('admin@platform.com');
  await page.getByTestId('login-password').fill('Admin123!');
  await page.getByTestId('login-submit').click();

  await page.goto('/admin/country-compare');
  await expect(page.getByTestId('admin-country-compare-page')).toBeVisible({ timeout: 60000 });
  await expect(page.getByTestId('country-compare-header-revenue')).toBeVisible();
});
