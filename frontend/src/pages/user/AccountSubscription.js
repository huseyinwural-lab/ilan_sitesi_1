import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { FinanceStatusBadge } from '@/components/finance/FinanceStatusBadge';
import { FinanceEmptyState, FinanceErrorState, FinanceLoadingState } from '@/components/finance/FinanceStateView';
import { formatMoneyMinor, resolveLocaleByCountry } from '@/utils/financeFormat';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AccountSubscriptionPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [subscription, setSubscription] = useState(null);
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState('');
  const [preview, setPreview] = useState(null);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [confirmAction, setConfirmAction] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);
  const locale = resolveLocaleByCountry(localStorage.getItem('selectedCountry') || 'TR');

  const resolveApiError = (err, fallback) => {
    const detail = err?.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) return detail;
    return fallback;
  };

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
    } catch (err) {
      setError(resolveApiError(err, 'Abonelik bilgileri yüklenemedi. Lütfen daha sonra tekrar deneyiniz.'));
    } finally {
      setLoading(false);
    }
  };

  const openConfirm = (actionType) => {
    setConfirmAction(actionType);
    setConfirmOpen(true);
  };

  const runConfirmedAction = async () => {
    if (!confirmAction) return;
    setActionLoading(true);
    setError('');
    setNotice('');
    try {
      if (confirmAction === 'cancel') {
        await axios.post(`${API}/account/subscription/cancel`, {}, { headers: authHeader });
        await loadData();
        setNotice('İptal talebiniz alınmıştır. Aboneliğiniz dönem sonunda sonlandırılacaktır.');
      }
      if (confirmAction === 'reactivate') {
        await axios.post(`${API}/account/subscription/reactivate`, {}, { headers: authHeader });
        await loadData();
        setNotice('Abonelik iptal talebiniz kaldırılmıştır. Planınız aktif durumda devam etmektedir.');
      }
      if (confirmAction === 'plan-preview') {
        if (!selectedPlan) {
          throw new Error('Lütfen bir plan seçiniz.');
        }
        const res = await axios.post(
          `${API}/account/subscription/plan-change-preview`,
          { target_plan_id: selectedPlan },
          { headers: { ...authHeader, 'Content-Type': 'application/json' } },
        );
        setPreview(res.data);
        setNotice('Plan değişikliği önizleme sonucu başarıyla hazırlandı.');
      }
      setConfirmOpen(false);
      setConfirmAction('');
    } catch (err) {
      if (confirmAction === 'plan-preview' && err?.message === 'Lütfen bir plan seçiniz.') {
        setError('Plan değişikliği önizlemesi için önce hedef plan seçiniz.');
      } else {
        setError(resolveApiError(err, 'İşlem tamamlanamadı. Lütfen daha sonra tekrar deneyiniz.'));
      }
    } finally {
      setActionLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const confirmTitle =
    confirmAction === 'cancel'
      ? 'Abonelik İptal Onayı'
      : confirmAction === 'reactivate'
        ? 'Abonelik Yeniden Aktifleştirme Onayı'
        : 'Plan Değişikliği Önizleme Onayı';

  const confirmDescription =
    confirmAction === 'cancel'
      ? 'Aboneliğiniz dönem sonunda iptal edilecektir. İşlemi onaylıyor musunuz?'
      : confirmAction === 'reactivate'
        ? 'Mevcut iptal talebi kaldırılacaktır. İşlemi onaylıyor musunuz?'
        : 'Seçili plan için önizleme hesaplaması yapılacaktır. Onaylıyor musunuz?';

  return (
    <div className="space-y-4" data-testid="account-subscription-page">
      <div data-testid="account-subscription-header">
        <h1 className="text-2xl font-bold" data-testid="account-subscription-title">Aboneliğim</h1>
        <p className="text-sm text-muted-foreground" data-testid="account-subscription-subtitle">Plan, yenileme ve abonelik işlemlerinizi buradan yönetebilirsiniz.</p>
      </div>

      {loading ? <FinanceLoadingState testId="account-subscription-loading" /> : null}
      {error ? <FinanceErrorState testId="account-subscription-error" message={error} /> : null}
      {notice ? (
        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700" data-testid="account-subscription-notice">
          {notice}
        </div>
      ) : null}

      {!loading && (!subscription || !subscription.has_subscription) ? (
        <FinanceEmptyState
          testId="account-subscription-empty"
          message="Aktif abonelik kaydınız bulunmamaktadır. Planlar aktif olduğunda bu ekrandan takip edebilirsiniz."
        />
      ) : null}

      {!loading && subscription?.has_subscription ? (
        <>
          <div className="rounded-lg border bg-white p-4 space-y-2" data-testid="account-subscription-summary">
            <div className="flex items-center gap-2" data-testid="account-subscription-status-row">
              <span className="text-sm">Durum:</span>
              <FinanceStatusBadge status={subscription.status} testId="account-subscription-status" />
            </div>
            <div className="text-sm" data-testid="account-subscription-plan">Plan: {subscription.plan?.name || '-'}</div>
            <div className="text-sm" data-testid="account-subscription-price">Ücret: {formatMoneyMinor(Math.round((subscription.plan?.price_amount || 0) * 100), subscription.plan?.currency_code || 'EUR', locale)}</div>
            <div className="text-sm" data-testid="account-subscription-renewal">Yenileme tarihi: {subscription.current_period_end ? new Date(subscription.current_period_end).toLocaleDateString(locale) : '-'}</div>
            <div className="text-xs text-muted-foreground" data-testid="account-subscription-cancel-flag">Dönem sonu iptal talebi: {subscription.cancel_at_period_end ? 'Açık' : 'Kapalı'}</div>

            {subscription.cancel_at_period_end ? (
              <div className="rounded-md border border-amber-200 bg-amber-50 p-2 text-xs text-amber-700" data-testid="account-subscription-pending-state">
                İptal talebiniz beklemede olup dönem sonunda uygulanacaktır.
              </div>
            ) : (
              <div className="rounded-md border border-emerald-200 bg-emerald-50 p-2 text-xs text-emerald-700" data-testid="account-subscription-active-state">
                Aboneliğiniz aktif durumdadır ve otomatik yenileme devam etmektedir.
              </div>
            )}

            <div className="flex gap-2 flex-wrap pt-2" data-testid="account-subscription-actions">
              <button
                type="button"
                className="h-9 px-3 rounded-md border text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={() => openConfirm('cancel')}
                disabled={actionLoading || subscription.cancel_at_period_end}
                data-testid="account-subscription-cancel-button"
              >
                Dönem sonunda iptal et
              </button>
              <button
                type="button"
                className="h-9 px-3 rounded-md border text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={() => openConfirm('reactivate')}
                disabled={actionLoading || !subscription.cancel_at_period_end}
                data-testid="account-subscription-reactivate-button"
              >
                İptal talebini kaldır
              </button>
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
              <button
                type="button"
                className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={() => openConfirm('plan-preview')}
                disabled={actionLoading || !selectedPlan}
                data-testid="account-subscription-preview-button"
              >
                Önizle
              </button>
            </div>
            {preview ? (
              <div className="text-sm space-y-1" data-testid="account-subscription-preview-result">
                <div data-testid="account-subscription-preview-current">Mevcut Plan: {preview.current_plan?.name || '-'}</div>
                <div data-testid="account-subscription-preview-target">Hedef Plan: {preview.target_plan?.name || '-'}</div>
                <div data-testid="account-subscription-preview-delta">Bugün fark: {preview.proration_preview?.immediate_delta_amount}</div>
                <div data-testid="account-subscription-preview-next">Sonraki dönem: {preview.proration_preview?.next_cycle_amount}</div>
              </div>
            ) : null}
          </div>
        </>
      ) : null}

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent data-testid="account-subscription-confirm-modal">
          <AlertDialogHeader>
            <AlertDialogTitle data-testid="account-subscription-confirm-title">{confirmTitle}</AlertDialogTitle>
            <AlertDialogDescription data-testid="account-subscription-confirm-description">{confirmDescription}</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel data-testid="account-subscription-confirm-cancel">Vazgeç</AlertDialogCancel>
            <AlertDialogAction
              data-testid="account-subscription-confirm-submit"
              onClick={(event) => {
                event.preventDefault();
                runConfirmedAction();
              }}
              disabled={actionLoading}
            >
              {actionLoading ? 'İşleniyor...' : 'Onayla'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
