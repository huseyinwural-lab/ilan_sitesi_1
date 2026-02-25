import React, { useEffect, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminPricingPackages() {
  const [packages, setPackages] = useState([]);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const authHeader = { Authorization: `Bearer ${localStorage.getItem('access_token')}` };

  const fetchPackages = async () => {
    const res = await axios.get(`${API}/admin/pricing/packages`, { headers: authHeader });
    setPackages(res.data?.items || []);
  };

  useEffect(() => {
    fetchPackages();
  }, []);

  const updatePackage = (id, field, value) => {
    setPackages((prev) => prev.map((item) => (item.id === id ? { ...item, [field]: value } : item)));
  };

  const handleSave = async () => {
    setStatus('');
    setError('');
    try {
      await axios.put(
        `${API}/admin/pricing/packages`,
        {
          packages: packages.map((item) => ({
            name: item.name,
            listing_quota: Number(item.listing_quota),
            package_duration_days: Number(item.package_duration_days),
            package_price_amount: Number(item.package_price_amount || 0),
            currency: item.currency || 'EUR',
            is_active: Boolean(item.is_active),
          })),
        },
        { headers: authHeader }
      );
      setStatus('Kaydedildi');
      fetchPackages();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Kaydetme başarısız');
    }
  };

  return (
    <div className="space-y-5" data-testid="admin-pricing-packages-page">
      <div>
        <h1 className="text-2xl font-semibold" data-testid="admin-pricing-packages-title">Kurumsal Paketler</h1>
        <p className="text-sm text-muted-foreground" data-testid="admin-pricing-packages-subtitle">
          Kurumsal quota paketlerini yönetin. 90 gün yayın süresi sabittir.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3" data-testid="admin-pricing-packages-grid">
        {packages.map((item) => (
          <div key={item.id} className="rounded-lg border bg-white p-4 space-y-3" data-testid={`admin-pricing-package-${item.id}`}>
            <div className="text-sm font-semibold">{item.name}</div>
            <div className="text-xs text-muted-foreground">Quota: {item.listing_quota} ilan</div>
            <div className="text-xs text-muted-foreground">Süre: {item.package_duration_days} gün</div>
            <div className="text-xs text-muted-foreground">Yayın: {item.publish_days} gün (sabit)</div>

            <input
              type="number"
              className="h-9 w-full rounded-md border px-2"
              value={item.package_price_amount ?? ''}
              onChange={(e) => updatePackage(item.id, 'package_price_amount', e.target.value)}
              data-testid={`admin-pricing-package-price-${item.id}`}
            />
            <input
              className="h-9 w-full rounded-md border px-2"
              value={item.currency || 'EUR'}
              onChange={(e) => updatePackage(item.id, 'currency', e.target.value.toUpperCase())}
              data-testid={`admin-pricing-package-currency-${item.id}`}
            />

            <label className="flex items-center gap-2 text-xs" data-testid={`admin-pricing-package-active-${item.id}`}>
              <input
                type="checkbox"
                checked={Boolean(item.is_active)}
                onChange={(e) => updatePackage(item.id, 'is_active', e.target.checked)}
                data-testid={`admin-pricing-package-active-toggle-${item.id}`}
              />
              Aktif
            </label>
          </div>
        ))}
      </div>

      {error && (
        <div className="text-xs text-rose-600" data-testid="admin-pricing-packages-error">{error}</div>
      )}
      {status && (
        <div className="text-xs text-emerald-600" data-testid="admin-pricing-packages-status">{status}</div>
      )}

      <button
        type="button"
        onClick={handleSave}
        className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
        data-testid="admin-pricing-packages-save"
      >
        Kaydet
      </button>
    </div>
  );
}
