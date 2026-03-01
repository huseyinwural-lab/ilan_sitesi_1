import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const FORM_STORAGE_KEY = 'ilan_ver_listing_form';
const AUTOCOMPLETE_DEBOUNCE_MS = 450;

const getToken = () => localStorage.getItem('access_token') || localStorage.getItem('token') || '';

const getOrCreateSessionId = () => {
  const existing = localStorage.getItem('ilan_ver_session_id');
  if (existing) return existing;
  const next = `ilan-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  localStorage.setItem('ilan_ver_session_id', next);
  return next;
};

const readJson = (key, fallback) => {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    return JSON.parse(raw);
  } catch (_err) {
    return fallback;
  }
};

const normalizeDurationOptions = (rawOptions = []) => {
  const options = [];
  rawOptions.forEach((item) => {
    const type = String(item?.doping_type || 'none');
    const label = String(item?.label || 'Standart');
    const basePrice = Math.max(0, Number(item?.price_eur || 0));
    const durations = Array.isArray(item?.durations) ? item.durations : [];
    durations.forEach((duration) => {
      const days = Math.max(0, Number(duration || 0));
      if (days <= 0) return;
      const oldPrice = Math.max(basePrice, Math.round(basePrice * 1.25));
      options.push({
        id: `${type}-${days}`,
        package_key: type,
        label,
        days,
        price_eur: basePrice,
        old_price_eur: oldPrice,
      });
    });
  });

  if (options.length === 0) {
    return [
      { id: 'default-30', package_key: 'standard', label: 'Standart', days: 30, price_eur: 0, old_price_eur: 0 },
      { id: 'default-60', package_key: 'standard', label: 'Standart+', days: 60, price_eur: 9, old_price_eur: 12 },
      { id: 'default-90', package_key: 'premium', label: 'Premium', days: 90, price_eur: 19, old_price_eur: 25 },
    ];
  }

  return options;
};

export default function ListingDetails() {
  const navigate = useNavigate();

  const selectedCategory = useMemo(() => readJson('ilan_ver_category', null), []);
  const selectedVehicle = useMemo(() => readJson('ilan_ver_vehicle_selection', null), []);
  const selectedPath = useMemo(() => {
    const parsed = readJson('ilan_ver_category_path', []);
    return Array.isArray(parsed) ? parsed : [];
  }, []);

  const [listingId, setListingId] = useState(() => localStorage.getItem('ilan_ver_listing_id') || '');
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [schemaError, setSchemaError] = useState('');
  const [categorySchema, setCategorySchema] = useState(null);
  const [durationOptions, setDurationOptions] = useState([]);
  const [durationLoading, setDurationLoading] = useState(false);
  const [draftLoading, setDraftLoading] = useState(false);
  const [uploadingMedia, setUploadingMedia] = useState(false);
  const [mediaItems, setMediaItems] = useState([]);
  const [loadingContinue, setLoadingContinue] = useState(false);
  const [error, setError] = useState('');
  const [autosaveInfo, setAutosaveInfo] = useState({ status: 'idle', block: '', message: '' });
  const [placesConfig, setPlacesConfig] = useState({ real_mode: false, mode: 'fallback', key_source: 'none', country_options: [] });
  const [placesConfigLoading, setPlacesConfigLoading] = useState(false);
  const [placesLoading, setPlacesLoading] = useState(false);
  const [placesError, setPlacesError] = useState('');
  const [placeSuggestions, setPlaceSuggestions] = useState([]);
  const [postalLookupItem, setPostalLookupItem] = useState(null);
  const [selectedStreetPlaceId, setSelectedStreetPlaceId] = useState('');

  const [acceptedTerms, setAcceptedTerms] = useState(() => {
    const raw = readJson(FORM_STORAGE_KEY, {});
    return Boolean(raw.accepted_terms);
  });

  const [form, setForm] = useState(() => {
    const raw = readJson(FORM_STORAGE_KEY, {});
    return {
      title: raw.title || '',
      description: raw.description || '',
      price: raw.price || '',
      city: raw.city || '',
      address_country: (raw.address_country || localStorage.getItem('selected_country') || 'DE').toUpperCase(),
      postal_code: raw.postal_code || '',
      district: raw.district || '',
      neighborhood: raw.neighborhood || '',
      latitude: raw.latitude || '',
      longitude: raw.longitude || '',
      address_line: raw.address_line || '',
      google_autocomplete_query: raw.google_autocomplete_query || '',
      contact_name: raw.contact_name || '',
      contact_phone: raw.contact_phone || '',
      allow_phone: raw.allow_phone !== false,
      allow_message: raw.allow_message !== false,
      dynamic_values: raw.dynamic_values || {},
      detail_values: raw.detail_values || {},
      video_url: raw.video_url || '',
      duration_key: raw.duration_key || '',
      duration_days: Number(raw.duration_days || 0),
      duration_price_eur: Number(raw.duration_price_eur || 0),
      duration_old_price_eur: Number(raw.duration_old_price_eur || 0),
    };
  });

  const saveFormLocal = useCallback((updater) => {
    setForm((prev) => {
      const next = typeof updater === 'function' ? updater(prev) : { ...prev, ...updater };
      localStorage.setItem(FORM_STORAGE_KEY, JSON.stringify({ ...next, accepted_terms: acceptedTerms }));
      return next;
    });
  }, [acceptedTerms]);

  const updateTerms = useCallback((checked) => {
    setAcceptedTerms(checked);
    const raw = readJson(FORM_STORAGE_KEY, {});
    localStorage.setItem(FORM_STORAGE_KEY, JSON.stringify({ ...raw, accepted_terms: checked }));
  }, []);

  const trackEvent = useCallback(async (eventName, metadata = {}) => {
    try {
      const token = getToken();
      const sessionId = getOrCreateSessionId();
      await fetch(`${API}/analytics/events`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          event_name: String(eventName || '').toLowerCase(),
          session_id: sessionId,
          page: 'listing_details',
          metadata,
        }),
      });
    } catch (_err) {
      // ignore analytics errors
    }
  }, []);

  const pathLabel = useMemo(() => {
    if (selectedPath.length > 0) {
      return selectedPath.map((item) => item?.name).filter(Boolean).join(' > ');
    }
    return selectedCategory?.name || 'Kategori seçilmedi';
  }, [selectedCategory?.name, selectedPath]);

  const moduleConfig = useMemo(() => {
    return categorySchema?.modules && typeof categorySchema.modules === 'object'
      ? categorySchema.modules
      : {};
  }, [categorySchema]);

  const schemaReady = Boolean(categorySchema && !schemaError);
  const dynamicFields = useMemo(() => (Array.isArray(categorySchema?.dynamic_fields) ? categorySchema.dynamic_fields : []), [categorySchema]);
  const detailGroups = useMemo(() => (Array.isArray(categorySchema?.detail_groups) ? categorySchema.detail_groups : []), [categorySchema]);
  const dynamicBlockEnabled = schemaReady && dynamicFields.length > 0;
  const detailBlockEnabled = schemaReady && detailGroups.length > 0;
  const addressBlockEnabled = schemaReady && (moduleConfig.address?.enabled !== false);
  const photoBlockEnabled = schemaReady && (moduleConfig.photos?.enabled !== false);
  const contactBlockEnabled = schemaReady && (moduleConfig.contact?.enabled !== false);
  const durationBlockEnabled = schemaReady && (moduleConfig.payment?.enabled !== false);
  const googleAutocompleteEnabled = Boolean(placesConfig.real_mode);
  const googleModeLabel = placesConfig.real_mode ? 'Real API (Admin Key)' : 'Fallback';
  const countryRadioOptions = useMemo(() => {
    const options = Array.isArray(placesConfig.country_options) ? placesConfig.country_options : [];
    if (options.length > 0) return options;
    return [{ code: 'DE', name: 'Germany' }];
  }, [placesConfig.country_options]);

  const buildVehiclePayload = useCallback(() => {
    if (!selectedVehicle) return null;
    return {
      ...selectedVehicle,
      vehicle_trim_id: selectedVehicle.trim_id || null,
      trim_id: selectedVehicle.trim_id || null,
      trim_key: selectedVehicle.trim_key || localStorage.getItem('ilan_ver_vehicle_trim_key') || null,
      manual_trim_text: selectedVehicle.manual_trim || null,
    };
  }, [selectedVehicle]);

  const buildDetailGroupsPayload = useCallback((detailMap) => {
    return detailGroups.map((group) => {
      const groupId = group?.id || group?.title;
      const selected = Array.isArray(detailMap?.[groupId]) ? detailMap[groupId] : [];
      return {
        id: groupId,
        title: group?.title || groupId,
        required: Boolean(group?.required),
        selected,
      };
    });
  }, [detailGroups]);

  const ensureDraft = useCallback(async (token) => {
    if (listingId) return listingId;
    if (!selectedCategory?.id) {
      throw new Error('Kategori bilgisi eksik. Lütfen önce kategori seçin.');
    }

    const payload = {
      category_id: selectedCategory.id,
      country: (form.address_country || localStorage.getItem('selected_country') || 'DE').toUpperCase(),
      selected_category_path: selectedPath,
    };
    const vehiclePayload = buildVehiclePayload();
    if (vehiclePayload) payload.vehicle = vehiclePayload;

    const res = await fetch(`${API}/v1/listings/vehicle`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data?.detail?.message || data?.detail || 'Draft oluşturulamadı');
    }

    const nextId = String(data?.id || '');
    if (!nextId) throw new Error('Draft kimliği üretilemedi');
    setListingId(nextId);
    localStorage.setItem('ilan_ver_listing_id', nextId);
    return nextId;
  }, [buildVehiclePayload, form.address_country, listingId, selectedCategory?.id, selectedPath]);

  const patchDraft = useCallback(async (blockKey, payload, options = {}) => {
    const { silent = false } = options;
    const token = getToken();
    if (!token) {
      navigate('/login');
      throw new Error('Oturum bulunamadı');
    }

    try {
      setAutosaveInfo({ status: 'saving', block: blockKey, message: 'Kaydediliyor...' });
      const ensuredId = await ensureDraft(token);
      const res = await fetch(`${API}/v1/listings/vehicle/${ensuredId}/draft`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail?.message || data?.detail || 'Draft kaydı başarısız');
      }
      setAutosaveInfo({
        status: 'saved',
        block: blockKey,
        message: `Kaydedildi • ${new Date().toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}`,
      });
      return ensuredId;
    } catch (err) {
      setAutosaveInfo({ status: 'error', block: blockKey, message: err.message || 'Kaydedilemedi' });
      if (!silent) setError(err.message || 'Kaydedilemedi');
      throw err;
    }
  }, [ensureDraft, navigate]);

  const saveCoreBlock = useCallback(async () => {
    const vehiclePayload = buildVehiclePayload();
    await patchDraft('core_fields', {
      core_fields: {
        title: form.title,
        description: form.description,
        price: {
          price_type: 'FIXED',
          amount: Number(form.price || 0),
          currency_primary: 'EUR',
        },
      },
      selected_category_path: selectedPath,
      ...(vehiclePayload ? { vehicle: vehiclePayload } : {}),
    }, { silent: true });
  }, [buildVehiclePayload, form.description, form.price, form.title, patchDraft, selectedPath]);

  const saveDynamicBlock = useCallback(async () => {
    if (!dynamicBlockEnabled) return;
    await patchDraft('dynamic_fields', {
      dynamic_fields: form.dynamic_values,
      selected_category_path: selectedPath,
    }, { silent: true });
  }, [dynamicBlockEnabled, form.dynamic_values, patchDraft, selectedPath]);

  const saveAddressBlock = useCallback(async () => {
    if (!addressBlockEnabled) return;
    await patchDraft('address', {
      location: {
        city: form.city,
        country: (form.address_country || localStorage.getItem('selected_country') || 'DE').toUpperCase(),
        postal_code: form.postal_code,
        district: form.district,
        neighborhood: form.neighborhood,
        latitude: form.latitude === '' ? null : Number(form.latitude),
        longitude: form.longitude === '' ? null : Number(form.longitude),
        address_line: form.address_line,
      },
      selected_category_path: selectedPath,
    }, { silent: true });
  }, [
    addressBlockEnabled,
    form.address_line,
    form.address_country,
    form.city,
    form.district,
    form.latitude,
    form.longitude,
    form.neighborhood,
    form.postal_code,
    patchDraft,
    selectedPath,
  ]);

  const saveDetailGroupsBlock = useCallback(async (overrideMap) => {
    if (!detailBlockEnabled) return;
    const detailMap = overrideMap || form.detail_values;
    await patchDraft('detail_groups', {
      detail_groups: buildDetailGroupsPayload(detailMap),
      selected_category_path: selectedPath,
    }, { silent: true });
  }, [buildDetailGroupsPayload, detailBlockEnabled, form.detail_values, patchDraft, selectedPath]);

  const saveMediaBlock = useCallback(async () => {
    if (!photoBlockEnabled) return;
    await patchDraft('media', {
      modules: {
        image_count: mediaItems.length,
        video_url: form.video_url || null,
      },
      selected_category_path: selectedPath,
    }, { silent: true });
  }, [form.video_url, mediaItems.length, patchDraft, photoBlockEnabled, selectedPath]);

  const saveContactBlock = useCallback(async () => {
    if (!contactBlockEnabled) return;
    await patchDraft('contact', {
      contact: {
        contact_name: form.contact_name,
        contact_phone: form.contact_phone,
        allow_phone: form.allow_phone,
        allow_message: form.allow_message,
      },
      selected_category_path: selectedPath,
    }, { silent: true });
  }, [contactBlockEnabled, form.allow_message, form.allow_phone, form.contact_name, form.contact_phone, patchDraft, selectedPath]);

  const saveDurationBlock = useCallback(async (payloadOverride) => {
    if (!durationBlockEnabled) return;
    const durationPayload = payloadOverride || {
      listing_duration_key: form.duration_key,
      listing_duration_days: Number(form.duration_days || 0),
      listing_duration_price_eur: Number(form.duration_price_eur || 0),
      listing_duration_old_price_eur: Number(form.duration_old_price_eur || 0),
    };
    await patchDraft('duration', {
      payment_options: durationPayload,
      selected_category_path: selectedPath,
    }, { silent: true });
  }, [durationBlockEnabled, form.duration_days, form.duration_key, form.duration_old_price_eur, form.duration_price_eur, patchDraft, selectedPath]);

  const validateClient = useCallback(() => {
    const issues = [];
    if (!selectedCategory?.id) issues.push('Kategori seçimi bulunamadı.');
    if (!form.title.trim()) issues.push('Başlık zorunludur.');
    if (!form.price || Number(form.price) <= 0) issues.push('Fiyat zorunludur.');
    if (!form.city.trim()) issues.push('Şehir zorunludur.');

    dynamicFields.forEach((field) => {
      if (!field?.required) return;
      const value = form.dynamic_values?.[field.key];
      const isMissing = value === undefined || value === null || value === '' || (Array.isArray(value) && value.length === 0);
      if (isMissing) {
        issues.push(`${field.label || field.key} alanı zorunludur.`);
      }
    });

    detailGroups.forEach((group) => {
      if (!group?.required) return;
      const groupId = group.id || group.title;
      const selected = form.detail_values?.[groupId] || [];
      if (!Array.isArray(selected) || selected.length === 0) {
        issues.push(`${group.title || groupId} alanında en az bir seçim zorunludur.`);
      }
    });

    if (photoBlockEnabled && mediaItems.length === 0) {
      issues.push('En az 1 fotoğraf yüklenmelidir.');
    }
    if (durationBlockEnabled && !form.duration_key) {
      issues.push('İlan süresi seçimi zorunludur.');
    }
    if (!acceptedTerms) {
      issues.push('İlan verme kurallarını kabul etmelisiniz.');
    }

    return issues;
  }, [acceptedTerms, detailGroups, durationBlockEnabled, dynamicFields, form.city, form.detail_values, form.duration_key, form.dynamic_values, form.price, form.title, mediaItems.length, photoBlockEnabled, selectedCategory?.id]);

  const completionBlocks = useMemo(() => {
    const dynamicRequiredMissing = dynamicFields.some((field) => {
      if (!field?.required) return false;
      const value = form.dynamic_values?.[field.key];
      return value === undefined || value === null || value === '' || (Array.isArray(value) && value.length === 0);
    });

    const detailRequiredMissing = detailGroups.some((group) => {
      if (!group?.required) return false;
      const groupId = group.id || group.title;
      const selected = form.detail_values?.[groupId] || [];
      return !Array.isArray(selected) || selected.length === 0;
    });

    const rows = [
      { key: 'core', label: 'Çekirdek alanlar', complete: Boolean(form.title.trim() && Number(form.price || 0) > 0) },
      { key: 'dynamic', label: 'Parametre alanları', complete: !dynamicBlockEnabled || !dynamicRequiredMissing },
      { key: 'address', label: 'Adres formu', complete: !addressBlockEnabled || Boolean(form.city.trim()) },
      { key: 'details', label: 'Detay grupları', complete: !detailBlockEnabled || !detailRequiredMissing },
      { key: 'media', label: 'Foto + Video', complete: !photoBlockEnabled || mediaItems.length > 0 },
      { key: 'contact', label: 'İletişim bilgileri', complete: !contactBlockEnabled || Boolean(form.contact_name.trim() && form.contact_phone.trim()) },
      { key: 'duration', label: 'İlan süresi', complete: !durationBlockEnabled || Boolean(form.duration_key) },
      { key: 'terms', label: 'Onay kutusu', complete: Boolean(acceptedTerms) },
    ];
    return rows;
  }, [
    acceptedTerms,
    addressBlockEnabled,
    contactBlockEnabled,
    detailBlockEnabled,
    detailGroups,
    durationBlockEnabled,
    dynamicBlockEnabled,
    dynamicFields,
    form.city,
    form.contact_name,
    form.contact_phone,
    form.detail_values,
    form.duration_key,
    form.dynamic_values,
    form.price,
    form.title,
    mediaItems.length,
    photoBlockEnabled,
  ]);

  const completionScore = useMemo(() => {
    const total = completionBlocks.length || 1;
    const completed = completionBlocks.filter((item) => item.complete).length;
    return Math.round((completed / total) * 100);
  }, [completionBlocks]);

  const missingChecklist = useMemo(
    () => completionBlocks.filter((item) => !item.complete).map((item) => item.label),
    [completionBlocks]
  );

  const completedAnalyticsRef = useRef(new Set());

  useEffect(() => {
    completionBlocks.forEach((item) => {
      if (item.complete && !completedAnalyticsRef.current.has(item.key)) {
        completedAnalyticsRef.current.add(item.key);
        void trackEvent('block_completed', {
          block_key: item.key,
          listing_id: listingId || null,
          category_id: selectedCategory?.id || null,
          completion_score: completionScore,
        });
      }
    });
  }, [completionBlocks, completionScore, listingId, selectedCategory?.id, trackEvent]);

  useEffect(() => {
    if (!selectedCategory?.id) return;
    const token = getToken();
    if (!token) return;

    const controller = new AbortController();
    const fetchSchema = async () => {
      setSchemaLoading(true);
      setSchemaError('');
      try {
        const country = (form.address_country || localStorage.getItem('selected_country') || 'DE').toUpperCase();
        const params = new URLSearchParams({ category_id: selectedCategory.id, country });
        const res = await fetch(`${API}/catalog/schema?${params.toString()}`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(data?.detail?.message || data?.detail || 'Kategori şeması alınamadı');
        }
        setCategorySchema(data?.schema || null);
      } catch (err) {
        if (err.name === 'AbortError') return;
        setCategorySchema(null);
        setSchemaError(err.message || 'Kategori şeması alınamadı. Bu bloklar admin konfigürasyonu olmadan pasif kalır.');
      } finally {
        setSchemaLoading(false);
      }
    };

    fetchSchema();
    return () => controller.abort();
  }, [form.address_country, selectedCategory?.id]);

  useEffect(() => {
    const token = getToken();
    if (!token) return;

    const fetchDurations = async () => {
      setDurationLoading(true);
      try {
        const res = await fetch(`${API}/v1/listings/doping/options`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error('Süre seçenekleri alınamadı');
        setDurationOptions(normalizeDurationOptions(data?.options || []));
      } catch (_err) {
        setDurationOptions(normalizeDurationOptions([]));
      } finally {
        setDurationLoading(false);
      }
    };

    fetchDurations();
  }, []);

  useEffect(() => {
    const token = getToken();
    if (!token || !listingId) return;

    const fetchDraft = async () => {
      setDraftLoading(true);
      try {
        const res = await fetch(`${API}/v1/listings/vehicle/${listingId}/draft`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) return;
        const item = data?.item;
        if (!item) return;

        const detailMap = {};
        (item.detail_groups || []).forEach((group) => {
          if (!group?.id) return;
          detailMap[group.id] = Array.isArray(group.selected) ? group.selected : [];
        });

        const nextForm = {
          title: item?.core_fields?.title || item?.title || '',
          description: item?.core_fields?.description || item?.description || '',
          price: item?.price?.amount || item?.price_amount || '',
          city: item?.location?.city || '',
          address_country: (item?.location?.country || form.address_country || localStorage.getItem('selected_country') || 'DE').toUpperCase(),
          postal_code: item?.location?.postal_code || '',
          district: item?.location?.district || '',
          neighborhood: item?.location?.neighborhood || '',
          latitude: item?.location?.latitude ?? '',
          longitude: item?.location?.longitude ?? '',
          address_line: item?.location?.address_line || '',
          google_autocomplete_query: form.google_autocomplete_query || '',
          contact_name: item?.contact?.contact_name || '',
          contact_phone: item?.contact?.contact_phone || '',
          allow_phone: item?.contact?.allow_phone !== false,
          allow_message: item?.contact?.allow_message !== false,
          dynamic_values: item?.attributes || {},
          detail_values: Object.keys(detailMap).length ? detailMap : form.detail_values,
          video_url: item?.modules?.video_url || form.video_url || '',
          duration_key: item?.payment_options?.listing_duration_key || form.duration_key || '',
          duration_days: Number(item?.payment_options?.listing_duration_days || form.duration_days || 0),
          duration_price_eur: Number(item?.payment_options?.listing_duration_price_eur || form.duration_price_eur || 0),
          duration_old_price_eur: Number(item?.payment_options?.listing_duration_old_price_eur || form.duration_old_price_eur || 0),
        };
        setForm(nextForm);
        localStorage.setItem(FORM_STORAGE_KEY, JSON.stringify({ ...nextForm, accepted_terms: acceptedTerms }));
        setMediaItems(Array.isArray(item?.media) ? item.media : []);
      } catch (_err) {
        // ignore draft hydrate failures
      } finally {
        setDraftLoading(false);
      }
    };

    fetchDraft();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [listingId]);

  useEffect(() => {
    let active = true;
    const loadPlacesConfig = async () => {
      setPlacesConfigLoading(true);
      try {
        const res = await fetch(`${API}/places/config`);
        const data = await res.json().catch(() => ({}));
        if (!active) return;
        setPlacesConfig({
          real_mode: Boolean(data?.real_mode),
          mode: data?.mode || 'fallback',
          key_source: data?.key_source || 'none',
          country_options: Array.isArray(data?.country_options) ? data.country_options : [],
        });
      } catch (_err) {
        if (!active) return;
        setPlacesConfig({ real_mode: false, mode: 'fallback', key_source: 'none', country_options: [] });
      } finally {
        if (active) setPlacesConfigLoading(false);
      }
    };
    loadPlacesConfig();
    return () => {
      active = false;
    };
  }, []);

  const runPostalLookup = useCallback(async () => {
    if (!addressBlockEnabled) return;
    const postalCode = String(form.postal_code || '').trim();
    const countryCode = String(form.address_country || '').trim().toUpperCase();
    if (postalCode.length < 3 || !countryCode) {
      setPostalLookupItem(null);
      setPlaceSuggestions([]);
      return;
    }

    setPlacesLoading(true);
    setPlacesError('');
    try {
      const params = new URLSearchParams({ postal_code: postalCode, country: countryCode });
      const res = await fetch(`${API}/places/postal-lookup?${params.toString()}`);
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data?.item) {
        throw new Error(data?.message || data?.detail || 'Posta kodu için harita verisi alınamadı');
      }

      const item = data.item;
      setPostalLookupItem(item);
      const streets = Array.isArray(data?.streets) ? data.streets : [];
      setPlaceSuggestions(streets);
      setSelectedStreetPlaceId(streets[0]?.place_id || '');

      saveFormLocal((prev) => ({
        ...prev,
        city: item.city || prev.city,
        district: item.district || prev.district,
        neighborhood: item.neighborhood || prev.neighborhood,
        latitude: item.latitude ?? prev.latitude,
        longitude: item.longitude ?? prev.longitude,
        postal_code: item.postal_code || prev.postal_code,
        address_country: (item.country_code || countryCode || prev.address_country || 'DE').toUpperCase(),
      }));
    } catch (err) {
      setPostalLookupItem(null);
      setPlaceSuggestions([]);
      setPlacesError(err.message || 'Posta kodu lookup başarısız');
    } finally {
      setPlacesLoading(false);
    }
  }, [API, addressBlockEnabled, form.address_country, form.postal_code, saveFormLocal]);

  useEffect(() => {
    if (!addressBlockEnabled) return;
    const postalCode = String(form.postal_code || '').trim();
    if (postalCode.length < 3) {
      setPostalLookupItem(null);
      setPlaceSuggestions([]);
      return;
    }
    const timer = setTimeout(() => {
      void runPostalLookup();
    }, AUTOCOMPLETE_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [addressBlockEnabled, form.address_country, form.postal_code, runPostalLookup]);

  const handleSelectAddressSuggestion = useCallback(async (suggestion) => {
    if (!suggestion?.place_id) return;
    const countryCode = String(form.address_country || localStorage.getItem('selected_country') || 'DE').toUpperCase();
    setPlacesLoading(true);
    setPlacesError('');
    try {
      const params = new URLSearchParams({ place_id: suggestion.place_id, country: countryCode });
      const res = await fetch(`${API}/places/details?${params.toString()}`);
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data?.item) {
        throw new Error(data?.message || data?.detail || 'Sokak detayı alınamadı');
      }

      const location = data.item;
      setSelectedStreetPlaceId(suggestion.place_id);
      saveFormLocal((prev) => ({
        ...prev,
        city: location.city || prev.city,
        district: location.district || prev.district,
        neighborhood: location.neighborhood || prev.neighborhood,
        postal_code: location.postal_code || prev.postal_code,
        address_line: location.formatted_address || suggestion.description || prev.address_line,
        latitude: location.latitude ?? prev.latitude,
        longitude: location.longitude ?? prev.longitude,
        address_country: (location.country_code || countryCode || prev.address_country || 'DE').toUpperCase(),
      }));

      await trackEvent('block_completed', {
        block_key: 'address',
        category_id: selectedCategory?.id,
        listing_id: listingId || null,
        source: 'postal_map_street_selection',
      });
      await saveAddressBlock();
    } catch (err) {
      setPlacesError(err.message || 'Sokak seçimi tamamlanamadı');
    } finally {
      setPlacesLoading(false);
    }
  }, [API, form.address_country, listingId, saveAddressBlock, saveFormLocal, selectedCategory?.id, trackEvent]);

  const handleUploadMedia = async (event) => {
    if (!photoBlockEnabled) return;
    const files = Array.from(event.target.files || []);
    if (files.length === 0) return;
    setError('');

    if ((mediaItems.length + files.length) > 20) {
      setError('En fazla 20 fotoğraf yükleyebilirsiniz.');
      return;
    }

    const invalid = files.find((file) => !file.type.startsWith('image/') || file.size > 2 * 1024 * 1024);
    if (invalid) {
      setError('Sadece png/jpg/webp ve maksimum 2MB dosya yükleyebilirsiniz.');
      return;
    }

    const token = getToken();
    if (!token) {
      navigate('/login');
      return;
    }

    setUploadingMedia(true);
    try {
      const ensuredId = await ensureDraft(token);
      const body = new FormData();
      files.forEach((file) => body.append('files', file));

      const res = await fetch(`${API}/v1/listings/vehicle/${ensuredId}/media`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail?.message || data?.detail || 'Fotoğraf yüklenemedi');
      }
      const nextMedia = Array.isArray(data?.media) ? data.media : [];
      setMediaItems(nextMedia);
      await saveMediaBlock();
    } catch (err) {
      setError(err.message || 'Fotoğraf yüklenemedi');
    } finally {
      setUploadingMedia(false);
      event.target.value = '';
    }
  };

  const handleSetCover = async (mediaId) => {
    if (!listingId || !mediaId) return;
    const token = getToken();
    if (!token) return;
    try {
      const res = await fetch(`${API}/v1/listings/vehicle/${listingId}/media/order`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          order: mediaItems.map((item) => item.media_id).filter(Boolean),
          cover_media_id: mediaId,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) return;
      setMediaItems(Array.isArray(data?.media) ? data.media : mediaItems);
      await saveMediaBlock();
    } catch (_err) {
      // ignore cover reorder failures in UI
    }
  };

  const toggleDetailOption = async (groupId, option) => {
    let nextMap = {};
    saveFormLocal((prev) => {
      const current = Array.isArray(prev.detail_values?.[groupId]) ? prev.detail_values[groupId] : [];
      const exists = current.includes(option);
      const nextValues = exists ? current.filter((item) => item !== option) : [...current, option];
      nextMap = {
        ...(prev.detail_values || {}),
        [groupId]: nextValues,
      };
      return {
        ...prev,
        detail_values: nextMap,
      };
    });
    await saveDetailGroupsBlock(nextMap);
  };

  const handleSelectDuration = async (item) => {
    const nextPayload = {
      listing_duration_key: item.id,
      listing_duration_days: item.days,
      listing_duration_price_eur: item.price_eur,
      listing_duration_old_price_eur: item.old_price_eur,
    };
    saveFormLocal({
      duration_key: item.id,
      duration_days: item.days,
      duration_price_eur: item.price_eur,
      duration_old_price_eur: item.old_price_eur,
    });
    await saveDurationBlock(nextPayload);
  };

  const handleContinue = async () => {
    setError('');
    if (completionScore < 100) {
      setError(`Form tamamlanma oranı %${completionScore}. Lütfen eksik blokları tamamlayın.`);
      await trackEvent('submit_blocked_incomplete', {
        listing_id: listingId || null,
        category_id: selectedCategory?.id || null,
        completion_score: completionScore,
        missing_blocks: missingChecklist,
      });
      return;
    }

    const issues = validateClient();
    if (issues.length > 0) {
      setError(issues[0]);
      return;
    }

    const token = getToken();
    if (!token) {
      navigate('/login');
      return;
    }

    setLoadingContinue(true);
    try {
      const vehiclePayload = buildVehiclePayload();
      const ensuredId = await ensureDraft(token);

      const finalDraftPayload = {
        core_fields: {
          title: form.title,
          description: form.description,
          price: {
            price_type: 'FIXED',
            amount: Number(form.price),
            currency_primary: 'EUR',
          },
        },
        dynamic_fields: form.dynamic_values,
        location: {
          city: form.city,
          country: (form.address_country || localStorage.getItem('selected_country') || 'DE').toUpperCase(),
          postal_code: form.postal_code,
          district: form.district,
          neighborhood: form.neighborhood,
          latitude: form.latitude === '' ? null : Number(form.latitude),
          longitude: form.longitude === '' ? null : Number(form.longitude),
          address_line: form.address_line,
        },
        detail_groups: buildDetailGroupsPayload(form.detail_values),
        modules: {
          image_count: mediaItems.length,
          video_url: form.video_url || null,
        },
        contact: {
          contact_name: form.contact_name,
          contact_phone: form.contact_phone,
          allow_phone: form.allow_phone,
          allow_message: form.allow_message,
        },
        payment_options: {
          listing_duration_key: form.duration_key,
          listing_duration_days: Number(form.duration_days || 0),
          listing_duration_price_eur: Number(form.duration_price_eur || 0),
          listing_duration_old_price_eur: Number(form.duration_old_price_eur || 0),
        },
        selected_category_path: selectedPath,
        ...(vehiclePayload ? { vehicle: vehiclePayload } : {}),
      };

      await patchDraft('finalize', finalDraftPayload);

      const previewReadyRes = await fetch(`${API}/v1/listings/vehicle/${ensuredId}/preview-ready`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          core_fields: finalDraftPayload.core_fields,
          location: finalDraftPayload.location,
          contact: finalDraftPayload.contact,
          selected_category_path: selectedPath,
        }),
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
      setError(err.message || 'Önizleme adımına geçilemedi');
    } finally {
      setLoadingContinue(false);
    }
  };

  const autosaveTone = autosaveInfo.status === 'error'
    ? 'text-rose-600'
    : autosaveInfo.status === 'saved'
      ? 'text-emerald-600'
      : 'text-slate-500';

  return (
    <div className="mx-auto max-w-6xl space-y-6" data-testid="ilan-ver-details-page">
      <div className="flex flex-wrap items-center justify-between gap-4" data-testid="ilan-ver-details-header">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="ilan-ver-details-title">İlan Verme Formu (8 Blok)</h1>
          <p className="text-sm text-slate-600" data-testid="ilan-ver-details-subtitle">Her blok sonrası draft otomatik PATCH ile kaydedilir.</p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/ilan-ver')}
          className="rounded-md border px-4 py-2 text-sm"
          data-testid="ilan-ver-details-back-button"
        >
          Kategoriye geri dön
        </button>
      </div>

      <div className="rounded-xl border bg-white p-4" data-testid="ilan-ver-details-summary-card">
        <div className="text-xs uppercase tracking-[0.2em] text-slate-400" data-testid="ilan-ver-details-breadcrumb-label">Seçim Yolu</div>
        <div className="mt-1 text-sm font-semibold text-slate-900" data-testid="ilan-ver-details-breadcrumb-value">{pathLabel}</div>
        <div className="mt-2 flex flex-wrap items-center gap-4 text-xs" data-testid="ilan-ver-details-status-row">
          <span className="text-slate-500" data-testid="ilan-ver-details-status-draft-id">Draft ID: {listingId || 'Henüz oluşturulmadı'}</span>
          <span className={autosaveTone} data-testid="ilan-ver-details-status-autosave">{autosaveInfo.message || 'Henüz autosave yapılmadı'}</span>
          {(schemaLoading || draftLoading) && (
            <span className="text-slate-500" data-testid="ilan-ver-details-status-loading">Yükleniyor...</span>
          )}
        </div>
      </div>

      {schemaError ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800" data-testid="ilan-ver-details-schema-warning">
          {schemaError}
        </div>
      ) : null}

      <section className="rounded-xl border bg-white p-4 space-y-4" data-testid="ilan-ver-block-core-fields">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-block-core-title">1) Çekirdek Alanlar</h2>
          <button type="button" className="rounded-md border px-3 py-1 text-xs" onClick={saveCoreBlock} data-testid="ilan-ver-block-core-save">Kaydet</button>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-1 text-xs" data-testid="ilan-ver-field-title-wrap">
            <span>İlan Başlığı *</span>
            <input
              value={form.title}
              onChange={(e) => saveFormLocal({ title: e.target.value })}
              onBlur={saveCoreBlock}
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
              onChange={(e) => saveFormLocal({ price: e.target.value })}
              onBlur={saveCoreBlock}
              className="h-10 w-full rounded-md border px-3"
              data-testid="ilan-ver-field-price"
            />
          </label>
        </div>
        <label className="space-y-1 text-xs" data-testid="ilan-ver-field-description-wrap">
          <span>Açıklama</span>
          <textarea
            value={form.description}
            onChange={(e) => saveFormLocal({ description: e.target.value })}
            onBlur={saveCoreBlock}
            className="min-h-[110px] w-full rounded-md border px-3 py-2"
            data-testid="ilan-ver-field-description"
          />
        </label>
      </section>

      <section className="rounded-xl border bg-white p-4 space-y-4" data-testid="ilan-ver-block-dynamic-fields">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-block-dynamic-title">2) Parametre Alanları (Leaf'e bağlı)</h2>
          <button type="button" className="rounded-md border px-3 py-1 text-xs" onClick={saveDynamicBlock} disabled={!dynamicBlockEnabled} data-testid="ilan-ver-block-dynamic-save">Kaydet</button>
        </div>
        {!dynamicBlockEnabled ? (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800" data-testid="ilan-ver-block-dynamic-disabled">
            Parametre bloğu admin konfigürasyonu eksik/pasif olduğu için devre dışı.
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2" data-testid="ilan-ver-dynamic-fields-grid">
            {dynamicFields.map((field) => {
              const key = field.key;
              const value = form.dynamic_values?.[key] ?? '';
              if (field.type === 'select') {
                return (
                  <label className="space-y-1 text-xs" key={key} data-testid={`ilan-ver-dynamic-field-wrap-${key}`}>
                    <span>{field.label}{field.required ? ' *' : ''}</span>
                    <select
                      value={value}
                      onChange={(e) => saveFormLocal((prev) => ({ ...prev, dynamic_values: { ...(prev.dynamic_values || {}), [key]: e.target.value } }))}
                      onBlur={saveDynamicBlock}
                      className="h-10 w-full rounded-md border px-2"
                      data-testid={`ilan-ver-dynamic-field-${key}`}
                    >
                      <option value="">Seçiniz</option>
                      {(field.options || []).map((option) => (
                        <option key={option} value={option}>{option}</option>
                      ))}
                    </select>
                  </label>
                );
              }
              if (field.type === 'radio') {
                return (
                  <div className="space-y-2 text-xs" key={key} data-testid={`ilan-ver-dynamic-field-wrap-${key}`}>
                    <div>{field.label}{field.required ? ' *' : ''}</div>
                    <div className="flex flex-wrap gap-3" data-testid={`ilan-ver-dynamic-radio-group-${key}`}>
                      {(field.options || []).map((option) => (
                        <label key={option} className="inline-flex items-center gap-2" data-testid={`ilan-ver-dynamic-radio-wrap-${key}-${option}`}>
                          <input
                            type="radio"
                            name={`dynamic-radio-${key}`}
                            checked={value === option}
                            onChange={() => saveFormLocal((prev) => ({ ...prev, dynamic_values: { ...(prev.dynamic_values || {}), [key]: option } }))}
                            onBlur={saveDynamicBlock}
                            data-testid={`ilan-ver-dynamic-radio-${key}-${option}`}
                          />
                          {option}
                        </label>
                      ))}
                    </div>
                  </div>
                );
              }
              return (
                <label className="space-y-1 text-xs" key={key} data-testid={`ilan-ver-dynamic-field-wrap-${key}`}>
                  <span>{field.label}{field.required ? ' *' : ''}</span>
                  <input
                    type={field.type === 'number' ? 'number' : 'text'}
                    value={value}
                    onChange={(e) => saveFormLocal((prev) => ({ ...prev, dynamic_values: { ...(prev.dynamic_values || {}), [key]: e.target.value } }))}
                    onBlur={saveDynamicBlock}
                    className="h-10 w-full rounded-md border px-3"
                    data-testid={`ilan-ver-dynamic-field-${key}`}
                  />
                </label>
              );
            })}
          </div>
        )}
      </section>

      <section className="rounded-xl border bg-white p-4 space-y-4" data-testid="ilan-ver-block-address">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-block-address-title">3) Adres Formu</h2>
          <button type="button" className="rounded-md border px-3 py-1 text-xs" onClick={saveAddressBlock} disabled={!addressBlockEnabled} data-testid="ilan-ver-block-address-save">Kaydet</button>
        </div>
        {!addressBlockEnabled ? (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800" data-testid="ilan-ver-block-address-disabled">
            Adres bloğu admin konfigürasyonunda pasif.
          </div>
        ) : (
          <div className="space-y-4" data-testid="ilan-ver-address-fields">
            <div className="rounded-md border bg-slate-50 p-3 text-xs text-slate-700" data-testid="ilan-ver-google-mode-info">
              <div className="font-semibold">Adres Servis Modu</div>
              <div className="mt-1">Mod: {googleModeLabel}</div>
              <div className="mt-1">Kaynak: {placesConfig.key_source || 'none'}</div>
              {placesConfigLoading ? <div className="mt-1 text-slate-500">Config yükleniyor...</div> : null}
            </div>

            <div className="space-y-2" data-testid="ilan-ver-address-country-radio-group">
              <div className="text-xs font-semibold text-slate-700" data-testid="ilan-ver-address-country-radio-label">Ülke Seçimi *</div>
              <div className="grid gap-2 md:grid-cols-2 lg:grid-cols-4" data-testid="ilan-ver-address-country-radio-options">
                {countryRadioOptions.map((option) => (
                  <label
                    key={option.code}
                    className={`inline-flex items-center gap-2 rounded-md border px-3 py-2 text-xs ${form.address_country === option.code ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-slate-200'}`}
                    data-testid={`ilan-ver-address-country-option-wrap-${option.code}`}
                  >
                    <input
                      type="radio"
                      name="ilan-ver-address-country"
                      checked={form.address_country === option.code}
                      onChange={() => saveFormLocal({ address_country: option.code })}
                      data-testid={`ilan-ver-address-country-option-${option.code}`}
                    />
                    <span>{option.name} ({option.code})</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-[1fr_auto]" data-testid="ilan-ver-postal-lookup-row">
              <label className="space-y-1 text-xs" data-testid="ilan-ver-field-postal-code-wrap">
                <span>Posta Kodu *</span>
                <input
                  value={form.postal_code}
                  onChange={(e) => saveFormLocal({ postal_code: e.target.value })}
                  className="h-10 w-full rounded-md border px-3"
                  data-testid="ilan-ver-field-postal-code"
                />
              </label>
              <div className="flex items-end" data-testid="ilan-ver-postal-lookup-action-wrap">
                <button
                  type="button"
                  onClick={() => {
                    void runPostalLookup();
                  }}
                  className="h-10 rounded-md border px-4 text-xs font-semibold"
                  data-testid="ilan-ver-postal-lookup-button"
                >
                  Haritada Aç
                </button>
              </div>
            </div>

            {placesLoading ? (
              <div className="rounded-md border border-slate-200 bg-slate-50 p-2 text-xs text-slate-600" data-testid="ilan-ver-address-autocomplete-loading">
                Posta koduna göre alan ve sokaklar yükleniyor...
              </div>
            ) : null}

            {placesError ? (
              <div className="rounded-md border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700" data-testid="ilan-ver-address-autocomplete-error">
                {placesError}
              </div>
            ) : null}

            {!googleAutocompleteEnabled ? (
              <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800" data-testid="ilan-ver-address-autocomplete-warning">
                Admin panelde Google Maps API key tanımlı değil. Harita/sokak seçimi pasif.
              </div>
            ) : null}

            {postalLookupItem?.map_embed_url ? (
              <div className="space-y-2" data-testid="ilan-ver-postal-map-section">
                <div className="text-xs font-semibold text-slate-700" data-testid="ilan-ver-postal-map-title">Posta Koduna Göre Harita Alanı</div>
                <iframe
                  src={postalLookupItem.map_embed_url}
                  title="Posta kodu haritasi"
                  className="h-64 w-full rounded-md border"
                  loading="lazy"
                  data-testid="ilan-ver-postal-map-iframe"
                />
              </div>
            ) : null}

            {placeSuggestions.length > 0 ? (
              <div className="space-y-2" data-testid="ilan-ver-address-street-list">
                <div className="text-xs font-semibold text-slate-700" data-testid="ilan-ver-address-street-list-title">Harita alanindaki sokaklardan secin</div>
                <div className="max-h-56 space-y-2 overflow-y-auto rounded-md border bg-white p-2" data-testid="ilan-ver-address-suggestions-list">
                  {placeSuggestions.map((item) => (
                    <label
                      key={item.place_id}
                      className={`flex cursor-pointer items-start gap-2 rounded-md border px-3 py-2 text-xs ${selectedStreetPlaceId === item.place_id ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-blue-300'}`}
                      data-testid={`ilan-ver-address-suggestion-wrap-${item.place_id}`}
                    >
                      <input
                        type="radio"
                        name="ilan-ver-street-selection"
                        checked={selectedStreetPlaceId === item.place_id}
                        onChange={() => handleSelectAddressSuggestion(item)}
                        data-testid={`ilan-ver-address-suggestion-${item.place_id}`}
                      />
                      <div>
                        <div className="font-semibold text-slate-800">{item.main_text || item.description}</div>
                        <div className="text-slate-500">{item.secondary_text || item.description}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            ) : null}

            <div className="grid gap-4 md:grid-cols-3">
              <label className="space-y-1 text-xs" data-testid="ilan-ver-field-city-wrap">
                <span>Il *</span>
                <input
                  value={form.city}
                  onChange={(e) => saveFormLocal({ city: e.target.value })}
                  onBlur={saveAddressBlock}
                  className="h-10 w-full rounded-md border px-3"
                  data-testid="ilan-ver-field-city"
                />
              </label>
              <label className="space-y-1 text-xs" data-testid="ilan-ver-field-district-wrap">
                <span>Ilce</span>
                <input
                  value={form.district}
                  onChange={(e) => saveFormLocal({ district: e.target.value })}
                  onBlur={saveAddressBlock}
                  className="h-10 w-full rounded-md border px-3"
                  data-testid="ilan-ver-field-district"
                />
              </label>
              <label className="space-y-1 text-xs" data-testid="ilan-ver-field-neighborhood-wrap">
                <span>Mahalle</span>
                <input
                  value={form.neighborhood}
                  onChange={(e) => saveFormLocal({ neighborhood: e.target.value })}
                  onBlur={saveAddressBlock}
                  className="h-10 w-full rounded-md border px-3"
                  data-testid="ilan-ver-field-neighborhood"
                />
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-2" data-testid="ilan-ver-field-latlng-row">
              <label className="space-y-1 text-xs" data-testid="ilan-ver-field-latitude-wrap">
                <span>Lat</span>
                <input
                  value={form.latitude}
                  onChange={(e) => saveFormLocal({ latitude: e.target.value })}
                  onBlur={saveAddressBlock}
                  className="h-10 w-full rounded-md border px-3"
                  data-testid="ilan-ver-field-latitude"
                />
              </label>
              <label className="space-y-1 text-xs" data-testid="ilan-ver-field-longitude-wrap">
                <span>Lng</span>
                <input
                  value={form.longitude}
                  onChange={(e) => saveFormLocal({ longitude: e.target.value })}
                  onBlur={saveAddressBlock}
                  className="h-10 w-full rounded-md border px-3"
                  data-testid="ilan-ver-field-longitude"
                />
              </label>
            </div>

            <label className="space-y-1 text-xs" data-testid="ilan-ver-field-address-line-wrap">
              <span>Acik Adres</span>
              <input
                value={form.address_line}
                onChange={(e) => saveFormLocal({ address_line: e.target.value })}
                onBlur={saveAddressBlock}
                className="h-10 w-full rounded-md border px-3"
                data-testid="ilan-ver-field-address-line"
              />
            </label>
          </div>
        )}
      </section>

      <section className="rounded-xl border bg-white p-4 space-y-4" data-testid="ilan-ver-block-detail-groups">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-block-detail-title">4) Detay Grupları</h2>
          <button type="button" className="rounded-md border px-3 py-1 text-xs" onClick={() => saveDetailGroupsBlock()} disabled={!detailBlockEnabled} data-testid="ilan-ver-block-detail-save">Kaydet</button>
        </div>
        {!detailBlockEnabled ? (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800" data-testid="ilan-ver-block-detail-disabled">
            Detay grubu admin konfigürasyonunda pasif/eksik.
          </div>
        ) : (
          <div className="space-y-4" data-testid="ilan-ver-detail-groups-list">
            {detailGroups.map((group) => {
              const groupId = group.id || group.title;
              const selected = Array.isArray(form.detail_values?.[groupId]) ? form.detail_values[groupId] : [];
              return (
                <div key={groupId} className="rounded-lg border p-3" data-testid={`ilan-ver-detail-group-${groupId}`}>
                  <div className="text-xs font-semibold text-slate-800" data-testid={`ilan-ver-detail-group-title-${groupId}`}>
                    {group.title}{group.required ? ' *' : ''}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-3" data-testid={`ilan-ver-detail-group-options-${groupId}`}>
                    {(group.options || []).map((option) => (
                      <label key={option} className="inline-flex items-center gap-2 text-xs" data-testid={`ilan-ver-detail-option-wrap-${groupId}-${option}`}>
                        <input
                          type="checkbox"
                          checked={selected.includes(option)}
                          onChange={() => toggleDetailOption(groupId, option)}
                          data-testid={`ilan-ver-detail-option-${groupId}-${option}`}
                        />
                        {option}
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section className="rounded-xl border bg-white p-4 space-y-4" data-testid="ilan-ver-block-media">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-block-media-title">5) Fotoğraf (max 20) + 1 Video</h2>
          <button type="button" className="rounded-md border px-3 py-1 text-xs" onClick={saveMediaBlock} disabled={!photoBlockEnabled} data-testid="ilan-ver-block-media-save">Kaydet</button>
        </div>
        {!photoBlockEnabled ? (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800" data-testid="ilan-ver-block-media-disabled">
            Medya bloğu admin konfigürasyonunda pasif.
          </div>
        ) : (
          <>
            <div className="space-y-2" data-testid="ilan-ver-media-upload-wrap">
              <label className="text-xs" data-testid="ilan-ver-media-upload-label">Fotoğraf Yükle (png/jpg/webp, max 2MB)</label>
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                multiple
                onChange={handleUploadMedia}
                disabled={uploadingMedia || mediaItems.length >= 20}
                data-testid="ilan-ver-media-upload-input"
              />
              <div className="text-xs text-slate-500" data-testid="ilan-ver-media-count">Yüklü: {mediaItems.length} / 20</div>
            </div>

            <div className="grid gap-3 md:grid-cols-2" data-testid="ilan-ver-media-grid">
              {mediaItems.map((item) => {
                const src = item.thumbnail_file
                  ? `${process.env.REACT_APP_BACKEND_URL}/media/listings/${listingId}/${item.thumbnail_file}`
                  : `${process.env.REACT_APP_BACKEND_URL}/media/listings/${listingId}/${item.file}`;
                return (
                  <div key={item.media_id} className="rounded-lg border p-3" data-testid={`ilan-ver-media-item-${item.media_id}`}>
                    <img src={src} alt="Medya" className="h-28 w-full rounded-md object-cover" data-testid={`ilan-ver-media-image-${item.media_id}`} />
                    <label className="mt-2 inline-flex items-center gap-2 text-xs" data-testid={`ilan-ver-media-cover-wrap-${item.media_id}`}>
                      <input
                        type="radio"
                        name="ilan-ver-cover"
                        checked={Boolean(item.is_cover)}
                        onChange={() => handleSetCover(item.media_id)}
                        data-testid={`ilan-ver-media-cover-${item.media_id}`}
                      />
                      Kapak Fotoğrafı
                    </label>
                  </div>
                );
              })}
            </div>

            <label className="space-y-1 text-xs" data-testid="ilan-ver-video-url-wrap">
              <span>Video URL (1 adet)</span>
              <input
                value={form.video_url}
                onChange={(e) => saveFormLocal({ video_url: e.target.value })}
                onBlur={saveMediaBlock}
                placeholder="https://..."
                className="h-10 w-full rounded-md border px-3"
                data-testid="ilan-ver-video-url-input"
              />
            </label>
          </>
        )}
      </section>

      <section className="rounded-xl border bg-white p-4 space-y-4" data-testid="ilan-ver-block-contact">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-block-contact-title">6) İletişim Bilgileri</h2>
          <button type="button" className="rounded-md border px-3 py-1 text-xs" onClick={saveContactBlock} disabled={!contactBlockEnabled} data-testid="ilan-ver-block-contact-save">Kaydet</button>
        </div>
        {!contactBlockEnabled ? (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800" data-testid="ilan-ver-block-contact-disabled">
            İletişim bloğu admin konfigürasyonunda pasif.
          </div>
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-2">
              <label className="space-y-1 text-xs" data-testid="ilan-ver-field-contact-name-wrap">
                <span>İletişim Adı</span>
                <input
                  value={form.contact_name}
                  onChange={(e) => saveFormLocal({ contact_name: e.target.value })}
                  onBlur={saveContactBlock}
                  className="h-10 w-full rounded-md border px-3"
                  data-testid="ilan-ver-field-contact-name"
                />
              </label>
              <label className="space-y-1 text-xs" data-testid="ilan-ver-field-contact-phone-wrap">
                <span>Telefon</span>
                <input
                  value={form.contact_phone}
                  onChange={(e) => saveFormLocal({ contact_phone: e.target.value })}
                  onBlur={saveContactBlock}
                  className="h-10 w-full rounded-md border px-3"
                  data-testid="ilan-ver-field-contact-phone"
                />
              </label>
            </div>
            <div className="flex flex-wrap gap-3 text-xs" data-testid="ilan-ver-field-contact-options">
              <label className="inline-flex items-center gap-2" data-testid="ilan-ver-field-allow-phone-wrap">
                <input
                  type="checkbox"
                  checked={form.allow_phone}
                  onChange={(e) => saveFormLocal({ allow_phone: e.target.checked })}
                  onBlur={saveContactBlock}
                  data-testid="ilan-ver-field-allow-phone"
                />
                Telefon ile iletişime izin ver
              </label>
              <label className="inline-flex items-center gap-2" data-testid="ilan-ver-field-allow-message-wrap">
                <input
                  type="checkbox"
                  checked={form.allow_message}
                  onChange={(e) => saveFormLocal({ allow_message: e.target.checked })}
                  onBlur={saveContactBlock}
                  data-testid="ilan-ver-field-allow-message"
                />
                Mesaj ile iletişime izin ver
              </label>
            </div>
          </>
        )}
      </section>

      <section className="rounded-xl border bg-white p-4 space-y-4" data-testid="ilan-ver-block-duration">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-block-duration-title">7) İlan Süresi</h2>
          <button type="button" className="rounded-md border px-3 py-1 text-xs" onClick={() => saveDurationBlock()} disabled={!durationBlockEnabled} data-testid="ilan-ver-block-duration-save">Kaydet</button>
        </div>
        {!durationBlockEnabled ? (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800" data-testid="ilan-ver-block-duration-disabled">
            Süre/fiyat bloğu admin konfigürasyonunda pasif.
          </div>
        ) : durationLoading ? (
          <div className="text-xs text-slate-500" data-testid="ilan-ver-block-duration-loading">Süre seçenekleri yükleniyor...</div>
        ) : (
          <div className="grid gap-3 md:grid-cols-3" data-testid="ilan-ver-duration-options-grid">
            {durationOptions.map((item) => {
              const selected = form.duration_key === item.id;
              return (
                <button
                  type="button"
                  key={item.id}
                  onClick={() => handleSelectDuration(item)}
                  className={`rounded-lg border px-3 py-3 text-left transition ${selected ? 'border-blue-600 bg-blue-50' : 'border-slate-200 hover:border-blue-400'}`}
                  data-testid={`ilan-ver-duration-option-${item.id}`}
                >
                  <div className="text-xs font-semibold text-slate-700" data-testid={`ilan-ver-duration-option-label-${item.id}`}>{item.label}</div>
                  <div className="mt-1 text-sm font-bold text-slate-900" data-testid={`ilan-ver-duration-option-days-${item.id}`}>{item.days} gün</div>
                  <div className="mt-1 text-xs text-slate-500" data-testid={`ilan-ver-duration-option-pricing-${item.id}`}>
                    <span className="line-through">€{item.old_price_eur}</span>
                    <span className="ml-2 font-semibold text-emerald-700">€{item.price_eur}</span>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </section>

      <section className="rounded-xl border bg-white p-4" data-testid="ilan-ver-block-terms">
        <h2 className="text-sm font-semibold text-slate-900 mb-3" data-testid="ilan-ver-block-terms-title">8) Onay Kutusu</h2>
        <label className="flex items-start gap-3" data-testid="ilan-ver-terms-label">
          <input
            type="checkbox"
            checked={acceptedTerms}
            onChange={(event) => updateTerms(event.target.checked)}
            className="mt-1 h-4 w-4"
            data-testid="ilan-ver-terms-checkbox"
          />
          <span className="text-sm text-slate-700" data-testid="ilan-ver-terms-text">İlan verme kurallarını okudum, kabul ediyorum.</span>
        </label>
      </section>

      <section className="rounded-xl border bg-white p-4 space-y-3" data-testid="ilan-ver-completion-panel">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-completion-title">Form Tamamlanma Durumu</h2>
          <span className="text-xs font-semibold text-slate-700" data-testid="ilan-ver-completion-score">%{completionScore}</span>
        </div>
        <div className="h-2 w-full rounded-full bg-slate-100" data-testid="ilan-ver-completion-progress-track">
          <div
            className="h-2 rounded-full bg-blue-600 transition-all"
            style={{ width: `${completionScore}%` }}
            data-testid="ilan-ver-completion-progress-fill"
          />
        </div>

        <div className="grid gap-2 md:grid-cols-2" data-testid="ilan-ver-completion-checklist-grid">
          {completionBlocks.map((item) => (
            <div
              key={item.key}
              className={`rounded-md border px-3 py-2 text-xs ${item.complete ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-800'}`}
              data-testid={`ilan-ver-completion-item-${item.key}`}
            >
              {item.complete ? '✓' : '•'} {item.label}
            </div>
          ))}
        </div>

        {missingChecklist.length > 0 ? (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800" data-testid="ilan-ver-completion-missing-list">
            Eksik bloklar: {missingChecklist.join(', ')}
          </div>
        ) : null}
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
          disabled={loadingContinue}
          className="rounded-md bg-blue-600 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
          data-testid="ilan-ver-details-continue"
        >
          {loadingContinue ? 'Önizleme hazırlanıyor...' : 'Önizlemeye Geç'}
        </button>
      </div>
    </div>
  );
}
