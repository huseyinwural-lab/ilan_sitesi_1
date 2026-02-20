import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { LoadingState, ErrorState } from '@/components/account/AccountStates';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AccountSupportDetail() {
  const { id } = useParams();
  const [item, setItem] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchDetail = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/applications/${id}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (!res.ok) {
        throw new Error('Başvuru bulunamadı');
      }
      const data = await res.json();
      setItem(data.item);
      setError('');
    } catch (err) {
      setError('Başvuru detayı yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [id]);

  if (loading) {
    return <LoadingState label="Başvuru yükleniyor..." />;
  }

  if (error || !item) {
    return <ErrorState message={error || 'Başvuru bulunamadı'} onRetry={fetchDetail} testId="account-support-detail-error" />;
  }

  return (
    <div className="space-y-4" data-testid="account-support-detail">
      <div className="flex items-center justify-between" data-testid="account-support-detail-header">
        <div>
          <h1 className="text-2xl font-bold" data-testid="account-support-detail-title">Başvuru Detayı</h1>
          <p className="text-sm text-muted-foreground" data-testid="account-support-detail-ref">
            Referans: {item.application_id || item.id}
          </p>
        </div>
        <Link to="/account/support" className="text-sm text-primary" data-testid="account-support-detail-back">
          Listeye dön
        </Link>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-3" data-testid="account-support-detail-card">
        <div>
          <div className="text-xs text-muted-foreground">Durum</div>
          <div className="font-semibold" data-testid="account-support-detail-status">{item.status}</div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground">Konu</div>
          <div data-testid="account-support-detail-subject">{item.subject}</div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground">Açıklama</div>
          <div className="text-sm text-slate-700" data-testid="account-support-detail-description">{item.description}</div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground">Admin Notu</div>
          <div className="text-sm" data-testid="account-support-detail-decision">{item.decision_reason || '-'}</div>
        </div>
        <div>
          <div className="text-xs text-muted-foreground">Oluşturulma</div>
          <div className="text-sm" data-testid="account-support-detail-created">
            {item.created_at ? new Date(item.created_at).toLocaleString('tr-TR') : '-'}
          </div>
        </div>
      </div>
    </div>
  );
}
