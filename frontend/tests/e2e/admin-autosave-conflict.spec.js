const { test, expect } = require('@playwright/test');

const adminCreds = { email: 'admin@platform.com', password: 'Admin123!' };

const loginAdmin = async (page) => {
  await page.goto('/admin/login');
  await page.getByTestId('login-email').fill(adminCreds.email);
  await page.getByTestId('login-password').fill(adminCreds.password);
  await page.getByTestId('login-submit').click();
  await expect(page.getByTestId('nav-catalog-categories')).toBeVisible({ timeout: 60000 });
};

test('Autosave conflict uyarısı gösterir', async ({ page, request }) => {
  const loginRes = await request.post('/api/auth/login', { data: adminCreds });
  const loginData = await loginRes.json();
  const token = loginData.access_token;

  const listRes = await request.get('/api/admin/categories?country=DE', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const listData = await listRes.json();
  const items = listData.items || [];
  let targetCategory = items.find(
    (item) => item.hierarchy_complete && item.form_schema && item.form_schema.status === 'draft'
  );

  if (!targetCategory) {
    throw new Error('Draft kategori bulunamadı');
  }

  const hasChild = items.some((child) => child.parent_id === targetCategory.id);
  if (!hasChild) {
    const childSlug = `${targetCategory.slug}-child-${Date.now()}`;
    await request.post('/api/admin/categories', {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        name: `${targetCategory.name} Child`,
        slug: childSlug,
        parent_id: targetCategory.id,
        country_code: targetCategory.country_code || 'DE',
        active_flag: true,
        sort_order: 0,
        hierarchy_complete: true,
      },
    });
  }

  if (!targetCategory.form_schema || targetCategory.form_schema.status !== 'draft') {
    test.skip(true, 'Autosave sadece draft şemalarda aktif');
  }

  await page.addInitScript(() => localStorage.setItem('selected_country', 'DE'));
  await loginAdmin(page);
  await page.getByTestId('nav-catalog-categories').click();
  await expect(page.getByTestId('categories-page')).toBeVisible({ timeout: 60000 });
  await page.waitForSelector('[data-testid="categories-loading"]', { state: 'detached' });

  let editLocator = page.locator(`[data-testid="categories-edit-${targetCategory.id}"]`);
  if (await editLocator.count() === 0) {
    editLocator = page.locator('[data-testid^="categories-edit-"]').first();
    const fallbackTestId = await editLocator.getAttribute('data-testid');
    const fallbackId = fallbackTestId?.replace('categories-edit-', '');
    const fallbackCategory = (listData.items || []).find((item) => item.id === fallbackId);
    if (fallbackCategory) {
      targetCategory = fallbackCategory;
    }
  }

  if (!targetCategory.form_schema || targetCategory.form_schema.status !== 'draft') {
    test.skip(true, 'Autosave sadece draft şemalarda aktif');
  }

  await editLocator.click({ force: true });
  await expect(page.getByTestId('category-hierarchy-step')).toBeVisible({ timeout: 60000 });

  if (await page.getByTestId('categories-subcategory-empty').isVisible()) {
    await page.getByTestId('categories-subcategory-add').click();
    await page.getByTestId('categories-subcategory-name-0').fill('Alt Kategori');
    await page.getByTestId('categories-subcategory-slug-0').fill(`alt-${Date.now()}`);
  }

  await page.getByTestId('categories-step-next').click();
  await expect(page.getByTestId('categories-core-step')).toBeVisible({ timeout: 60000 });

  const freshRes = await request.get(`/api/admin/categories?country=DE`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const freshData = await freshRes.json();
  const refreshed = (freshData.items || []).find((item) => item.id === targetCategory.id);

  if (refreshed) {
    await request.patch(`/api/admin/categories/${targetCategory.id}`, {
      headers: { Authorization: `Bearer ${token}` },
      data: {
        name: `${targetCategory.name}-conflict`,
        expected_updated_at: refreshed.updated_at,
      },
    });
  }

  await page.getByTestId('categories-title-min').fill('11');
  await page.waitForTimeout(3000);
  await expect(page.getByText('Başka bir sekmede güncellendi')).toBeVisible();
});
