import React, { useEffect, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const SCOPE_LABELS = {
  all: 'Her iki kullanıcı',
  individual: 'Bireysel',
  corporate: 'Kurumsal',
};

const emptyForm = {
  is_enabled: false,
  start_at: '',
  end_at: '',
  scope: 'all',
};

export default function AdminPricingCampaign() {
  const [policy, setPolicy] = useState(null);
  const [form, setForm] = useState(emptyForm);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [active, setActive] = useState(false);

  const authHeader = { Authorization: `Bearer ${localStorage.getItem('access_token')}` };

  const fetchPolicy = async () => {
    const res = await axios.get(`${API}/admin/pricing/campaign`, { headers: authHeader });
    const data = res.data;
    setPolicy(data.policy);
    setActive(Boolean(data.active));
    setForm({
      is_enabled: Boolean(data.policy?.is_enabled),
      start_at: data.policy?.start_at ? data.policy.start_at.slice(0, 16) : '',
      end_at: data.policy?.end_at ? data.policy.end_at.slice(0, 16) : '',
      scope: data.policy?.scope || 'all',
    });
  };

  useEffect(() => {
    fetchPolicy();
  }, []);

  const savePolicy = async (overrideEnabled) => {
    setStatus('');
    setError('');
    const payload = {
      is_enabled: overrideEnabled ?? form.is_enabled,
      start_at: form.start_at || null,
      end_at: form.end_at || null,
      scope: form.scope,
    };
    if (payload.is_enabled && !payload.start_at) {
      setError('Aktif etmek için başlangıç tarihi zorunlu.');
      return;
    }
    try {
      const res = await axios.put(`${API}/admin/pricing/campaign`, payload, { headers: authHeader });
      setPolicy(res.data.policy);
      setActive(Boolean(res.data.active));
      setForm({
        is_enabled: Boolean(res.data.policy?.is_enabled),
        start_at: res.data.policy?.start_at ? res.data.policy.start_at.slice(0, 16) : '',
        end_at: res.data.policy?.end_at ? res.data.policy.end_at.slice(0, 16) : '',
        scope: res.data.policy?.scope || 'all',
      });
      setStatus('Kaydedildi');
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || 'Kaydetme başarısız');
    }
  };

  return (
    <div className="space-y-5" data-testid="admin-pricing-campaign-page">
      <div>
        <h1 className="text-2xl font-semibold" data-testid="admin-pricing-campaign-title">Lansman Kampanyası Modu</h1>
        <p className="text-sm text-muted-foreground" data-testid="admin-pricing-campaign-subtitle">
          Kampanya policy ve override yönetimi.
        </p>
      </div>

      <div className="rounded-lg border bg-white p-4" data-testid="admin-pricing-campaign-card">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold" data-testid="admin-pricing-campaign-status">{active ? 'Aktif Kampanya' : 'Kampanya Pasif'}</div>
            <div className="text-xs text-muted-foreground" data-testid="admin-pricing-campaign-status-detail">
              Scope: {SCOPE_LABELS[form.scope] || form.scope}
            </div>
          </div>
          <div className="text-xs text-muted-foreground" data-testid="admin-pricing-campaign-version">
            Versiyon: {policy?.version ?? 0}
          </div>
        </div>
        <div className="mt-2 text-xs text-muted-foreground" data-testid="admin-pricing-campaign-dates">
          Başlangıç: {policy?.start_at ? policy.start_at.slice(0, 10) : '—'} | Bitiş: {policy?.end_at ? policy.end_at.slice(0, 10) : '—'}
        </div>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="admin-pricing-campaign-form">
        <div className="flex items-center gap-3">
          <label className="text-sm" data-testid="admin-pricing-campaign-toggle-label">Aç / Kapat</label>
          <input
            type="checkbox"
            checked={form.is_enabled}
            onChange={(e) => setForm((prev) => ({ ...prev, is_enabled: e.target.checked }))}
            data-testid="admin-pricing-campaign-toggle"
          />
        </div>

        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <label className="text-xs">Başlangıç</label>
            <input
              type="datetime-local"
              className="mt-1 h-9 w-full rounded-md border px-2"
              value={form.start_at}
              onChange={(e) => setForm((prev) => ({ ...prev, start_at: e.target.value }))}
              data-testid="admin-pricing-campaign-start"
            />
          </div>
          <div>
            <label className="text-xs">Bitiş (opsiyonel)</label>
            <input
              type="datetime-local"
              className="mt-1 h-9 w-full rounded-md border px-2"
              value={form.end_at}
              onChange={(e) => setForm((prev) => ({ ...prev, end_at: e.target.value }))}
              data-testid="admin-pricing-campaign-end"
            />
          </div>
          <div>
            <label className="text-xs">Scope</label>
            <select
              className="mt-1 h-9 w-full rounded-md border px-2"
              value={form.scope}
              onChange={(e) => setForm((prev) => ({ ...prev, scope: e.target.value }))}
              data-testid="admin-pricing-campaign-scope"
            >
              <option value="all">Her iki kullanıcı</option>
              <option value="individual">Bireysel</option>
              <option value="corporate">Kurumsal</option>
            </select>
          </div>
        </div>

        {error && (
          <div className="text-xs text-rose-600" data-testid="admin-pricing-campaign-error">{error}</div>
        )}
        {status && (
          <div className="text-xs text-emerald-600" data-testid="admin-pricing-campaign-success">{status}</div>
        )}

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => savePolicy()}
            className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
            data-testid="admin-pricing-campaign-save"
          >
            Kaydet
          </button>
          {!form.is_enabled && (
            <button
              type="button"
              onClick={() => savePolicy(true)}
              className="h-9 px-4 rounded-md border text-sm"
              data-testid="admin-pricing-campaign-publish"
            >
              Yayınla
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
