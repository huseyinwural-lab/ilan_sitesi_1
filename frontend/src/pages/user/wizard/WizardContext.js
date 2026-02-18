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

  // Keep wizard country in sync with selected country
  useEffect(() => {
    if (selectedCountry) {
      setBasicInfo((prev) => ({ ...prev, country: selectedCountry }));
    }
  }, [selectedCountry]);

  const [media, setMedia] = useState([]);

  // Actions
  const createDraft = async (selectedCategory) => {
    setLoading(true);
    setValidationErrors([]);
    try {
      setCategory(selectedCategory);

      const payload = {
        country: selectedCountry || 'DE',
        category_key: selectedCategory.id,
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

      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/listings/vehicle/${draftId}/submit`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        },
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
      attributes,
      media,
      loading,
      validationErrors,
      publishedDetailUrl,
      createDraft,
      saveStep,
      publishListing,
      setDraftId,
      setMedia
    }}>
      {children}
    </WizardContext.Provider>
  );
};

export const useWizard = () => useContext(WizardContext);
