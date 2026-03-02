import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { FinanceStatusBadge } from '@/components/finance/FinanceStatusBadge';
import { FinanceEmptyState, FinanceErrorState, FinanceLoadingState } from '@/components/finance/FinanceStateView';
import { formatMoneyMinor, normalizePaymentMessage, resolveLocaleByCountry } from '@/utils/financeFormat';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function AccountPaymentsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('all');
  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);
  const locale = resolveLocaleByCountry(localStorage.getItem('selectedCountry') || 'TR');

  const loadPayments = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (status !== 'all') params.set('status', status);
      const res = await axios.get(`${API}/account/payments?${params.toString()}`, { headers: authHeader });
      setItems(res.data.items || []);
      setError('');
    } catch {
      setError('Ödeme geçmişi yüklenemedi. Lütfen daha sonra tekrar deneyiniz.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPayments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  return (
    <div className="space-y-4" data-testid="account-payments-page">
      <div className="flex items-center justify-between gap-3" data-testid="account-payments-header">
        <div>
          <h1 className="text-2xl font-bold" data-testid="account-payments-title">Ödeme Geçmişi</h1>
          <p className="text-sm text-muted-foreground" data-testid="account-payments-subtitle">Ödeme kayıtlarınızı ve işlem durumlarını görüntüleyebilirsiniz.</p>
        </div>
        <div className="text-xs text-muted-foreground" data-testid="account-payments-count">Toplam kayıt: {items.length}</div>
        <select className="h-9 rounded-md border px-3 text-sm" value={status} onChange={(e) => setStatus(e.target.value)} data-testid="account-payments-filter-status">
          <option value="all">Tümü</option>
          <option value="succeeded">Başarılı</option>
          <option value="failed">Başarısız</option>
          <option value="processing">İşleniyor</option>
          <option value="pending">Beklemede</option>
        </select>
      </div>

      {error ? <FinanceErrorState testId="account-payments-error" message={error} /> : null}

      <div className="rounded-lg border bg-white overflow-hidden" data-testid="account-payments-table">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left p-3">Ödeme</th>
              <th className="text-left p-3">Tutar</th>
              <th className="text-left p-3">Durum</th>
              <th className="text-left p-3">Mesaj</th>
              <th className="text-left p-3">Tarih</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="5" className="p-3"><FinanceLoadingState testId="account-payments-loading" /></td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan="5" className="p-3"><FinanceEmptyState testId="account-payments-empty" message="Henüz ödeme kaydı bulunmamaktadır." /></td></tr>
            ) : items.map((item) => (
              <tr key={item.id} className="border-t" data-testid={`account-payments-row-${item.id}`}>
                <td className="p-3 font-mono text-xs" data-testid={`account-payments-id-${item.id}`}>{item.provider_ref || item.id}</td>
                <td className="p-3" data-testid={`account-payments-amount-${item.id}`}>{formatMoneyMinor(item.amount_minor, item.currency, locale)}</td>
                <td className="p-3"><FinanceStatusBadge status={item.status} testId={`account-payments-status-${item.id}`} /></td>
                <td className="p-3" data-testid={`account-payments-message-${item.id}`}>{item.normalized_message || normalizePaymentMessage(item.status)}</td>
                <td className="p-3" data-testid={`account-payments-created-${item.id}`}>{item.created_at ? new Date(item.created_at).toLocaleString(locale) : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
