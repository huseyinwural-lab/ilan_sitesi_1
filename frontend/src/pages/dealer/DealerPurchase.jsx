import React, { useEffect, useState } from 'react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function DealerPurchase() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [invoices, setInvoices] = useState([]);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/invoices?limit=20`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || 'Satın alma verisi alınamadı');
      setInvoices(Array.isArray(payload?.items) ? payload.items : []);
    } catch (err) {
      setError(err?.message || 'Satın alma verisi alınamadı');
      setInvoices([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="space-y-4" data-testid="dealer-purchase-page">
      <div className="flex items-center justify-between" data-testid="dealer-purchase-header">
        <h1 className="text-xl font-semibold" data-testid="dealer-purchase-title">Paket & Satın Alım</h1>
        <button onClick={fetchData} className="h-9 rounded-md border px-3 text-sm" data-testid="dealer-purchase-refresh-button">Yenile</button>
      </div>
      {error && <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-purchase-error">{error}</div>}

      <div className="rounded-md border overflow-x-auto" data-testid="dealer-purchase-table-wrap">
        <table className="w-full text-sm" data-testid="dealer-purchase-table">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-3 py-2 text-left">Invoice</th>
              <th className="px-3 py-2 text-left">Paket</th>
              <th className="px-3 py-2 text-left">Durum</th>
              <th className="px-3 py-2 text-left">Tutar</th>
              <th className="px-3 py-2 text-left">Tarih</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td className="px-3 py-4" colSpan={5} data-testid="dealer-purchase-loading">Yükleniyor...</td></tr>
            ) : invoices.length === 0 ? (
              <tr><td className="px-3 py-4 text-slate-500" colSpan={5} data-testid="dealer-purchase-empty">Kayıt yok</td></tr>
            ) : (
              invoices.map((row) => (
                <tr key={row.id} className="border-t" data-testid={`dealer-purchase-row-${row.id}`}>
                  <td className="px-3 py-2" data-testid={`dealer-purchase-invoice-${row.id}`}>{row.invoice_no || row.id}</td>
                  <td className="px-3 py-2" data-testid={`dealer-purchase-plan-${row.id}`}>{row.plan_name || '-'}</td>
                  <td className="px-3 py-2" data-testid={`dealer-purchase-status-${row.id}`}>{row.status}</td>
                  <td className="px-3 py-2" data-testid={`dealer-purchase-amount-${row.id}`}>{row.amount_total} {row.currency}</td>
                  <td className="px-3 py-2" data-testid={`dealer-purchase-date-${row.id}`}>{row.created_at || '-'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
