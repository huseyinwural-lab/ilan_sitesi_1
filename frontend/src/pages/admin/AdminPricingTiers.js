import React, { useEffect, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminPricingTiers() {
  const [tiers, setTiers] = useState([]);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const authHeader = { Authorization: `Bearer ${localStorage.getItem('access_token')}` };

  const fetchTiers = async () => {
    const res = await axios.get(`${API}/admin/pricing/tiers`, { headers: authHeader });
    setTiers(res.data?.items || []);
  };

  useEffect(() => {
    fetchTiers();
  }, []);

  const getTier = (tierNo) => tiers.find((rule) => rule.tier_no === tierNo) || {};

  const updateTierValue = (tierNo, field, value) => {
    setTiers((prev) => prev.map((rule) => (rule.tier_no === tierNo ? { ...rule, [field]: value } : rule)));
  };

  const handleSave = async () => {
    setStatus('');
    setError('');
    const tier1 = getTier(1);
    const tier2 = getTier(2);
    const tier3 = getTier(3);
    const currency = tier2.currency || tier3.currency || tier1.currency || 'EUR';

    try {
      await axios.put(
        `${API}/admin/pricing/tiers`,
        {
          rules: [
            { tier_no: 1, price_amount: 0, currency },
            { tier_no: 2, price_amount: Number(tier2.price_amount || 0), currency },
            { tier_no: 3, price_amount: Number(tier3.price_amount || 0), currency },
          ],
        },
        { headers: authHeader }
      );
      setStatus('Kaydedildi');
      fetchTiers();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Kaydetme başarısız');
    }
  };

  return (
    <div className="space-y-5" data-testid="admin-pricing-tiers-page">
      <div>
        <h1 className="text-2xl font-semibold" data-testid="admin-pricing-tiers-title">Bireysel Tier Pricing</h1>
        <p className="text-sm text-muted-foreground" data-testid="admin-pricing-tiers-subtitle">
          Bireysel ilan ücretleri (takvim yılı). 90 gün yayın süresi sabittir.
        </p>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-3" data-testid="admin-pricing-tiers-card">
        <div className="grid gap-3 md:grid-cols-3" data-testid="admin-pricing-tiers-grid">
          <div className="rounded-md border p-3" data-testid="admin-pricing-tier-1">
            <div className="text-xs text-muted-foreground">0. İlan (Ücretsiz)</div>
            <div className="text-lg font-semibold">0</div>
            <div className="text-xs text-muted-foreground">Para birimi: {getTier(1).currency || 'EUR'}</div>
            <div className="text-xs text-muted-foreground">Yayın: 90 gün (sabit)</div>
          </div>

          <div className="rounded-md border p-3" data-testid="admin-pricing-tier-2">
            <div className="text-xs text-muted-foreground">2. İlan</div>
            <input
              type="number"
              className="mt-2 h-9 w-full rounded-md border px-2"
              value={getTier(2).price_amount ?? ''}
              onChange={(e) => updateTierValue(2, 'price_amount', e.target.value)}
              data-testid="admin-pricing-tier-2-price"
            />
            <input
              className="mt-2 h-9 w-full rounded-md border px-2"
              value={getTier(2).currency || 'EUR'}
              onChange={(e) => updateTierValue(2, 'currency', e.target.value.toUpperCase())}
              data-testid="admin-pricing-tier-2-currency"
            />
            <div className="text-xs text-muted-foreground mt-1">Yayın: 90 gün (sabit)</div>
          </div>

          <div className="rounded-md border p-3" data-testid="admin-pricing-tier-3">
            <div className="text-xs text-muted-foreground">3+ İlan</div>
            <input
              type="number"
              className="mt-2 h-9 w-full rounded-md border px-2"
              value={getTier(3).price_amount ?? ''}
              onChange={(e) => updateTierValue(3, 'price_amount', e.target.value)}
              data-testid="admin-pricing-tier-3-price"
            />
            <input
              className="mt-2 h-9 w-full rounded-md border px-2"
              value={getTier(3).currency || getTier(2).currency || 'EUR'}
              onChange={(e) => updateTierValue(3, 'currency', e.target.value.toUpperCase())}
              data-testid="admin-pricing-tier-3-currency"
            />
            <div className="text-xs text-muted-foreground mt-1">Yayın: 90 gün (sabit)</div>
          </div>
        </div>

        {error && (
          <div className="text-xs text-rose-600" data-testid="admin-pricing-tiers-error">{error}</div>
        )}
        {status && (
          <div className="text-xs text-emerald-600" data-testid="admin-pricing-tiers-status">{status}</div>
        )}
        <button
          type="button"
          onClick={handleSave}
          className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
          data-testid="admin-pricing-tiers-save"
        >
          Kaydet
        </button>
      </div>
    </div>
  );
}
