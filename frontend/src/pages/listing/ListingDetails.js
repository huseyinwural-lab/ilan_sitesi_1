import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const getToken = () => localStorage.getItem('access_token') || localStorage.getItem('token') || '';

const ListingDetails = () => {
  const navigate = useNavigate();
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const selectedCategory = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('ilan_ver_category') || 'null');
    } catch (_e) {
      return null;
    }
  }, []);

  const selectedVehicle = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('ilan_ver_vehicle_selection') || 'null');
    } catch (_e) {
      return null;
    }
  }, []);

  const selectedPath = useMemo(() => {
    try {
      const parsed = JSON.parse(localStorage.getItem('ilan_ver_category_path') || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (_e) {
      return [];
    }
  }, []);

  const pathLabel = selectedPath.length > 0
    ? selectedPath.map((item) => item?.name).filter(Boolean).join(' > ')
    : (selectedCategory?.name || 'Kategori seçilmedi');

  const [form, setForm] = useState(() => {
    try {
      const raw = JSON.parse(localStorage.getItem('ilan_ver_listing_form') || '{}');
      return {
        title: raw.title || '',
        description: raw.description || '',
        price: raw.price || '',
        city: raw.city || '',
        contact_name: raw.contact_name || '',
        contact_phone: raw.contact_phone || '',
        allow_phone: raw.allow_phone !== false,
        allow_message: raw.allow_message !== false,
      };
    } catch (_e) {
      return {
        title: '',
        description: '',
        price: '',
        city: '',
        contact_name: '',
        contact_phone: '',
        allow_phone: true,
        allow_message: true,
      };
    }
  });

  const updateForm = (patch) => {
    setForm((prev) => {
      const next = { ...prev, ...patch };
      localStorage.setItem('ilan_ver_listing_form', JSON.stringify(next));
      return next;
    });
  };

  const handleContinue = async () => {
    setError('');

    if (!acceptedTerms) {
      setError('Devam etmek için kuralları kabul etmelisiniz.');
      return;
    }
    if (!selectedCategory?.id) {
      setError('Kategori bilgisi bulunamadı. Lütfen kategori adımına dönün.');
      return;
    }
    if (!form.title.trim() || !form.price || !form.city.trim()) {
      setError('Başlık, fiyat ve şehir alanları zorunludur.');
      return;
    }

    const token = getToken();
    if (!token) {
      navigate('/login');
      return;
    }

    setLoading(true);
    try {
      let listingId = localStorage.getItem('ilan_ver_listing_id') || '';

      const createPayload = {
        category_id: selectedCategory.id,
        country: (localStorage.getItem('selected_country') || 'DE').toUpperCase(),
        selected_category_path: selectedPath,
      };

      if (selectedVehicle) {
        createPayload.vehicle = {
          ...selectedVehicle,
          vehicle_trim_id: selectedVehicle.trim_id || null,
          manual_trim_text: selectedVehicle.manual_trim || null,
        };
      }

      if (!listingId) {
        const createRes = await fetch(`${API}/v1/listings/vehicle`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(createPayload),
        });

        const createData = await createRes.json().catch(() => ({}));
        if (!createRes.ok) {
          throw new Error(createData?.detail?.message || createData?.detail || 'Draft oluşturulamadı');
        }
        listingId = createData.id;
        localStorage.setItem('ilan_ver_listing_id', listingId);
      }

      const draftPayload = {
        core_fields: {
          title: form.title,
          description: form.description,
          price: {
            price_type: 'FIXED',
            amount: Number(form.price),
            currency_primary: 'EUR',
          },
        },
        selected_category_path: selectedPath,
        location: {
          city: form.city,
          country: (localStorage.getItem('selected_country') || 'DE').toUpperCase(),
        },
        contact: {
          contact_name: form.contact_name,
          contact_phone: form.contact_phone,
          allow_phone: form.allow_phone,
          allow_message: form.allow_message,
        },
      };

      const saveRes = await fetch(`${API}/v1/listings/vehicle/${listingId}/draft`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(draftPayload),
      });
      const saveData = await saveRes.json().catch(() => ({}));
      if (!saveRes.ok) {
        throw new Error(saveData?.detail?.message || saveData?.detail || 'Draft kaydedilemedi');
      }

      const previewReadyRes = await fetch(`${API}/v1/listings/vehicle/${listingId}/preview-ready`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(draftPayload),
      });
      const previewReadyData = await previewReadyRes.json().catch(() => ({}));
      if (!previewReadyRes.ok) {
        const detail = previewReadyData?.detail;
        if (detail?.validation_errors?.length) {
          throw new Error(detail.validation_errors[0]?.message || 'Önizleme doğrulaması başarısız');
        }
        throw new Error(detail || 'Önizleme adımı hazırlanamadı');
      }

      navigate('/ilan-ver/onizleme');
    } catch (err) {
      setError(err.message || 'Beklenmeyen bir hata oluştu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6" data-testid="ilan-ver-details-page">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="ilan-ver-details-title">İlan Verme Formu</h1>
          <p className="text-sm text-slate-600" data-testid="ilan-ver-details-subtitle">Çekirdek alanları doldurup gerçek önizleme adımına geçin.</p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/ilan-ver')}
          className="rounded-md border px-4 py-2 text-sm"
          data-testid="ilan-ver-details-back"
        >
          Kategoriye geri dön
        </button>
      </div>

      <div className="rounded-xl border bg-white p-4 space-y-2" data-testid="ilan-ver-details-summary">
        <div className="text-xs uppercase tracking-[0.2em] text-slate-400" data-testid="ilan-ver-details-breadcrumb-label">Seçim Yolu</div>
        <div className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-details-breadcrumb">{pathLabel}</div>
      </div>

      <section className="rounded-xl border bg-white p-4 space-y-4" data-testid="ilan-ver-details-form-card">
        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-1 text-xs" data-testid="ilan-ver-field-title-wrap">
            <span>İlan Başlığı *</span>
            <input
              value={form.title}
              onChange={(e) => updateForm({ title: e.target.value })}
              className="h-10 w-full rounded-md border px-3"
              data-testid="ilan-ver-field-title"
            />
          </label>

          <label className="space-y-1 text-xs" data-testid="ilan-ver-field-price-wrap">
            <span>Fiyat (EUR) *</span>
            <input
              type="number"
              min="1"
              value={form.price}
              onChange={(e) => updateForm({ price: e.target.value })}
              className="h-10 w-full rounded-md border px-3"
              data-testid="ilan-ver-field-price"
            />
          </label>
        </div>

        <label className="space-y-1 text-xs" data-testid="ilan-ver-field-description-wrap">
          <span>Açıklama</span>
          <textarea
            value={form.description}
            onChange={(e) => updateForm({ description: e.target.value })}
            className="min-h-[110px] w-full rounded-md border px-3 py-2"
            data-testid="ilan-ver-field-description"
          />
        </label>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-1 text-xs" data-testid="ilan-ver-field-city-wrap">
            <span>Şehir *</span>
            <input
              value={form.city}
              onChange={(e) => updateForm({ city: e.target.value })}
              className="h-10 w-full rounded-md border px-3"
              data-testid="ilan-ver-field-city"
            />
          </label>

          <label className="space-y-1 text-xs" data-testid="ilan-ver-field-contact-name-wrap">
            <span>İletişim Adı</span>
            <input
              value={form.contact_name}
              onChange={(e) => updateForm({ contact_name: e.target.value })}
              className="h-10 w-full rounded-md border px-3"
              data-testid="ilan-ver-field-contact-name"
            />
          </label>
        </div>

        <label className="space-y-1 text-xs" data-testid="ilan-ver-field-contact-phone-wrap">
          <span>Telefon</span>
          <input
            value={form.contact_phone}
            onChange={(e) => updateForm({ contact_phone: e.target.value })}
            className="h-10 w-full rounded-md border px-3"
            data-testid="ilan-ver-field-contact-phone"
          />
        </label>

        <div className="flex flex-wrap gap-3 text-xs" data-testid="ilan-ver-field-contact-options">
          <label className="inline-flex items-center gap-2" data-testid="ilan-ver-field-allow-phone-wrap">
            <input
              type="checkbox"
              checked={form.allow_phone}
              onChange={(e) => updateForm({ allow_phone: e.target.checked })}
              data-testid="ilan-ver-field-allow-phone"
            />
            Telefon ile iletişime izin ver
          </label>
          <label className="inline-flex items-center gap-2" data-testid="ilan-ver-field-allow-message-wrap">
            <input
              type="checkbox"
              checked={form.allow_message}
              onChange={(e) => updateForm({ allow_message: e.target.checked })}
              data-testid="ilan-ver-field-allow-message"
            />
            Mesaj ile iletişime izin ver
          </label>
        </div>
      </section>

      <section className="rounded-xl border bg-white p-4" data-testid="ilan-ver-core-section-8">
        <label className="flex items-start gap-3" data-testid="ilan-ver-terms-label">
          <input
            type="checkbox"
            checked={acceptedTerms}
            onChange={(event) => setAcceptedTerms(event.target.checked)}
            className="mt-1 h-4 w-4"
            data-testid="ilan-ver-terms-checkbox"
          />
          <span className="text-sm text-slate-700" data-testid="ilan-ver-terms-text">İlan verme kurallarını okudum, kabul ediyorum.</span>
        </label>
      </section>

      {error ? (
        <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="ilan-ver-details-error">
          {error}
        </div>
      ) : null}

      <div className="flex flex-wrap items-center justify-end gap-3" data-testid="ilan-ver-details-actions">
        <button
          type="button"
          onClick={handleContinue}
          disabled={!acceptedTerms || loading}
          className="rounded-md bg-blue-600 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
          data-testid="ilan-ver-details-continue"
        >
          {loading ? 'Hazırlanıyor...' : 'Önizlemeye Geç'}
        </button>
      </div>
    </div>
  );
};

export default ListingDetails;
