import React, { useCallback, useEffect, useMemo, useState } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const DEFAULT_LISTING_DESIGN = {
  step1: {
    rows: 2,
    columns: 4,
    cards: [
      { id: 'vehicle', title: 'Vasıta', description: 'Araç ilanı ver', module_key: 'vehicle', border_color: '#2563eb', image_url: '' },
      { id: 'real_estate', title: 'Emlak', description: 'Emlak ilanı ver', module_key: 'real_estate', border_color: '#059669', image_url: '' },
      { id: 'other', title: 'Diğer', description: 'Genel ilan ver', module_key: 'other', border_color: '#7c3aed', image_url: '' },
    ],
  },
  step2: {
    show_search: true,
    show_breadcrumb: true,
    mobile_stepper: true,
    continue_limit: 5,
    require_leaf_before_continue: true,
  },
  step3: {
    block_order: ['core', 'params', 'address', 'details', 'media', 'contact', 'duration', 'terms'],
    media: {
      max_photos: 20,
      max_videos: 1,
      max_file_size_mb: 2,
      accepted_types: ['image/png', 'image/jpeg', 'image/webp'],
    },
    contact: {
      allow_phone_toggle: true,
      allow_message_toggle: true,
    },
    duration: {
      show_discount_strike: true,
    },
    terms: {
      text: 'İlan verme kurallarını okudum, kabul ediyorum.',
      required: true,
    },
  },
};

const DEFAULT_LISTING_CREATE_CONFIG = {
  apply_modules: ['vehicle', 'real_estate', 'other'],
  country_selector_mode: 'radio',
  postal_code_required: true,
  map_required: true,
  street_selection_required: true,
  require_city: true,
  require_district: false,
  require_neighborhood: false,
  require_latitude: false,
  require_longitude: false,
  require_address_line: true,
};

const DEFAULT_GOOGLE_SETTINGS = {
  key_configured: false,
  api_key_masked: '',
  country_codes: ['DE'],
  country_options: [{ code: 'DE', name: 'Germany' }],
};

const MODULE_OPTIONS = [
  { key: 'vehicle', label: 'Vasıta' },
  { key: 'real_estate', label: 'Emlak' },
  { key: 'other', label: 'Diğer' },
];

