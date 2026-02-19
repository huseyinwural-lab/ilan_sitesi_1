import React, { createContext, useContext, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCountry } from '@/contexts/CountryContext';

const WizardContext = createContext();

export const WizardProvider = ({ children }) => {
  const navigate = useNavigate();
  const { selectedCountry } = useCountry();
  const [draftId, setDraftId] = useState(null);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  
  // Data
  const [category, setCategory] = useState(null);
  const [validationErrors, setValidationErrors] = useState([]);
  const [publishedDetailUrl, setPublishedDetailUrl] = useState(null);
  const [basicInfo, setBasicInfo] = useState({
    country: 'DE',
    category_key: null, // segment
    category_id: null,
    make_key: null,
    model_key: null,
    year: null,
    mileage_km: null,
    price_eur: null,
    fuel_type: null,
    transmission: null,
    condition: null,
  });
  const [attributes, setAttributes] = useState({});
  const [schema, setSchema] = useState(null);
  const [schemaLoading, setSchemaLoading] = useState(false);
  const [coreFields, setCoreFields] = useState({
    title: '',
    description: '',
    price_amount: '',
    price_display: '',
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

  // Keep wizard country in sync with selected country
  useEffect(() => {
    if (selectedCountry) {
      setBasicInfo((prev) => ({ ...prev, country: selectedCountry }));
    }
  }, [selectedCountry]);

  const [media, setMedia] = useState([]);

  const loadCategorySchema = async (categoryId) => {
    if (!categoryId) return null;
    try {
      setSchemaLoading(true);
      const res = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/catalog/schema?category_id=${categoryId}&country=${selectedCountry || 'DE'}`
      );
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data?.detail || 'Schema yüklenemedi');
      }
      setSchema(data.schema);
      const priceConfig = data.schema?.core_fields?.price || {};
      setCoreFields((prev) => ({
        ...prev,
        currency_primary: priceConfig.currency_primary || 'EUR',
        currency_secondary: priceConfig.currency_secondary || 'CHF',
        secondary_enabled: priceConfig.secondary_enabled || false,
        decimal_places: priceConfig.decimal_places ?? 0,
      }));
      return data.schema;
    } catch (error) {
      console.error(error);
      return null;
    } finally {
      setSchemaLoading(false);
    }
  };

  // Actions
  const createDraft = async (selectedCategory) => {
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

      // Create empty draft first; details set in step 2
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/listings/vehicle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const t = await res.text();
        throw new Error(t || 'Draft create failed');
      }

      const data = await res.json();
      setDraftId(data.id);
      // expose for media step (minimal wiring)
      window.__WIZARD_DRAFT_ID__ = data.id;

      setBasicInfo((prev) => ({
        ...prev,
        country: selectedCountry || 'DE',
        category_key: selectedCategory.id,
        category_id: selectedCategory.id,
      }));
      setStep(2);
    } catch (error) {
      console.error(error);
      setValidationErrors([{ field: 'draft', code: 'DRAFT_CREATE_FAILED', message: 'Draft oluşturulamadı' }]);
    } finally {
      setLoading(false);
    }
  };

  const saveStep = async (data) => {
    setLoading(true);
    setValidationErrors([]);
    try {
      if (step === 2) {
        setBasicInfo((prev) => ({ ...prev, ...data.basic }));
        if (data.basic?.attributes) setAttributes(data.basic.attributes);
        if (data.coreFields) setCoreFields(data.coreFields);
        if (data.dynamicValues) setDynamicValues(data.dynamicValues);
        if (data.detailGroups) setDetailGroups(data.detailGroups);
        if (data.moduleData) setModuleData(data.moduleData);
      } else if (step === 3) {
        setMedia(data);
      }

      // ensure draft exists before leaving step 2
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
            amount: coreFields.price_amount ? Number(coreFields.price_amount) : null,
            currency_primary: coreFields.currency_primary,
            currency_secondary: coreFields.secondary_enabled ? coreFields.currency_secondary : null,
            secondary_amount: coreFields.secondary_amount ? Number(coreFields.secondary_amount) : null,
            decimal_places: coreFields.decimal_places,
          },
        },
        vehicle: {
          make_key: basicInfo.make_key,
          model_key: basicInfo.model_key,
          year: basicInfo.year,
          trim_key: basicInfo.trim_key,
        },
        attributes: {
          ...attributes,
          mileage_km: basicInfo.mileage_km,
          fuel_type: basicInfo.fuel_type,
          transmission: basicInfo.transmission,
          condition: basicInfo.condition,
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
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
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
      step, setStep,
      draftId,
      category,
      basicInfo,
      setBasicInfo,
      attributes,
      setAttributes,
      schema,
      schemaLoading,
      loadCategorySchema,
      coreFields,
      dynamicValues,
      detailGroups,
      moduleData,
      media,
      loading,
      validationErrors,
      publishedDetailUrl,
      createDraft,
      saveStep,
      publishListing,
      setDraftId,
      setMedia,
      setCoreFields,
      setDynamicValues,
      setDetailGroups,
      setModuleData
    }}>
      {children}
    </WizardContext.Provider>
  );
};

export const useWizard = () => useContext(WizardContext);
