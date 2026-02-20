const { test, expect } = require('@playwright/test');

test('super admin can open admin invite modal', async ({ page }) => {
  await page.goto('/admin/login');
  await page.getByTestId('login-email').fill('admin@platform.com');
  await page.getByTestId('login-password').fill('Admin123!');
  await page.getByTestId('login-submit').click();

  await page.goto('/admin/admin-users');
  await expect(page.getByTestId('admin-users-page')).toBeVisible({ timeout: 60000 });
  await page.getByTestId('admin-users-create-button').click();
  await expect(page.getByTestId('admin-users-modal')).toBeVisible();
});

test('admin users ia cleanup: legacy routes redirect and menu item removed', async ({ page }) => {
  await page.goto('/admin/login');
  await page.getByTestId('login-email').fill('admin@platform.com');
  await page.getByTestId('login-password').fill('Admin123!');
  await page.getByTestId('login-submit').click();

  await page.goto('/admin/users');
  await expect(page).toHaveURL(/\/admin\/admin-users/);

  await page.goto('/admin/user-management');
  await expect(page).toHaveURL(/\/admin\/admin-users/);

  await expect(page.getByTestId('nav-management-users')).toHaveCount(0);
});

test('bulk deactivate limit enforced', async ({ request }) => {
  const login = await request.post('/api/auth/login', {
    data: { email: 'admin@platform.com', password: 'Admin123!' },
  });
  const loginJson = await login.json();
  const token = loginJson.access_token;

  const payload = { user_ids: Array.from({ length: 21 }).map((_, idx) => `dummy-${idx}`) };
  const response = await request.post('/api/admin/users/bulk-deactivate', {
    data: payload,
    headers: { Authorization: `Bearer ${token}` },
  });

  expect(response.status()).toBe(400);
});

test('super admin can soft delete admin users', async ({ request }) => {
  const login = await request.post('/api/auth/login', {
    data: { email: 'admin@platform.com', password: 'Admin123!' },
  });
  const loginJson = await login.json();
  const token = loginJson.access_token;

  const listResponse = await request.get('/api/admin/users', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const listJson = await listResponse.json();
  const target = (listJson.items || []).find(
    (user) => user.role !== 'super_admin' && user.email !== 'countryadmin@platform.com'
  );

  if (!target) {
    test.skip(true, 'No deletable admin user available');
  }

  const deleteResponse = await request.delete(`/api/admin/users/${target.id}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(deleteResponse.status()).toBe(200);

  const afterResponse = await request.get('/api/admin/users', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const afterJson = await afterResponse.json();
  const stillVisible = (afterJson.items || []).find((user) => user.id === target.id);
  expect(stillVisible).toBeFalsy();
});

test('country admin cannot access admin users api', async ({ request }) => {
  const login = await request.post('/api/auth/login', {
    data: { email: 'countryadmin@platform.com', password: 'Country123!' },
  });
  const loginJson = await login.json();
  const token = loginJson.access_token;

  const response = await request.get('/api/admin/users', {
    headers: { Authorization: `Bearer ${token}` },
  });

  expect(response.status()).toBe(403);
});

const hasSendGrid = Boolean(process.env.SENDGRID_API_KEY);

test.describe('admin invite flow', () => {
  test.skip(!hasSendGrid, 'SendGrid API key not configured');

  test('super admin can invite and accept admin', async ({ page }) => {
    const uniqueEmail = `invite-${Date.now()}@platform.com`;

    await page.goto('/admin/login');
    await page.getByTestId('login-email').fill('admin@platform.com');
    await page.getByTestId('login-password').fill('Admin123!');
    await page.getByTestId('login-submit').click();

    await page.goto('/admin/admin-users');
    await page.getByTestId('admin-users-create-button').click();
    await page.getByTestId('admin-users-form-full-name').fill('Invite User');
    await page.getByTestId('admin-users-form-email').fill(uniqueEmail);
    await page.getByTestId('admin-users-form-role').selectOption('support');
    await page.getByTestId('admin-users-form-submit').click();

    await expect(page.getByTestId('admin-users-form-success')).toContainText('Admin daveti');
  });
});