export default function AdminListingDesign() {
  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');

  const [listingDesign, setListingDesign] = useState(DEFAULT_LISTING_DESIGN);
  const [listingCreateConfig, setListingCreateConfig] = useState(DEFAULT_LISTING_CREATE_CONFIG);
  const [googleSettings, setGoogleSettings] = useState(DEFAULT_GOOGLE_SETTINGS);
  const [googleApiKeyInput, setGoogleApiKeyInput] = useState('');

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [designRes, createRes, mapsRes] = await Promise.all([
        axios.get(`${API}/admin/site/listing-design`, { headers: authHeader }),
        axios.get(`${API}/admin/system-settings/listing-create`, { headers: authHeader }),
        axios.get(`${API}/admin/system-settings/google-maps`, { headers: authHeader }),
      ]);

      setListingDesign({ ...DEFAULT_LISTING_DESIGN, ...(designRes.data?.config || {}) });
      setListingCreateConfig({ ...DEFAULT_LISTING_CREATE_CONFIG, ...(createRes.data?.config || {}) });
      setGoogleSettings({ ...DEFAULT_GOOGLE_SETTINGS, ...(mapsRes.data || {}) });
    } catch (err) {
      setError(err?.response?.data?.detail || 'İlan tasarım ayarları yüklenemedi');
    } finally {
      setLoading(false);
    }
  }, [authHeader]);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const updateCardField = (cardIndex, key, value) => {
    setListingDesign((prev) => {
      const nextCards = [...(prev.step1?.cards || [])];
      const current = nextCards[cardIndex] || {};
      nextCards[cardIndex] = { ...current, [key]: value };
      return {
        ...prev,
        step1: { ...(prev.step1 || {}), cards: nextCards },
      };
    });
  };

  const addCard = () => {
    setListingDesign((prev) => {
      const cards = [...(prev.step1?.cards || [])];
      cards.push({
        id: `card-${Date.now()}`,
        title: `Yeni Modül ${cards.length + 1}`,
        description: '',
        module_key: 'other',
        border_color: '#334155',
        image_url: '',
      });
      return {
        ...prev,
        step1: { ...(prev.step1 || {}), cards },
      };
    });
  };

  const removeCard = (cardIndex) => {
    setListingDesign((prev) => {
      const cards = [...(prev.step1?.cards || [])];
      cards.splice(cardIndex, 1);
      return {
        ...prev,
        step1: { ...(prev.step1 || {}), cards },
      };
    });
  };

  const handleCardImageUpload = (cardIndex, file) => {
    if (!file) return;
    if (file.size > 2 * 1024 * 1024) {
      setError('Görsel 2MB üstü olamaz');
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      updateCardField(cardIndex, 'image_url', String(reader.result || ''));
    };
    reader.readAsDataURL(file);
  };

  const toggleApplyModule = (moduleKey) => {
    setListingCreateConfig((prev) => {
      const next = new Set(prev.apply_modules || []);
      if (next.has(moduleKey)) next.delete(moduleKey);
      else next.add(moduleKey);
      return {
        ...prev,
        apply_modules: Array.from(next),
      };
    });
  };

  const toggleCountryCode = (code) => {
    setGoogleSettings((prev) => {
      const next = new Set(prev.country_codes || []);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return {
        ...prev,
        country_codes: Array.from(next),
      };
    });
  };

  const saveAll = async () => {
    setSaving(true);
    setError('');
    setStatus('');
    try {
      await axios.put(
        `${API}/admin/site/listing-design`,
        { config: listingDesign },
        { headers: authHeader }
      );

      await axios.post(
        `${API}/admin/system-settings/listing-create`,
        listingCreateConfig,
        { headers: authHeader }
      );

      await axios.post(
        `${API}/admin/system-settings/google-maps`,
        {
          api_key: googleApiKeyInput.trim() || null,
          country_codes: googleSettings.country_codes || [],
        },
        { headers: authHeader }
      );

      setGoogleApiKeyInput('');
      setStatus('İlan tasarım ayarları kaydedildi ve webe yansıtıldı.');
      await fetchAll();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Kayıt başarısız');
    } finally {
      setSaving(false);
    }
  };

  const clearMapsKey = async () => {
    setSaving(true);
    setError('');
    setStatus('');
    try {
      await axios.post(
        `${API}/admin/system-settings/google-maps`,
        {
          api_key: null,
          clear_api_key: true,
          country_codes: googleSettings.country_codes || ['DE'],
        },
        { headers: authHeader }
      );
      setStatus('Google Maps key temizlendi.');
      await fetchAll();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Key temizlenemedi');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-sm text-slate-500" data-testid="admin-listing-design-loading">İlan Tasarım yükleniyor…</div>;
  }

  return (
    <div className="space-y-6" data-testid="admin-listing-design-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="admin-listing-design-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="admin-listing-design-title">İlan Tasarım</h1>
          <p className="text-sm text-slate-600" data-testid="admin-listing-design-subtitle">PDF’teki 8 adımı admin panelden yönet.</p>
        </div>
        <div className="flex items-center gap-2" data-testid="admin-listing-design-actions">
          <button type="button" onClick={fetchAll} className="rounded-md border px-3 py-2 text-sm" data-testid="admin-listing-design-refresh">Yenile</button>
          <button type="button" onClick={saveAll} disabled={saving} className="rounded-md bg-slate-900 px-3 py-2 text-sm text-white disabled:opacity-60" data-testid="admin-listing-design-save-all">
            {saving ? 'Kaydediliyor…' : 'Tümünü Kaydet'}
          </button>
        </div>
      </div>

      <section className="rounded-xl border bg-white p-4 space-y-3" data-testid="admin-listing-design-step1-section">
        <h2 className="text-sm font-semibold" data-testid="admin-listing-design-step1-title">1) İlan 1 — Modül Grid</h2>
        <div className="grid gap-3 md:grid-cols-3" data-testid="admin-listing-design-step1-grid-size">
          <label className="text-xs" data-testid="admin-listing-design-step1-rows-wrap">Satır
            <input type="number" min={1} max={6} value={listingDesign.step1?.rows || 2} onChange={(e) => setListingDesign((prev) => ({ ...prev, step1: { ...(prev.step1 || {}), rows: Number(e.target.value) || 2 } }))} className="mt-1 h-9 w-full rounded border px-2" data-testid="admin-listing-design-step1-rows-input" />
          </label>
          <label className="text-xs" data-testid="admin-listing-design-step1-columns-wrap">Sütun
            <input type="number" min={1} max={8} value={listingDesign.step1?.columns || 4} onChange={(e) => setListingDesign((prev) => ({ ...prev, step1: { ...(prev.step1 || {}), columns: Number(e.target.value) || 4 } }))} className="mt-1 h-9 w-full rounded border px-2" data-testid="admin-listing-design-step1-columns-input" />
          </label>
          <div className="flex items-end" data-testid="admin-listing-design-step1-add-card-wrap">
            <button type="button" onClick={addCard} className="h-9 rounded border px-3 text-xs" data-testid="admin-listing-design-step1-add-card">Modül Kutusu Ekle</button>
          </div>
        </div>

        <div className="space-y-3" data-testid="admin-listing-design-step1-cards">
          {(listingDesign.step1?.cards || []).map((card, index) => (
            <div key={card.id || index} className="rounded-lg border p-3 space-y-2" data-testid={`admin-listing-design-step1-card-${index}`}>
              <div className="grid gap-2 md:grid-cols-4">
                <input value={card.title || ''} onChange={(e) => updateCardField(index, 'title', e.target.value)} className="h-9 rounded border px-2 text-xs" placeholder="Başlık" data-testid={`admin-listing-design-step1-card-title-${index}`} />
                <input value={card.description || ''} onChange={(e) => updateCardField(index, 'description', e.target.value)} className="h-9 rounded border px-2 text-xs" placeholder="Açıklama" data-testid={`admin-listing-design-step1-card-description-${index}`} />
                <select value={card.module_key || 'other'} onChange={(e) => updateCardField(index, 'module_key', e.target.value)} className="h-9 rounded border px-2 text-xs" data-testid={`admin-listing-design-step1-card-module-${index}`}>
                  {MODULE_OPTIONS.map((mod) => <option key={mod.key} value={mod.key}>{mod.label}</option>)}
                </select>
                <input value={card.border_color || '#334155'} onChange={(e) => updateCardField(index, 'border_color', e.target.value)} className="h-9 rounded border px-2 text-xs" placeholder="#334155" data-testid={`admin-listing-design-step1-card-border-${index}`} />
              </div>
              <div className="flex flex-wrap items-center gap-2" data-testid={`admin-listing-design-step1-card-image-row-${index}`}>
                <input type="file" accept="image/png,image/jpeg,image/webp" onChange={(e) => handleCardImageUpload(index, e.target.files?.[0])} data-testid={`admin-listing-design-step1-card-image-upload-${index}`} />
                <input value={card.image_url || ''} onChange={(e) => updateCardField(index, 'image_url', e.target.value)} className="h-9 min-w-[280px] flex-1 rounded border px-2 text-xs" placeholder="Görsel URL / dataURL" data-testid={`admin-listing-design-step1-card-image-url-${index}`} />
                <button type="button" onClick={() => removeCard(index)} className="h-9 rounded border border-rose-300 px-2 text-xs text-rose-700" data-testid={`admin-listing-design-step1-card-remove-${index}`}>Sil</button>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-xl border bg-white p-4 space-y-3" data-testid="admin-listing-design-step2-section">
        <h2 className="text-sm font-semibold" data-testid="admin-listing-design-step2-title">2) İlan 2 — Sonsuz Seviye + Arama</h2>
        <div className="grid gap-2 md:grid-cols-2" data-testid="admin-listing-design-step2-toggles">
          {[
            ['show_search', 'Kategori arama açık'],
            ['show_breadcrumb', 'Breadcrumb açık'],
            ['mobile_stepper', 'Mobil stepper açık'],
            ['require_leaf_before_continue', 'Leaf seçmeden devam yok'],
          ].map(([key, label]) => (
            <label key={key} className="inline-flex items-center gap-2 rounded border px-2 py-2 text-xs" data-testid={`admin-listing-design-step2-toggle-wrap-${key}`}>
              <input type="checkbox" checked={Boolean(listingDesign.step2?.[key])} onChange={(e) => setListingDesign((prev) => ({ ...prev, step2: { ...(prev.step2 || {}), [key]: e.target.checked } }))} data-testid={`admin-listing-design-step2-toggle-${key}`} />
              <span>{label}</span>
            </label>
          ))}
          <label className="text-xs" data-testid="admin-listing-design-step2-limit-wrap">Devamını Gör limiti
            <input type="number" min={3} max={20} value={listingDesign.step2?.continue_limit || 5} onChange={(e) => setListingDesign((prev) => ({ ...prev, step2: { ...(prev.step2 || {}), continue_limit: Number(e.target.value) || 5 } }))} className="mt-1 h-9 w-full rounded border px-2" data-testid="admin-listing-design-step2-limit-input" />
          </label>
        </div>
      </section>

      <section className="rounded-xl border bg-white p-4 space-y-3" data-testid="admin-listing-design-step3-section">
        <h2 className="text-sm font-semibold" data-testid="admin-listing-design-step3-title">3) İlan 3 — 8 Blok Form</h2>
        <div className="grid gap-4 lg:grid-cols-2" data-testid="admin-listing-design-step3-grid">
          <div className="space-y-3" data-testid="admin-listing-design-step3-address-config">
            <div className="text-xs font-semibold">4) Adres Blok Kuralları</div>
            <div className="grid gap-2 md:grid-cols-2">
              <label className="text-xs">Ülke seçim tipi
                <select value={listingCreateConfig.country_selector_mode} onChange={(e) => setListingCreateConfig((prev) => ({ ...prev, country_selector_mode: e.target.value }))} className="mt-1 h-9 w-full rounded border px-2" data-testid="admin-listing-design-address-country-mode">
                  <option value="radio">Radio</option>
                  <option value="select">Select</option>
                </select>
              </label>
              <div className="text-xs" data-testid="admin-listing-design-address-module-apply">
                <div className="mb-1 font-medium">Uygulama modülleri</div>
                <div className="flex flex-wrap gap-2">
                  {MODULE_OPTIONS.map((mod) => (
                    <label key={mod.key} className="inline-flex items-center gap-1 rounded border px-2 py-1" data-testid={`admin-listing-design-address-module-wrap-${mod.key}`}>
                      <input type="checkbox" checked={(listingCreateConfig.apply_modules || []).includes(mod.key)} onChange={() => toggleApplyModule(mod.key)} data-testid={`admin-listing-design-address-module-${mod.key}`} />
                      {mod.label}
                    </label>
                  ))}
                </div>
              </div>
            </div>
            <div className="grid gap-2 md:grid-cols-2" data-testid="admin-listing-design-address-requirements">
              {[
                ['postal_code_required', 'Posta kodu zorunlu'],
                ['map_required', 'Harita zorunlu'],
                ['street_selection_required', 'Sokak seçimi zorunlu'],
                ['require_city', 'İl zorunlu'],
                ['require_district', 'İlçe zorunlu'],
                ['require_neighborhood', 'Mahalle zorunlu'],
                ['require_latitude', 'Lat zorunlu'],
                ['require_longitude', 'Lng zorunlu'],
                ['require_address_line', 'Adres satırı zorunlu'],
              ].map(([key, label]) => (
                <label key={key} className="inline-flex items-center gap-2 rounded border px-2 py-2 text-xs" data-testid={`admin-listing-design-address-toggle-wrap-${key}`}>
                  <input type="checkbox" checked={Boolean(listingCreateConfig[key])} onChange={(e) => setListingCreateConfig((prev) => ({ ...prev, [key]: e.target.checked }))} data-testid={`admin-listing-design-address-toggle-${key}`} />
                  <span>{label}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="space-y-3" data-testid="admin-listing-design-step3-google-config">
            <div className="text-xs font-semibold">Google Maps Key + Ülke Listesi</div>
            <input value={googleApiKeyInput} onChange={(e) => setGoogleApiKeyInput(e.target.value)} placeholder={googleSettings.api_key_masked || 'GOOGLE_MAPS_API_KEY'} className="h-9 w-full rounded border px-2 text-xs" data-testid="admin-listing-design-google-key-input" />
            <div className="text-[11px] text-slate-500" data-testid="admin-listing-design-google-key-hint">Mevcut: {googleSettings.api_key_masked || 'tanımsız'}</div>
            <div className="flex flex-wrap gap-2" data-testid="admin-listing-design-google-country-options">
              {(googleSettings.country_options || []).map((country) => (
                <label key={country.code} className="inline-flex items-center gap-1 rounded border px-2 py-1 text-xs" data-testid={`admin-listing-design-google-country-wrap-${country.code}`}>
                  <input type="checkbox" checked={(googleSettings.country_codes || []).includes(country.code)} onChange={() => toggleCountryCode(country.code)} data-testid={`admin-listing-design-google-country-${country.code}`} />
                  {country.name} ({country.code})
                </label>
              ))}
            </div>
            <button type="button" onClick={clearMapsKey} className="h-9 rounded border border-rose-300 px-3 text-xs text-rose-700" data-testid="admin-listing-design-google-key-clear">Key’i Temizle</button>
          </div>

          <div className="space-y-2" data-testid="admin-listing-design-step3-media-config">
            <div className="text-xs font-semibold">5) Foto + Video</div>
            <div className="grid gap-2 md:grid-cols-3">
              <label className="text-xs">Max foto
                <input type="number" min={1} max={40} value={listingDesign.step3?.media?.max_photos || 20} onChange={(e) => setListingDesign((prev) => ({ ...prev, step3: { ...(prev.step3 || {}), media: { ...(prev.step3?.media || {}), max_photos: Number(e.target.value) || 20 } } }))} className="mt-1 h-9 w-full rounded border px-2" data-testid="admin-listing-design-media-max-photos" />
              </label>
              <label className="text-xs">Max video
                <input type="number" min={0} max={5} value={listingDesign.step3?.media?.max_videos || 1} onChange={(e) => setListingDesign((prev) => ({ ...prev, step3: { ...(prev.step3 || {}), media: { ...(prev.step3?.media || {}), max_videos: Number(e.target.value) || 1 } } }))} className="mt-1 h-9 w-full rounded border px-2" data-testid="admin-listing-design-media-max-videos" />
              </label>
              <label className="text-xs">Max MB
                <input type="number" min={1} max={20} value={listingDesign.step3?.media?.max_file_size_mb || 2} onChange={(e) => setListingDesign((prev) => ({ ...prev, step3: { ...(prev.step3 || {}), media: { ...(prev.step3?.media || {}), max_file_size_mb: Number(e.target.value) || 2 } } }))} className="mt-1 h-9 w-full rounded border px-2" data-testid="admin-listing-design-media-max-size" />
              </label>
            </div>
          </div>

          <div className="space-y-2" data-testid="admin-listing-design-step3-contact-config">
            <div className="text-xs font-semibold">6) İletişim Bilgileri</div>
            <label className="inline-flex items-center gap-2 rounded border px-2 py-2 text-xs" data-testid="admin-listing-design-contact-phone-toggle-wrap">
              <input type="checkbox" checked={Boolean(listingDesign.step3?.contact?.allow_phone_toggle)} onChange={(e) => setListingDesign((prev) => ({ ...prev, step3: { ...(prev.step3 || {}), contact: { ...(prev.step3?.contact || {}), allow_phone_toggle: e.target.checked } } }))} data-testid="admin-listing-design-contact-phone-toggle" />
              Telefon izni togglesı
            </label>
            <label className="inline-flex items-center gap-2 rounded border px-2 py-2 text-xs" data-testid="admin-listing-design-contact-message-toggle-wrap">
              <input type="checkbox" checked={Boolean(listingDesign.step3?.contact?.allow_message_toggle)} onChange={(e) => setListingDesign((prev) => ({ ...prev, step3: { ...(prev.step3 || {}), contact: { ...(prev.step3?.contact || {}), allow_message_toggle: e.target.checked } } }))} data-testid="admin-listing-design-contact-message-toggle" />
              Mesaj izni togglesı
            </label>
          </div>

          <div className="space-y-2" data-testid="admin-listing-design-step3-duration-config">
            <div className="text-xs font-semibold">7) İlan Süresi/Fiyat</div>
            <label className="inline-flex items-center gap-2 rounded border px-2 py-2 text-xs" data-testid="admin-listing-design-duration-discount-wrap">
              <input type="checkbox" checked={Boolean(listingDesign.step3?.duration?.show_discount_strike)} onChange={(e) => setListingDesign((prev) => ({ ...prev, step3: { ...(prev.step3 || {}), duration: { ...(prev.step3?.duration || {}), show_discount_strike: e.target.checked } } }))} data-testid="admin-listing-design-duration-discount-toggle" />
              İndirim çizgisi göster
            </label>
          </div>

          <div className="space-y-2" data-testid="admin-listing-design-step3-terms-config">
            <div className="text-xs font-semibold">8) Onay Kutusu</div>
            <textarea value={listingDesign.step3?.terms?.text || ''} onChange={(e) => setListingDesign((prev) => ({ ...prev, step3: { ...(prev.step3 || {}), terms: { ...(prev.step3?.terms || {}), text: e.target.value } } }))} className="min-h-[80px] w-full rounded border px-2 py-2 text-xs" data-testid="admin-listing-design-terms-text" />
            <label className="inline-flex items-center gap-2 rounded border px-2 py-2 text-xs" data-testid="admin-listing-design-terms-required-wrap">
              <input type="checkbox" checked={Boolean(listingDesign.step3?.terms?.required)} onChange={(e) => setListingDesign((prev) => ({ ...prev, step3: { ...(prev.step3 || {}), terms: { ...(prev.step3?.terms || {}), required: e.target.checked } } }))} data-testid="admin-listing-design-terms-required" />
              Onay kutusu zorunlu
            </label>
          </div>
        </div>
      </section>

      {status ? <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700" data-testid="admin-listing-design-status">{status}</div> : null}
      {error ? <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700" data-testid="admin-listing-design-error">{error}</div> : null}
    </div>
  );
}
