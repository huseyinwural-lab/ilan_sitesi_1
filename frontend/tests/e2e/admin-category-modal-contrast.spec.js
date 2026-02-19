const { test, expect } = require('@playwright/test');

test('admin category modal contrast', async ({ page }) => {
  await page.goto('/admin/login');
  await page.getByTestId('login-email').fill('admin@platform.com');
  await page.getByTestId('login-password').fill('Admin123!');
  await page.getByTestId('login-submit').click();

  await expect(page.getByTestId('nav-catalog-categories')).toBeVisible({ timeout: 60000 });
  await page.getByTestId('nav-catalog-categories').click();
  await expect(page.getByTestId('categories-page')).toBeVisible({ timeout: 30000 });
  await page.getByTestId('categories-create-open').click();
  await expect(page.getByTestId('categories-modal')).toBeVisible({ timeout: 30000 });

  const textColor = await page.getByTestId('categories-name-input').evaluate(el => getComputedStyle(el).color);
  const placeholderColor = await page.getByTestId('categories-name-input').evaluate(el => getComputedStyle(el, '::placeholder').color);
  const modalBg = await page.getByTestId('categories-modal').evaluate(el => getComputedStyle(el.firstElementChild).backgroundColor);

  expect(textColor).toBe('rgb(15, 23, 42)');
  expect(placeholderColor).toBe('rgb(71, 85, 105)');
  expect(modalBg).toBe('rgb(255, 255, 255)');

  await expect(page.getByTestId('categories-modal')).toHaveScreenshot('category-modal-contrast.png');
});