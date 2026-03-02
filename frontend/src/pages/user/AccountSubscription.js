import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { FinanceStatusBadge } from '@/components/finance/FinanceStatusBadge';
import { FinanceEmptyState, FinanceErrorState, FinanceLoadingState } from '@/components/finance/FinanceStateView';
import { formatMoneyMinor, resolveLocaleByCountry } from '@/utils/financeFormat';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AccountSubscriptionPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [subscription, setSubscription] = useState(null);
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState('');
  const [preview, setPreview] = useState(null);

  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);
  const locale = resolveLocaleByCountry(localStorage.getItem('selectedCountry') || 'TR');

  const loadData = async () => {
    setLoading(true);
    try {
      const [subRes, planRes] = await Promise.all([
        axios.get(`${API}/account/subscription`, { headers: authHeader }),
        axios.get(`${API}/account/subscription/plans`, { headers: authHeader }),
      ]);
      setSubscription(subRes.data);
      setPlans(planRes.data.items || []);
      setError('');
    } catch {
      setError('Abonelik verisi alınamadı');
    } finally {
      setLoading(false);
    }
  };

  const cancelAtPeriodEnd = async () => {
    try {
      await axios.post(`${API}/account/subscription/cancel`, {}, { headers: authHeader });
      await loadData();
    } catch {
      setError('İptal işlemi başarısız');
    }
  };

  const reactivate = async () => {
    try {
      await axios.post(`${API}/account/subscription/reactivate`, {}, { headers: authHeader });
      await loadData();
    } catch {
      setError('Yeniden aktive etme başarısız');
    }
  };

  const previewPlanChange = async () => {
    if (!selectedPlan) return;
    try {
      const res = await axios.post(
        `${API}/account/subscription/plan-change-preview`,
        { target_plan_id: selectedPlan },
        { headers: { ...authHeader, 'Content-Type': 'application/json' } },
      );
      setPreview(res.data);
    } catch {
      setError('Plan değişikliği önizlemesi alınamadı');
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) return <FinanceLoadingState testId="account-subscription-loading" />;
  if (error) return <FinanceErrorState testId="account-subscription-error" message={error} />;
  if (!subscription || !subscription.has_subscription) return <FinanceEmptyState testId="account-subscription-empty" message="Aktif abonelik bulunamadı" />;

  return (
    <div className="space-y-4" data-testid="account-subscription-page">
      <div data-testid="account-subscription-header">
        <h1 className="text-2xl font-bold" data-testid="account-subscription-title">Aboneliğim</h1>
        <p className="text-sm text-muted-foreground" data-testid="account-subscription-subtitle">Plan, yenileme ve abonelik işlemleriniz.</p>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-2" data-testid="account-subscription-summary">
        <div className="flex items-center gap-2" data-testid="account-subscription-status-row">
          <span className="text-sm">Durum:</span>
          <FinanceStatusBadge status={subscription.status} testId="account-subscription-status" />
        </div>
        <div className="text-sm" data-testid="account-subscription-plan">Plan: {subscription.plan?.name || '-'}</div>
        <div className="text-sm" data-testid="account-subscription-price">Ücret: {formatMoneyMinor(Math.round((subscription.plan?.price_amount || 0) * 100), subscription.plan?.currency_code || 'EUR', locale)}</div>
        <div className="text-sm" data-testid="account-subscription-renewal">Yenileme: {subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString(locale) : '-'}</div>
        <div className="text-xs text-muted-foreground" data-testid="account-subscription-cancel-flag">cancel_at_period_end: {subscription.cancel_at_period_end ? 'true' : 'false'}</div>

        <div className="flex gap-2 flex-wrap pt-2" data-testid="account-subscription-actions">
          <button className="h-9 px-3 rounded-md border text-sm" onClick={cancelAtPeriodEnd} data-testid="account-subscription-cancel-button">Dönem sonunda iptal et</button>
          <button className="h-9 px-3 rounded-md border text-sm" onClick={reactivate} data-testid="account-subscription-reactivate-button">Tekrar aktive et</button>
        </div>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-3" data-testid="account-subscription-plan-preview">
        <div className="text-sm font-semibold" data-testid="account-subscription-plan-preview-title">Plan değişikliği önizleme</div>
        <div className="flex gap-2 flex-wrap" data-testid="account-subscription-plan-preview-controls">
          <select className="h-9 rounded-md border px-3 text-sm" value={selectedPlan} onChange={(e) => setSelectedPlan(e.target.value)} data-testid="account-subscription-plan-select">
            <option value="">Plan seçin</option>
            {plans.map((plan) => (
              <option key={plan.id} value={plan.id}>{plan.name} - {plan.price_amount} {plan.currency_code}</option>
            ))}
          </select>
          <button className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm" onClick={previewPlanChange} data-testid="account-subscription-preview-button">Önizle</button>
        </div>
        {preview ? (
          <div className="text-sm space-y-1" data-testid="account-subscription-preview-result">
            <div data-testid="account-subscription-preview-current">Mevcut: {preview.current_plan?.name || '-'}</div>
            <div data-testid="account-subscription-preview-target">Hedef: {preview.target_plan?.name || '-'}</div>
            <div data-testid="account-subscription-preview-delta">Bugün fark: {preview.proration_preview?.immediate_delta_amount}</div>
            <div data-testid="account-subscription-preview-next">Sonraki dönem: {preview.proration_preview?.next_cycle_amount}</div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
