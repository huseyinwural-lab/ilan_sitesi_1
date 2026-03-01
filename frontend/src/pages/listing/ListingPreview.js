import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getToken = () => localStorage.getItem('access_token') || localStorage.getItem('token') || '';

const formatPrice = (amount, currency = 'EUR') => {
  const value = Number(amount || 0);
  if (!Number.isFinite(value) || value <= 0) return '-';
  return new Intl.NumberFormat('tr-TR', { style: 'currency', currency, maximumFractionDigits: 0 }).format(value);
};

export default function ListingPreview() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [preview, setPreview] = useState(null);

  const listingId = useMemo(() => localStorage.getItem('ilan_ver_listing_id') || '', []);

  const fetchPreview = async () => {
    if (!listingId) {
      setLoading(false);
      setError('Draft bulunamadı. Lütfen detay adımını tamamlayın.');
      return;
    }
    const token = getToken();
    if (!token) {
      navigate('/login');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const res = await fetch(`${API}/v1/listings/vehicle/${listingId}/preview`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail || 'Önizleme yüklenemedi');
      }
      setPreview(data);
    } catch (err) {
      setError(err.message || 'Önizleme yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPreview();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listingId]);

  const handleSubmitReview = async () => {
    if (!listingId) return;
    const token = getToken();
    if (!token) {
      navigate('/login');
      return;
    }

    const idempotencyKey = localStorage.getItem('ilan_ver_submit_idempotency_key') || crypto.randomUUID();
    localStorage.setItem('ilan_ver_submit_idempotency_key', idempotencyKey);

    setSubmitting(true);
    setError('');
    setSuccess('');
    try {
      const res = await fetch(`${API}/v1/listings/vehicle/${listingId}/submit-review`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Idempotency-Key': idempotencyKey,
        },
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail || 'Onaya gönderilemedi');
      }
      setSuccess('İlan başarıyla admin onay kuyruğuna gönderildi.');
      setPreview((prev) => (prev ? { ...prev, status: data.status, flow_state: data.flow_state } : prev));
    } catch (err) {
      setError(err.message || 'Onaya gönderim sırasında hata oluştu');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6" data-testid="ilan-ver-preview-page">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="ilan-ver-preview-title">İlan Önizleme</h1>
          <p className="text-sm text-slate-600" data-testid="ilan-ver-preview-subtitle">Taslağı kontrol edin, isterseniz doping seçin ve admin onayına gönderin.</p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/ilan-ver/detaylar')}
          className="rounded-md border px-4 py-2 text-sm"
          data-testid="ilan-ver-preview-back-details"
        >
          Detaylara geri dön
        </button>
      </div>

      {loading ? <div className="rounded-lg border bg-white p-4 text-sm" data-testid="ilan-ver-preview-loading">Önizleme yükleniyor...</div> : null}

      {!loading && preview ? (
        <>
          <section className="rounded-xl border bg-white p-4 space-y-3" data-testid="ilan-ver-preview-summary-card">
            <div className="text-sm font-semibold" data-testid="ilan-ver-preview-listing-title">{preview.title || '-'}</div>
            <div className="text-xs text-slate-600" data-testid="ilan-ver-preview-category-path">
              {(preview.selected_category_path || []).map((item) => item?.name).filter(Boolean).join(' > ') || 'Kategori yolu yok'}
            </div>
            <div className="text-sm font-semibold text-blue-700" data-testid="ilan-ver-preview-price">{formatPrice(preview?.price?.amount, preview?.price?.currency || 'EUR')}</div>
            <div className="text-xs text-slate-600" data-testid="ilan-ver-preview-location">Şehir: {preview?.location?.city || '-'}</div>
            <div className="text-xs text-slate-600" data-testid="ilan-ver-preview-contact">İletişim: {preview?.contact?.contact_name || '-'} / {preview?.contact?.contact_phone || '-'}</div>
            <div className="text-xs text-slate-600" data-testid="ilan-ver-preview-flow-state">Durum: {preview.flow_state}</div>
          </section>

          {preview?.cover_media?.file ? (
            <section className="rounded-xl border bg-white p-4" data-testid="ilan-ver-preview-cover-card">
              <div className="text-xs uppercase tracking-[0.2em] text-slate-500" data-testid="ilan-ver-preview-cover-label">Kapak Fotoğrafı</div>
              <img
                src={`${process.env.REACT_APP_BACKEND_URL}/media/listings/${preview.id}/${preview.cover_media.file}`}
                alt="Kapak"
                className="mt-3 h-56 w-full rounded-lg object-cover"
                data-testid="ilan-ver-preview-cover-image"
              />
            </section>
          ) : null}

          {preview?.doping_selection?.enabled ? (
            <section className="rounded-xl border border-indigo-200 bg-indigo-50 p-4" data-testid="ilan-ver-preview-doping-active">
              <div className="text-sm font-semibold text-indigo-800" data-testid="ilan-ver-preview-doping-title">Aktif Doping Seçimi</div>
              <div className="mt-1 text-xs text-indigo-700" data-testid="ilan-ver-preview-doping-value">
                {preview?.doping_selection?.doping_type} / {preview?.doping_selection?.duration_days || 0} gün
              </div>
            </section>
          ) : null}

          <div className="flex flex-wrap justify-end gap-3" data-testid="ilan-ver-preview-actions">
            <button
              type="button"
              onClick={() => navigate('/ilan-ver/doping')}
              className="rounded-md border px-4 py-2 text-sm"
              data-testid="ilan-ver-preview-open-doping"
            >
              Doping Seç
            </button>
            <button
              type="button"
              onClick={handleSubmitReview}
              disabled={submitting}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              data-testid="ilan-ver-preview-submit-review"
            >
              {submitting ? 'Gönderiliyor...' : 'Admin Onayına Gönder'}
            </button>
          </div>
        </>
      ) : null}

      {error ? <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="ilan-ver-preview-error">{error}</div> : null}
      {success ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700" data-testid="ilan-ver-preview-success">{success}</div> : null}
    </div>
  );
}
