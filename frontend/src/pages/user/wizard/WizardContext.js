import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCountry } from '@/contexts/CountryContext';

const WizardContext = createContext();

export const WizardProvider = ({ children, editListingId = null }) => {
  const navigate = useNavigate();
  const { selectedCountry } = useCountry();
  const [draftId, setDraftId] = useState(null);
  const [step, setStep] = useState(1);
  const [completedSteps, setCompletedSteps] = useState({});
  const [loading, setLoading] = useState(false);
  const [editLoading, setEditLoading] = useState(false);
  const [autosaveStatus, setAutosaveStatus] = useState({
    status: 'idle',
    lastSuccessAt: null,
    lastErrorAt: null,
  });

  const [category, setCategory] = useState(null);
  const moduleKey = useMemo(() => localStorage.getItem('ilan_ver_module') || 'vehicle', []);
  const [validationErrors, setValidationErrors] = useState([]);
  const [publishedDetailUrl, setPublishedDetailUrl] = useState(null);
  const [basicInfo, setBasicInfo] = useState({
    country: 'DE',
    category_key: null,
    category_id: null,
    make_key: null,
    make_id: null,
    make_label: null,
    model_key: null,
    model_id: null,
    model_label: null,
    year: null,
    trim_key: null,
    vehicle_trim_id: null,
    vehicle_trim_label: null,
    manual_trim_flag: false,
    manual_trim_text: null,
    trim_filter_fuel: null,
    trim_filter_body: null,
    trim_filter_transmission: null,
    trim_filter_drive: null,
    trim_filter_engine_type: null,
    mileage_km: null,
    fuel_type: null,
    transmission: null,
    drive_type: null,
    body_type: null,
    color: null,
    damage_status: null,
    engine_cc: null,
    engine_hp: null,
    trade_in: null,
    price_eur: null,
  });
  const [attributes, setAttributes] = useState({});
  const [schema, setSchema] = useState(null);
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [schemaNotice, setSchemaNotice] = useState('');
  const [coreFields, setCoreFields] = useState({
    title: '',
    description: '',
    price_type: 'FIXED',
    price_amount: '',
    price_display: '',
    hourly_rate: '',
    hourly_display: '',
    currency_primary: 'EUR',
    currency_secondary: 'CHF',
    secondary_amount: '',
    secondary_display: '',
    secondary_enabled: false,
    decimal_places: 0,
  });
  const [dynamicValues, setDynamicValues] = useState({});
  const [detailGroups, setDetailGroups] = useState({});
  const [moduleData, setModuleData] = useState({
    address: { street: '', city: '', postal_code: '' },
    contact: { phone: '', allow_phone: true, allow_message: true },
    payment: { package_selected: false, doping_selected: false },
  });
  const [media, setMedia] = useState([]);

  useEffect(() => {
    if (selectedCountry) {
      setBasicInfo((prev) => ({ ...prev, country: selectedCountry }));
    }
  }, [selectedCountry]);

  const loadCategorySchema = useCallback(async (categoryId) => {
    if (!categoryId) return null;
    try {
      setSchemaLoading(true);
      setSchemaNotice('');
      const res = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/catalog/schema?category_id=${categoryId}&country=${selectedCountry || 'DE'}`
      );
      if (!res.ok) {
        const raw = await res.text();
        let detail = 'Schema yüklenemedi';
        try {
          const parsed = JSON.parse(raw);
          detail = parsed?.detail || detail;
        } catch (err) {
          if (raw) detail = raw;
        }
        if (res.status === 409) {
          setSchema(null);
          setSchemaNotice(detail);
          return null;
        }
        throw new Error(detail);
      }
      const data = await res.json();
      setSchema(data.schema);
      setSchemaNotice('');
      const priceConfig = data.schema?.core_fields?.price || {};
      const allowedPriceTypes = priceConfig.allowed_types || (priceConfig.hourly_enabled === false ? ['FIXED'] : ['FIXED', 'HOURLY']);
      setCoreFields((prev) => ({
        ...prev,
        price_type: allowedPriceTypes.includes(prev.price_type) ? prev.price_type : 'FIXED',
        currency_primary: priceConfig.currency_primary || 'EUR',
        currency_secondary: priceConfig.currency_secondary || 'CHF',
        secondary_enabled: priceConfig.secondary_enabled || false,
        decimal_places: priceConfig.decimal_places ?? 0,
      }));
      return data.schema;
    } catch (error) {
      console.error(error);
      setSchemaNotice(error?.message || 'Schema yüklenemedi');
      return null;
    } finally {
      setSchemaLoading(false);
    }
  }, [selectedCountry]);

  const formatDisplay = (amount, decimals = 0) => {
    if (amount === null || amount === undefined || amount === '') return '';
    const value = Number(amount);
    if (Number.isNaN(value)) return '';
    return new Intl.NumberFormat('de-DE', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(value);
  };

  const MIN_MEDIA_COUNT = 3;

  const computeCompletionFromData = (data, schemaData) => {
    if (!data) return {};
    const attrs = data.attributes || {};
    const attributeValues = attrs.attributes || {};
    const vehicleInfo = data.vehicle || attrs.vehicle || {};
    const makeKey = vehicleInfo.make_key || null;
    const modelKey = vehicleInfo.model_key || null;
    const yearValue = vehicleInfo.year || null;
    const normalizedYear = yearValue ? Number(yearValue) : null;
    const trimId = vehicleInfo.vehicle_trim_id || vehicleInfo.trim_id || null;
    const manualTrimFlag = Boolean(vehicleInfo.manual_trim_flag);
    const manualTrimText = (vehicleInfo.manual_trim_text || '').toString().trim();

    const pricePayload = data.price || {};
    const priceType = String(pricePayload.price_type || data.price_type || 'FIXED').toUpperCase();
    const priceValue = priceType === 'HOURLY'
      ? (pricePayload.hourly_rate ?? data.hourly_rate)
      : (pricePayload.amount ?? data.price_amount);

    const moduleInfo = data.modules || attrs.modules || {};
    const addressInfo = moduleInfo.address || {};
    const cityValue = addressInfo.city || null;

    const isVehicleModule = moduleKey === 'vehicle';

    const coreComplete = Boolean(data.title && data.description && priceValue)
      && cityValue
      && (isVehicleModule
        ? (
          attributeValues.mileage_km
          && attributeValues.fuel_type
          && attributeValues.transmission
          && attributeValues.drive_type
          && attributeValues.body_type
          && attributeValues.color
          && attributeValues.damage_status
          && attributeValues.engine_cc
          && attributeValues.engine_hp
          && attributeValues.trade_in !== null
          && attributeValues.trade_in !== undefined
          && attributeValues.trade_in !== ''
        )
        : true);

    const step2Complete = isVehicleModule ? Boolean(makeKey) : true;
    const step3Complete = isVehicleModule ? Boolean(modelKey) : true;
    const step4Complete = isVehicleModule
      ? Boolean(
        normalizedYear
        && (
          (normalizedYear >= 2000 && trimId)
          || (normalizedYear < 2000 && manualTrimFlag && manualTrimText.length > 1)
        )
      )
      : true;
    const dynamicFields = schemaData?.dynamic_fields || [];
    const detailGroups = schemaData?.detail_groups || [];

    const dynamicComplete = dynamicFields.every((field) => {
      if (!field.required) return true;
      const value = attributeValues[field.key];
      return value !== undefined && value !== null && value !== '';
    });

    const detailComplete = detailGroups.every((group) => {
      if (!group.required) return true;
      const selected = (data.detail_groups || attrs.detail_groups || {})[group.id] || [];
      return Array.isArray(selected) && selected.length > 0;
    });

    const mediaCount = (data.media || []).length;
    const featuresComplete = dynamicComplete && detailComplete && mediaCount >= MIN_MEDIA_COUNT;

    return {
      1: Boolean(data.category_id || data.category_key),
      2: step2Complete,
      3: step3Complete,
      4: step4Complete,
      5: Boolean(coreComplete),
      6: Boolean(featuresComplete),
    };
  };

  const getFirstIncompleteStep = (completion) => {
    const requiredSteps = moduleKey === 'vehicle' ? [1, 2, 3, 4, 5, 6] : [1, 5, 6];
    for (let i = 0; i < requiredSteps.length; i += 1) {
      const stepId = requiredSteps[i];
      if (!completion[stepId]) return stepId;
    }
    return 7;
  };

  const hydrateFromListing = async (listing) => {
    if (!listing) return;
    const categoryId = listing.category_id || listing.category_key;
    setCategory({ id: categoryId, name: listing.category_key || 'Kategori', slug: listing.category_slug || null });
    const loadedSchema = await loadCategorySchema(categoryId);

    setDraftId(listing.id);
    window.__WIZARD_DRAFT_ID__ = listing.id;

    const attrs = listing.attributes || {};
    const attributeValues = attrs.attributes || {};
    setAttributes(attributeValues);
    const reserved = new Set([
      'mileage_km',
      'fuel_type',
      'transmission',
      'drive_type',
      'body_type',
      'color',
      'damage_status',
      'engine_cc',
      'engine_hp',
      'trade_in',
      'price_eur',
    ]);
    const dynamic = {};
    Object.entries(attributeValues).forEach(([key, value]) => {
      if (!reserved.has(key)) {
        dynamic[key] = value;
      }
    });

    const priceData = listing.price || {};
    const priceType = String(priceData.price_type || listing.price_type || 'FIXED').toUpperCase();
    const hourlyValue = priceData.hourly_rate ?? listing.hourly_rate;
    setCoreFields((prev) => ({
      ...prev,
      title: listing.title || '',
      description: listing.description || '',
      price_type: priceType,
      price_amount: priceType === 'FIXED' && priceData.amount ? String(priceData.amount) : '',
      price_display: priceType === 'FIXED' && priceData.amount ? formatDisplay(priceData.amount, prev.decimal_places) : '',
      hourly_rate: priceType === 'HOURLY' && hourlyValue ? String(hourlyValue) : '',
      hourly_display: priceType === 'HOURLY' && hourlyValue ? formatDisplay(hourlyValue, prev.decimal_places) : '',
      currency_primary: priceData.currency_primary || prev.currency_primary,
      currency_secondary: priceData.currency_secondary || prev.currency_secondary,
      secondary_amount: priceData.secondary_amount ? String(priceData.secondary_amount) : '',
      secondary_display: priceData.secondary_amount ? formatDisplay(priceData.secondary_amount, prev.decimal_places) : '',
    }));

    const vehicleInfo = listing.vehicle || attrs.vehicle || {};
    setBasicInfo((prev) => ({
      ...prev,
      country: listing.country || prev.country,
      category_key: listing.category_key,
      category_id: listing.category_id,
      make_key: vehicleInfo.make_key || null,
      make_id: vehicleInfo.make_id || null,
      make_label: null,
      model_key: vehicleInfo.model_key || null,
      model_id: vehicleInfo.model_id || null,
      model_label: null,
      year: vehicleInfo.year || null,
      trim_key: vehicleInfo.trim_key || null,
      vehicle_trim_id: vehicleInfo.vehicle_trim_id || vehicleInfo.trim_id || null,
      vehicle_trim_label: vehicleInfo.vehicle_trim_label || null,
      manual_trim_flag: Boolean(vehicleInfo.manual_trim_flag),
      manual_trim_text: vehicleInfo.manual_trim_text || null,
      trim_filter_fuel: vehicleInfo.fuel_type || null,
      trim_filter_body: vehicleInfo.body || null,
      trim_filter_transmission: vehicleInfo.transmission || null,
      trim_filter_drive: vehicleInfo.drive || null,
      trim_filter_engine_type: vehicleInfo.engine_type || null,
      mileage_km: attributeValues.mileage_km || null,
      fuel_type: attributeValues.fuel_type || null,
      transmission: attributeValues.transmission || null,
      drive_type: attributeValues.drive_type || null,
      body_type: attributeValues.body_type || null,
      color: attributeValues.color || null,
      damage_status: attributeValues.damage_status || null,
      engine_cc: attributeValues.engine_cc || null,
      engine_hp: attributeValues.engine_hp || null,
      trade_in: attributeValues.trade_in ?? null,
    }));

    setDynamicValues(dynamic);
    setDetailGroups(listing.detail_groups || attrs.detail_groups || {});
    setModuleData((prev) => ({
      ...prev,
      ...(listing.modules || attrs.modules || {}),
    }));

    const mediaItems = (listing.media || []).map((m) => ({
      media_id: m.media_id,
      file: m.file,
      url: m.url || `/media/listings/${listing.id}/${m.file}`,
      is_cover: Boolean(m.is_cover),
    }));
    setMedia(mediaItems);

    const completion = computeCompletionFromData(listing, loadedSchema);
    setCompletedSteps(completion);
    setStep(getFirstIncompleteStep(completion));
  };

  useEffect(() => {
    if (!editListingId) return;
    const fetchDraft = async () => {
      setEditLoading(true);
      try {
        const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/listings/vehicle/${editListingId}/draft`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
        if (!res.ok) {
          throw new Error('Draft yüklenemedi');
        }
        const data = await res.json();
        await hydrateFromListing(data.item);
      } catch (error) {
        console.error(error);
      } finally {
        setEditLoading(false);
      }
    };
    fetchDraft();
  }, [editListingId]);

  const createDraft = useCallback(async (selectedCategory, options = {}) => {
    const { autoAdvance = false } = options;
    setLoading(true);
    setValidationErrors([]);
    try {
      setCategory(selectedCategory);
      await loadCategorySchema(selectedCategory.id);

      const payload = {
        country: selectedCountry || 'DE',
        category_key: selectedCategory.id,
        category_id: selectedCategory.id,
      };

      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/listings/vehicle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || 'Draft create failed');
      }

      const data = await res.json();
      setDraftId(data.id);
      window.__WIZARD_DRAFT_ID__ = data.id;

      setBasicInfo((prev) => ({
        ...prev,
        country: selectedCountry || 'DE',
        category_key: selectedCategory.id,
        category_id: selectedCategory.id,
        make_key: null,
        make_id: null,
        make_label: null,
        model_key: null,
        model_id: null,
        model_label: null,
        year: null,
        trim_key: null,
        vehicle_trim_id: null,
        vehicle_trim_label: null,
        manual_trim_flag: false,
        manual_trim_text: null,
        trim_filter_fuel: null,
        trim_filter_body: null,
        trim_filter_transmission: null,
        trim_filter_drive: null,
        trim_filter_engine_type: null,
      }));

      if (autoAdvance) {
        setStep(2);
      }

      return true;
    } catch (error) {
      console.error(error);
      setValidationErrors([{ field: 'draft', code: 'DRAFT_CREATE_FAILED', message: 'Draft oluşturulamadı' }]);
      return false;
    } finally {
      setLoading(false);
    }
  }, [loadCategorySchema, selectedCountry]);


  const saveDraft = async (payload) => {
    if (!draftId) return { ok: false };
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/listings/vehicle/${draftId}/draft`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload || {}),
      });
      if (!res.ok) return { ok: false };
      let data = {};
      try {
        data = await res.json();
      } catch (err) {
        data = {};
      }
      return { ok: true, updatedAt: data?.updated_at || data?.updatedAt || null };
    } catch (error) {
      console.error(error);
      return { ok: false };
    }
  };

  const trackWizardEvent = useCallback(async (eventName, metadata = {}) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/analytics/events`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          event_name: eventName,
          metadata,
        }),
      });
    } catch (err) {
      console.error('Analytics event error', err);
    }
  }, []);

  const saveStep = async (data) => {
    setLoading(true);
    setValidationErrors([]);
    try {
      if (step === 2) {
        setBasicInfo((prev) => ({ ...prev, ...data.basic }));
        if (data.basic?.attributes) setAttributes(data.basic.attributes);
        if (data.dynamicValues) setDynamicValues(data.dynamicValues);
        if (data.detailGroups) setDetailGroups(data.detailGroups);
      } else if (step === 3) {
        if (data.coreFields) setCoreFields(data.coreFields);
        if (data.moduleData) setModuleData(data.moduleData);
      } else if (step === 4) {
        setMedia(data);
      }

      if (step === 2 && !draftId) {
        throw new Error('Missing draftId');
      }

      setStep(step + 1);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const publishListing = async () => {
    setLoading(true);
    setValidationErrors([]);
    try {
      if (!draftId) {
        throw new Error('Missing draftId');
      }

      const payload = {
        core_fields: {
          title: coreFields.title,
          description: coreFields.description,
          price: {
            price_type: coreFields.price_type || 'FIXED',
            amount: coreFields.price_type === 'FIXED' && coreFields.price_amount ? Number(coreFields.price_amount) : null,
            hourly_rate: coreFields.price_type === 'HOURLY' && coreFields.hourly_rate ? Number(coreFields.hourly_rate) : null,
            currency_primary: coreFields.currency_primary,
            currency_secondary: coreFields.secondary_enabled && coreFields.price_type === 'FIXED' ? coreFields.currency_secondary : null,
            secondary_amount: coreFields.secondary_enabled && coreFields.price_type === 'FIXED' && coreFields.secondary_amount ? Number(coreFields.secondary_amount) : null,
            decimal_places: coreFields.decimal_places,
          },
        },
        vehicle: {
          make_key: basicInfo.make_key,
          make_id: basicInfo.make_id,
          model_key: basicInfo.model_key,
          model_id: basicInfo.model_id,
          year: basicInfo.year,
          trim_key: basicInfo.trim_key,
          vehicle_trim_id: basicInfo.vehicle_trim_id,
          vehicle_trim_label: basicInfo.vehicle_trim_label,
          manual_trim_flag: Boolean(basicInfo.manual_trim_flag),
          manual_trim_text: basicInfo.manual_trim_text,
          fuel_type: basicInfo.trim_filter_fuel,
          body: basicInfo.trim_filter_body,
          transmission: basicInfo.trim_filter_transmission,
          drive: basicInfo.trim_filter_drive,
          engine_type: basicInfo.trim_filter_engine_type,
        },
        attributes: {
          ...attributes,
          mileage_km: basicInfo.mileage_km,
          fuel_type: basicInfo.fuel_type,
          transmission: basicInfo.transmission,
          drive_type: basicInfo.drive_type,
          body_type: basicInfo.body_type,
          color: basicInfo.color,
          damage_status: basicInfo.damage_status,
          engine_cc: basicInfo.engine_cc,
          engine_hp: basicInfo.engine_hp,
          trade_in: basicInfo.trade_in,
        },
        dynamic_fields: dynamicValues,
        detail_groups: detailGroups,
        modules: moduleData,
        payment_options: {
          package: moduleData.payment?.package_selected,
          doping: moduleData.payment?.doping_selected,
        },
      };
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/listings/vehicle/${draftId}/submit`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (res.status === 422) {
        const payload = await res.json().catch(() => null);
        const detail = payload?.detail;
        const errs = Array.isArray(detail?.validation_errors) ? detail.validation_errors : [];
        setValidationErrors(errs);
        return;
      }

      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || 'Publish failed');
      }

      const data = await res.json();
      setPublishedDetailUrl(data.detail_url);
      navigate(data.detail_url);
    } catch (error) {
      console.error(error);
      setValidationErrors([{ field: 'submit', code: 'PUBLISH_FAILED', message: 'Yayınlama başarısız' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <WizardContext.Provider value={{
      completedSteps,
      setCompletedSteps,
      step,
      setStep,
      draftId,
      category,
      basicInfo,
      setBasicInfo,
      attributes,
      setAttributes,
      schema,
      schemaLoading,
      schemaNotice,
      loadCategorySchema,
      coreFields,
      setCoreFields,
      dynamicValues,
      setDynamicValues,
      detailGroups,
      setDetailGroups,
      moduleData,
      setModuleData,
      media,
      setMedia,
      loading,
      editLoading,
      autosaveStatus,
      setAutosaveStatus,
      validationErrors,
      publishedDetailUrl,
      createDraft,
      saveDraft,
      trackWizardEvent,
      saveStep,
      publishListing,
      setDraftId,
    }}>
      {children}
    </WizardContext.Provider>
  );
};

export const useWizard = () => useContext(WizardContext);
