const { test, expect } = require('@playwright/test');

test('moderator actions: suspend -> login blocked -> reactivate', async ({ request }) => {
  const login = await request.post('/api/auth/login', {
    data: { email: 'admin@platform.com', password: 'Admin123!' },
  });
  const loginJson = await login.json();
  const token = loginJson.access_token;

  const listResponse = await request.get('/api/admin/individual-users?limit=10', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const listJson = await listResponse.json();
  const target = (listJson.items || []).find((user) => user.email && user.email !== 'admin@platform.com');

  if (!target) {
    return;
  }

  const payload = { reason_code: 'spam', reason_detail: 'test' };
  const suspendResponse = await request.post(`/api/admin/users/${target.id}/suspend`, {
    data: payload,
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(suspendResponse.status()).toBe(200);

  const blockedLogin = await request.post('/api/auth/login', {
    data: { email: target.email, password: 'User123!' },
  });
  expect(blockedLogin.status()).toBe(403);

  const reactivateResponse = await request.post(`/api/admin/users/${target.id}/activate`, {
    data: payload,
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(reactivateResponse.status()).toBe(200);

  const okLogin = await request.post('/api/auth/login', {
    data: { email: target.email, password: 'User123!' },
  });
  expect(okLogin.status()).toBe(200);
});

test('super admin delete hides user from list', async ({ request }) => {
  const login = await request.post('/api/auth/login', {
    data: { email: 'admin@platform.com', password: 'Admin123!' },
  });
  const loginJson = await login.json();
  const token = loginJson.access_token;

  const listResponse = await request.get('/api/admin/individual-users?limit=10', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const listJson = await listResponse.json();
  const target = (listJson.items || []).find((user) => user.email && user.email !== 'user@platform.com');

  if (!target) {
    test.skip(true, 'No deletable individual user available');
  }

  const deleteResponse = await request.delete(`/api/admin/users/${target.id}`, {
    data: { reason_code: 'policy', reason_detail: 'test' },
    headers: { Authorization: `Bearer ${token}` },
  });
  expect(deleteResponse.status()).toBe(200);

  const afterResponse = await request.get('/api/admin/individual-users?limit=10', {
    headers: { Authorization: `Bearer ${token}` },
  });
  const afterJson = await afterResponse.json();
  const stillVisible = (afterJson.items || []).find((user) => user.id === target.id);
  expect(stillVisible).toBeFalsy();
});
