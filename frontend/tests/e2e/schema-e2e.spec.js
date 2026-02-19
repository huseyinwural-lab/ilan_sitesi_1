const { test, expect } = require('@playwright/test');
const path = require('path');

const adminCreds = { email: 'admin@platform.com', password: 'Admin123!' };
const userCreds = { email: 'user@platform.com', password: 'User123!' };
const runId = Date.now();
const categoryName = `e2e-test-category-${runId}`;
const categorySlug = `e2e-test-category-${runId}`;
const dynamicKey = 'extra_option';
const detailGroupId = 'features';
const detailOptions = ['ABS', 'Airbag', 'Klima', 'ESP'];

const photoFiles = [
  path.join(__dirname, '../fixtures/photo1.jpg'),
  path.join(__dirname, '../fixtures/photo2.jpg'),
  path.join(__dirname, '../fixtures/photo3.jpg'),
];

let adminToken = "";

test.describe.serial('FAZ-8 Schema E2E', () => {
  test.beforeAll(async ({ request }) => {
    const loginRes = await request.post('/api/auth/login', { data: adminCreds });
    const loginData = await loginRes.json();
    adminToken = loginData.access_token;

    const listRes = await request.get('/api/admin/categories?country=DE', {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    if (!listRes.ok()) return;
    const listData = await listRes.json();
    const existing = (listData.items || []).find((item) => item.slug === categorySlug);
    if (existing) {
      await request.delete(`/api/admin/categories/${existing.id}`, {
        headers: { Authorization: `Bearer ${adminToken}` },
      });
    }
  });

  test('Senaryo 1: Kategori oluştur → publish', async ({ page, request }) => {
    await page.goto('/admin/login');
    await page.getByTestId('login-email').fill(adminCreds.email);
    await page.getByTestId('login-password').fill(adminCreds.password);
    await page.getByTestId('login-submit').click();

    await expect(page.getByTestId('nav-catalog-categories')).toBeVisible({ timeout: 60000 });
    await page.getByTestId('nav-catalog-categories').click();
    await expect(page.getByTestId('categories-page')).toBeVisible();

    await page.getByTestId('categories-create-open').click();
    await expect(page.getByTestId('category-hierarchy-step')).toBeVisible();

    await page.getByTestId('categories-name-input').fill(categoryName);
    await page.getByTestId('categories-slug-input').fill(categorySlug);
    await page.getByTestId('categories-country-input').fill('DE');
    await page.getByTestId('categories-step-next').click();

    await expect(page.getByTestId('categories-core-step')).toBeVisible({ timeout: 60000 });
    await page.getByTestId('categories-title-min').fill('10');
    await page.getByTestId('categories-title-max').fill('120');

    await page.getByTestId('categories-step-next').click();
    await expect(page.getByTestId('categories-dynamic-step')).toBeVisible();

    await page.getByTestId('categories-dynamic-draft-label').fill('Ekstra Seçim');
    await page.getByTestId('categories-dynamic-draft-key').fill(dynamicKey);
    await page.getByTestId('categories-dynamic-draft-options').fill('A, B');
    await page.getByTestId('categories-dynamic-draft-required-input').check();
    await page.getByTestId('categories-dynamic-next').click();

    await page.getByTestId('categories-step-next').click();
    await expect(page.getByTestId('categories-detail-step')).toBeVisible();

    await page.getByTestId('categories-detail-draft-title').fill('Donanım');
    await page.getByTestId('categories-detail-draft-key').fill(detailGroupId);
    await page.getByTestId('categories-detail-draft-required-input').check();

    for (const option of detailOptions) {
      await page.getByTestId('categories-detail-option-input').fill(option);
      await page.getByTestId('categories-detail-option-add').click();
    }

    await page.getByTestId('categories-detail-next').click();

    await page.getByTestId('categories-step-next').click();
    await expect(page.getByTestId('categories-modules-step')).toBeVisible();

    const contactToggle = page.getByTestId('categories-module-contact');
    if (await contactToggle.isChecked()) {
      await contactToggle.click();
    }
    const paymentToggle = page.getByTestId('categories-module-payment');
    if (await paymentToggle.isChecked()) {
      await paymentToggle.click();
    }

    await page.getByTestId('categories-photos-max').fill('12');

    await page.getByTestId('categories-step-next').click();
    await expect(page.getByTestId('categories-preview-step')).toBeVisible();

    await expect(page.getByTestId('categories-publish')).toBeDisabled();
    await page.getByTestId('categories-preview-confirm').click();
    await expect(page.getByTestId('categories-preview-ready')).toBeVisible();

    const draftResponsePromise = page.waitForResponse((res) => (
      res.url().includes('/api/admin/categories') &&
      ['POST', 'PATCH'].includes(res.request().method()) &&
      res.status() >= 200 && res.status() < 300
    ));
    await page.getByTestId('categories-save-draft').click();
    const draftResponse = await draftResponsePromise;
    const draftData = await draftResponse.json();
    expect(draftData.category.form_schema.status).toBe('draft');

    await expect(page.getByTestId('categories-page')).toBeVisible({ timeout: 60000 });

    const listRes = await request.get('/api/admin/categories?country=DE', {
      headers: { Authorization: `Bearer ${adminToken}` },
    });
    expect(listRes.ok()).toBeTruthy();
    const listData = await listRes.json();
    const savedCategory = (listData.items || []).find((item) => item.slug === categorySlug);
    expect(savedCategory).toBeTruthy();
    expect(savedCategory.form_schema.status).toBe('draft');

    await page.getByTestId(`categories-edit-${savedCategory.id}`).click();
    await expect(page.getByTestId('categories-modal')).toBeVisible();
    await page.getByTestId('category-step-preview').click();
    await expect(page.getByTestId('categories-preview-step')).toBeVisible();
    await page.getByTestId('categories-preview-confirm').click();
    await expect(page.getByTestId('categories-publish')).toBeEnabled();

    const publishResponsePromise = page.waitForResponse((res) => (
      res.url().includes(`/api/admin/categories/${savedCategory.id}`) &&
      res.request().method() === 'PATCH' &&
      (res.request().postData() || '').includes('"status":"published"')
    ));
    await page.getByTestId('categories-publish').click();
    const publishResponse = await publishResponsePromise;
    const publishData = await publishResponse.json();
    expect(publishData.category.form_schema.status).toBe('published');

    await expect(page.getByTestId('categories-page')).toBeVisible({ timeout: 60000 });
    await expect(page.getByText(categorySlug)).toBeVisible({ timeout: 30000 });
  });

  test('Senaryo 2: Wizard step-2 validation tetikleme', async ({ page }) => {
    await page.goto('/login');
    await page.getByTestId('login-email').fill(userCreds.email);
    await page.getByTestId('login-password').fill(userCreds.password);
    await page.getByTestId('login-submit').click();

    await page.goto('/account/create/vehicle-wizard');
    await expect(page.getByTestId('listing-category-selector')).toBeVisible({ timeout: 60000 });

    await page.getByRole('button', { name: categoryName }).click();
    await page.getByRole('button', { name: `${categoryName} seç` }).click();

    await expect(page.getByTestId('listing-attributes-form')).toBeVisible({ timeout: 60000 });

    await page.getByTestId('listing-title-input').fill('E2E Test Başlık');
    await page.getByTestId('listing-description-textarea').fill('Bu açıklama FAZ-8 E2E test senaryosu için yeterince uzundur.');
    await page.getByTestId('listing-price-input').fill('15000');

    await page.getByTestId('listing-make-select').selectOption({ index: 1 });
    await page.getByTestId('listing-model-select').selectOption({ index: 1 });
    await page.getByTestId('listing-year-input').fill('2022');
    await page.getByTestId('listing-mileage-input').fill('5000');
    await page.getByTestId('listing-fuel-select').selectOption({ index: 1 });
    await page.getByTestId('listing-transmission-select').selectOption({ index: 1 });
    await page.getByTestId('listing-condition-select').selectOption({ index: 1 });

    await page.getByTestId('listing-attributes-submit').click();
    await expect(page.getByTestId(`listing-dynamic-error-${dynamicKey}`)).toBeVisible({ timeout: 30000 });
  });

  test('Senaryo 3: Listing detail modül görünürlüğü', async ({ page }) => {
    await page.goto('/login');
    await page.getByTestId('login-email').fill(userCreds.email);
    await page.getByTestId('login-password').fill(userCreds.password);
    await page.getByTestId('login-submit').click();

    await page.goto('/account/create/vehicle-wizard');
    await expect(page.getByTestId('listing-category-selector')).toBeVisible({ timeout: 60000 });

    await page.getByRole('button', { name: categoryName }).click();
    await page.getByRole('button', { name: `${categoryName} seç` }).click();

    await expect(page.getByTestId('listing-attributes-form')).toBeVisible({ timeout: 60000 });

    await page.getByTestId('listing-title-input').fill('E2E Detay Başlık');
    await page.getByTestId('listing-description-textarea').fill('Bu açıklama FAZ-8 senaryosu için yeterince uzundur ve yayınlama içindir.');
    await page.getByTestId('listing-price-input').fill('22000');

    await page.getByTestId('listing-make-select').selectOption({ index: 1 });
    await page.getByTestId('listing-model-select').selectOption({ index: 1 });
    await page.getByTestId('listing-year-input').fill('2021');
    await page.getByTestId('listing-mileage-input').fill('9000');
    await page.getByTestId('listing-fuel-select').selectOption({ index: 1 });
    await page.getByTestId('listing-transmission-select').selectOption({ index: 1 });
    await page.getByTestId('listing-condition-select').selectOption({ index: 1 });

    await page.getByTestId(`listing-dynamic-select-${dynamicKey}`).selectOption({ index: 1 });
    await page.getByTestId(`listing-detail-group-summary-${detailGroupId}`).click();
    await page.getByTestId(`listing-detail-checkbox-${detailGroupId}-ABS`).check();

    await page.getByTestId('listing-attributes-submit').click();

    await expect(page.getByTestId('wizard-photo-input')).toBeVisible({ timeout: 60000 });
    await page.getByTestId('wizard-photo-input').setInputFiles(photoFiles);
    await page.getByTestId('wizard-photos-next').click();

    await expect(page.getByTestId('wizard-review')).toBeVisible({ timeout: 60000 });
    await page.getByTestId('wizard-publish').click();

    await page.waitForURL(/\/ilan\//, { timeout: 60000 });
    await expect(page.getByTestId('listing-photos-section')).toBeVisible({ timeout: 60000 });
    await expect(page.getByTestId('listing-address-section')).toBeVisible();
    await expect(page.locator('[data-testid="listing-contact-section"]')).toHaveCount(0);
  });
});
