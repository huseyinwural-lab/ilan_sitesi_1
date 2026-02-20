import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { LoadingState, ErrorState, EmptyState } from '@/components/account/AccountStates';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const statusOptions = [
  { value: 'all', label: 'Tümü' },
  { value: 'pending', label: 'Beklemede' },
  { value: 'in_review', label: 'İncelemede' },
  { value: 'approved', label: 'Onaylandı' },
  { value: 'rejected', label: 'Reddedildi' },
  { value: 'closed', label: 'Kapatıldı' },
];

export default function AccountSupportList() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [status, setStatus] = useState('all');

  const fetchItems = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (status !== 'all') params.set('status', status);
      const res = await fetch(`${API}/applications/my?${params.toString()}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (!res.ok) {
        throw new Error('Başvurular yüklenemedi');
      }
      const data = await res.json();
      setItems(data.items || []);
      setError('');
    } catch (err) {
      setError('Başvurular yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [status]);

  if (loading) {
    return <LoadingState label="Başvurular yükleniyor..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={fetchItems} testId="account-support-error" />;
  }

  if (items.length === 0) {
    return (
      <EmptyState
        title="Başvuru bulunamadı"
        description="Henüz destek başvurunuz yok."
        actionLabel="Yeni Başvuru Oluştur"
        onAction={() => window.location.assign('/support')}
        testId="account-support-empty"
      />
    );
  }

  return (
    <div className="space-y-4" data-testid="account-support-list">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="account-support-header">
        <div>
          <h1 className="text-2xl font-bold" data-testid="account-support-title">Başvurularım</h1>
          <p className="text-sm text-muted-foreground" data-testid="account-support-subtitle">Tüm destek talepleriniz.</p>
        </div>
        <Link
          to="/support"
          className="h-10 px-4 rounded-md bg-primary text-primary-foreground text-sm inline-flex items-center"
          data-testid="account-support-new"
        >
          Yeni Başvuru
        </Link>
      </div>

      <div className="flex items-center gap-3" data-testid="account-support-filters">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          className="h-9 rounded-md border px-3 text-sm"
          data-testid="account-support-status"
        >
          {statusOptions.map((opt) => (
            <option key={opt.value} value={opt.value} data-testid={`account-support-status-${opt.value}`}>{opt.label}</option>
          ))}
        </select>
      </div>

      <div className="rounded-lg border bg-white overflow-hidden" data-testid="account-support-table">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left p-3">Referans</th>
              <th className="text-left p-3">Konu</th>
              <th className="text-left p-3">Durum</th>
              <th className="text-left p-3">Tarih</th>
              <th className="text-right p-3">Detay</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr key={item.id} className="border-t" data-testid={`account-support-row-${item.id}`}>
                <td className="p-3" data-testid={`account-support-ref-${item.id}`}>{item.application_id || item.id}</td>
                <td className="p-3" data-testid={`account-support-subject-${item.id}`}>{item.subject}</td>
                <td className="p-3" data-testid={`account-support-status-${item.id}`}>{item.status}</td>
                <td className="p-3" data-testid={`account-support-date-${item.id}`}>{
                  item.created_at ? new Date(item.created_at).toLocaleDateString('tr-TR') : '-'
                }</td>
                <td className="p-3 text-right">
                  <Link
                    to={`/account/support/${item.id}`}
                    className="text-primary text-sm"
                    data-testid={`account-support-detail-${item.id}`}
                  >
                    Görüntüle
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
