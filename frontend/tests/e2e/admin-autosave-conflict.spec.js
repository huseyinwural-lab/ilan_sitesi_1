const { test, expect } = require('@playwright/test');

const adminCreds = { email: 'admin@platform.com', password: 'Admin123!' };

const loginAdmin = async (page) => {
  await page.goto('/admin/login');
  await page.getByTestId('login-email').fill(adminCreds.email);
  await page.getByTestId('login-password').fill(adminCreds.password);
  await page.getByTestId('login-submit').click();
  await page.waitForURL(/\/admin/, { timeout: 60000 });
};

test('Autosave conflict uyarısı gösterir', async ({ page, request }) => {
  const loginRes = await request.post('/api/auth/login', { data: adminCreds });
  const loginData = await loginRes.json();
  const token = loginData.access_token;

  const listRes = await request.get('/api/admin/categories?country=DE', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const listData = await listRes.json();
  const targetCategory = (listData.items || []).find(
    (item) => item.hierarchy_complete && item.form_schema && item.form_schema.status === 'draft'
  );

  if (!targetCategory) {
    throw new Error('Draft kategori bulunamadı');
  }

  await page.addInitScript(() => localStorage.setItem('selected_country', 'DE'));
  await loginAdmin(page);
  await page.goto('/admin/categories');
  await page.waitForSelector(`[data-testid="categories-edit-${targetCategory.id}"]`, { timeout: 60000 });
  await page.getByTestId(`categories-edit-${targetCategory.id}`).click({ force: true });
  await expect(page.getByTestId('categories-core-step')).toBeVisible({ timeout: 60000 });

  await request.patch(`/api/admin/categories/${targetCategory.id}`, {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      name: `${targetCategory.name}-conflict`,
      expected_updated_at: targetCategory.updated_at,
    },
  });

  await page.getByTestId('categories-title-min').fill('11');
  await page.waitForTimeout(3000);
  await expect(page.getByText('Başka bir sekmede güncellendi')).toBeVisible();
});
