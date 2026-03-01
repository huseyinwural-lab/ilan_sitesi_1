import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getToken = () => localStorage.getItem('access_token') || localStorage.getItem('token') || '';

export default function ListingDoping() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [options, setOptions] = useState([]);
  const [selection, setSelection] = useState({ doping_type: 'none', duration_days: 0 });

  const listingId = useMemo(() => localStorage.getItem('ilan_ver_listing_id') || '', []);

  const fetchData = async () => {
    if (!listingId) {
      setError('Draft bulunamadı.');
      setLoading(false);
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
      const [optRes, previewRes] = await Promise.all([
        fetch(`${API}/v1/listings/doping/options`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/v1/listings/vehicle/${listingId}/preview`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);

      const optData = await optRes.json().catch(() => ({}));
      const previewData = await previewRes.json().catch(() => ({}));

      if (!optRes.ok) throw new Error(optData?.detail || 'Doping seçenekleri yüklenemedi');
      if (!previewRes.ok) throw new Error(previewData?.detail || 'Önizleme verisi yüklenemedi');

      const current = previewData?.doping_selection || { enabled: false, doping_type: 'none', duration_days: 0 };
      setOptions(Array.isArray(optData?.options) ? optData.options : []);
      setSelection({
        doping_type: current?.enabled ? current.doping_type : 'none',
        duration_days: Number(current?.duration_days || 0),
      });
    } catch (err) {
      setError(err.message || 'Veriler yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listingId]);

  const selectedOption = options.find((item) => item.doping_type === selection.doping_type) || null;

  const saveSelection = async () => {
    if (!listingId) return;
    const token = getToken();
    if (!token) {
      navigate('/login');
      return;
    }

    setSaving(true);
    setError('');
    try {
      const res = await fetch(`${API}/v1/listings/vehicle/${listingId}/doping`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(selection),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail || 'Doping seçimi kaydedilemedi');
      }
      navigate('/ilan-ver/onizleme');
    } catch (err) {
      setError(err.message || 'Doping seçimi kaydedilemedi');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-4xl space-y-6" data-testid="ilan-ver-doping-page">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="ilan-ver-doping-title">Doping Seçimi</h1>
          <p className="text-sm text-slate-600" data-testid="ilan-ver-doping-subtitle">İsterseniz ilanın görünürlüğünü artıracak doping seçin.</p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/ilan-ver/onizleme')}
          className="rounded-md border px-4 py-2 text-sm"
          data-testid="ilan-ver-doping-back-preview"
        >
          Önizlemeye dön
        </button>
      </div>

      {loading ? <div className="rounded-lg border bg-white p-4 text-sm" data-testid="ilan-ver-doping-loading">Seçenekler yükleniyor...</div> : null}

      {!loading ? (
        <div className="grid gap-3 md:grid-cols-3" data-testid="ilan-ver-doping-options-grid">
          {options.map((option) => (
            <button
              type="button"
              key={option.doping_type}
              onClick={() => setSelection((prev) => ({
                doping_type: option.doping_type,
                duration_days: option.durations?.[0] ?? prev.duration_days,
              }))}
              className={`rounded-xl border p-4 text-left ${selection.doping_type === option.doping_type ? 'border-blue-500 bg-blue-50' : 'bg-white'}`}
              data-testid={`ilan-ver-doping-option-${option.doping_type}`}
            >
              <div className="text-sm font-semibold" data-testid={`ilan-ver-doping-option-title-${option.doping_type}`}>{option.label}</div>
              <div className="mt-1 text-xs text-slate-600" data-testid={`ilan-ver-doping-option-desc-${option.doping_type}`}>{option.description}</div>
              <div className="mt-2 text-xs font-semibold text-slate-700" data-testid={`ilan-ver-doping-option-price-${option.doping_type}`}>
                {option.price_eur ? `€${option.price_eur}` : 'Ücretsiz'}
              </div>
            </button>
          ))}
        </div>
      ) : null}

      {selectedOption && selectedOption.doping_type !== 'none' ? (
        <section className="rounded-xl border bg-white p-4" data-testid="ilan-ver-doping-duration-wrap">
          <div className="text-xs uppercase tracking-[0.2em] text-slate-500" data-testid="ilan-ver-doping-duration-label">Süre</div>
          <div className="mt-3 flex flex-wrap gap-2" data-testid="ilan-ver-doping-duration-list">
            {(selectedOption.durations || []).map((day) => (
              <button
                key={day}
                type="button"
                onClick={() => setSelection((prev) => ({ ...prev, duration_days: Number(day) }))}
                className={`rounded-full border px-3 py-1 text-xs ${Number(selection.duration_days) === Number(day) ? 'border-blue-600 bg-blue-50 text-blue-700' : ''}`}
                data-testid={`ilan-ver-doping-duration-${day}`}
              >
                {day} gün
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {error ? <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="ilan-ver-doping-error">{error}</div> : null}

      <div className="flex justify-end" data-testid="ilan-ver-doping-actions">
        <button
          type="button"
          onClick={saveSelection}
          disabled={saving}
          className="rounded-md bg-blue-600 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
          data-testid="ilan-ver-doping-save"
        >
          {saving ? 'Kaydediliyor...' : 'Seçimi Kaydet'}
        </button>
      </div>
    </div>
  );
}
