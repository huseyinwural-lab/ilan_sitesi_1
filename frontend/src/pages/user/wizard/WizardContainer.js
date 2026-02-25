import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { WizardProvider, useWizard } from './WizardContext';
import Step1Category from './Step1Category';
import Step2Brand from './Step2Brand';
import Step3Model from './Step3Model';
import Step4YearTrim from './Step4YearTrim';
import Step5CoreFields from './Step5CoreFields';
import Step6FeaturesMedia from './Step6FeaturesMedia';
import Step7Review from './Step4Review';
import ErrorBoundary from '@/components/ErrorBoundary';

const WizardContent = () => {
  const { step, loading, editLoading, autosaveStatus, trackWizardEvent } = useWizard();
  const badgeEventRef = useRef("");

  const moduleKey = useMemo(() => localStorage.getItem('ilan_ver_module') || 'vehicle', []);
  const isVehicleModule = moduleKey === 'vehicle';

  const steps = useMemo(() => {
    if (isVehicleModule) {
      return [
        { step: 1, label: 'Kategori/Segment', display: 1 },
        { step: 2, label: 'Marka', display: 2 },
        { step: 3, label: 'Model', display: 3 },
        { step: 4, label: 'Yıl/Versiyon', display: 4 },
        { step: 5, label: 'Çekirdek Alanlar', display: 5 },
        { step: 6, label: 'Özellikler + Medya', display: 6 },
        { step: 7, label: 'Önizleme', display: 7 },
      ];
    }
    return [
      { step: 1, label: 'Kategori/Segment', display: 1 },
      { step: 5, label: 'Çekirdek Alanlar', display: 2 },
      { step: 6, label: 'Özellikler + Medya', display: 3 },
      { step: 7, label: 'Önizleme', display: 4 },
    ];
  }, [isVehicleModule]);

  const stepIdMap = useMemo(
    () => ({
      1: 'category',
      2: 'brand',
      3: 'model',
      4: 'year',
      5: 'core',
      6: 'features',
      7: 'review',
    }),
    []
  );

  const showAutosaveBadge = step !== 7 && autosaveStatus?.status && autosaveStatus.status !== 'idle';

  const autosaveBadgeLabel = useMemo(() => {
    if (!showAutosaveBadge) return '';
    if (autosaveStatus.status === 'error') return 'Kaydedilemedi';
    const time = autosaveStatus.lastSuccessAt ? new Date(autosaveStatus.lastSuccessAt) : null;
    if (!time || Number.isNaN(time.getTime())) return 'Kaydedildi';
    return `Kaydedildi • ${time.toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })}`;
  }, [autosaveStatus, showAutosaveBadge]);

  useEffect(() => {
    if (!showAutosaveBadge) return;
    const badgeKey = `${autosaveStatus.status}-${autosaveStatus.lastSuccessAt}-${autosaveStatus.lastErrorAt}-${step}`;
    if (badgeEventRef.current === badgeKey) return;
    badgeEventRef.current = badgeKey;
    trackWizardEvent('wizard_autosave_badge_rendered', {
      step_id: stepIdMap[step] || `step_${step}`,
      status: autosaveStatus.status,
      timestamp: autosaveStatus.lastSuccessAt || autosaveStatus.lastErrorAt,
    });
  }, [autosaveStatus, showAutosaveBadge, step, stepIdMap, trackWizardEvent]);

  const prevStepRef = useRef(step);

  useEffect(() => {
    if (prevStepRef.current === step) return;
    if (step !== 7) {
      const isMobile = window.innerWidth < 768;
      window.scrollTo({ top: 0, behavior: isMobile ? 'smooth' : 'auto' });
    }
    prevStepRef.current = step;
  }, [step]);

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="bg-white rounded-xl shadow-sm border p-6 mb-6" data-testid="wizard-progress">
        <div className="flex items-center justify-between">
          {steps.map((s, index) => (
            <div key={s.step} className="flex items-center" data-testid={`wizard-step-${s.step}`}>
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                  step >= s.step ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                }`}
              >
                {s.display}
              </div>
              <span className={`ml-2 text-sm ${step >= s.step ? 'text-gray-900' : 'text-gray-500'}`}>
                {s.label}
              </span>
              {index < steps.length - 1 && (
                <div className={`w-12 h-0.5 mx-4 ${step > s.step ? 'bg-blue-600' : 'bg-gray-200'}`} />
              )}
            </div>
          ))}
        </div>
        {showAutosaveBadge && (
          <div className="mt-3 flex justify-end">
            <span
              className={`text-xs font-semibold rounded-full px-3 py-1 ${
                autosaveStatus.status === 'error'
                  ? 'bg-rose-100 text-rose-700'
                  : 'bg-emerald-100 text-emerald-700'
              }`}
              data-testid="wizard-autosave-badge"
            >
              {autosaveBadgeLabel}
            </span>
          </div>
        )}
      </div>

      {(loading || editLoading) && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6" data-testid="wizard-loading">
          İşlem yapılıyor, lütfen bekleyin...
        </div>
      )}

      {step === 1 && <Step1Category />}
      {isVehicleModule && step === 2 && <Step2Brand />}
      {isVehicleModule && step === 3 && <Step3Model />}
      {isVehicleModule && step === 4 && <Step4YearTrim />}
      {step === 5 && <Step5CoreFields />}
      {step === 6 && <Step6FeaturesMedia />}
      {step === 7 && <Step7Review />}
    </div>
  );
};

const WizardContainer = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const editListingId = searchParams.get('edit');
  const [preselectStatus, setPreselectStatus] = useState('checking');

  const trackEvent = useCallback(async (eventName, metadata = {}) => {
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

  useEffect(() => {
    const validatePreselect = async () => {
      if (editListingId) {
        setPreselectStatus('ok');
        return;
      }
      const storedCategory = localStorage.getItem('ilan_ver_category');
      const moduleKey = localStorage.getItem('ilan_ver_module');
      const country = (localStorage.getItem('selected_country') || 'DE').toUpperCase();
      if (!storedCategory || !moduleKey) {
        await trackEvent('wizard_preselect_invalid', { reason: 'missing', country });
        navigate('/ilan-ver/kategori-secimi', { replace: true });
        setPreselectStatus('redirect');
        return;
      }
      let parsed = null;
      try {
        parsed = JSON.parse(storedCategory);
      } catch (err) {
        parsed = null;
      }
      if (!parsed?.id) {
        await trackEvent('wizard_preselect_invalid', { reason: 'invalid_payload', country, module: moduleKey });
        localStorage.removeItem('ilan_ver_category');
        localStorage.removeItem('ilan_ver_category_path');
        localStorage.removeItem('ilan_ver_module');
        localStorage.removeItem('ilan_ver_module_label');
        navigate('/ilan-ver/kategori-secimi', { replace: true });
        setPreselectStatus('redirect');
        return;
      }
      try {
        const params = new URLSearchParams({ category_id: parsed.id, country, module: moduleKey });
        const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/categories/validate?${params.toString()}`);
        if (!res.ok) {
          await trackEvent('wizard_preselect_invalid', { reason: 'validation_failed', country, module: moduleKey, category_id: parsed.id });
          localStorage.removeItem('ilan_ver_category');
          localStorage.removeItem('ilan_ver_category_path');
          localStorage.removeItem('ilan_ver_module');
          localStorage.removeItem('ilan_ver_module_label');
          navigate('/ilan-ver/kategori-secimi', { replace: true });
          setPreselectStatus('redirect');
          return;
        }
        await trackEvent('wizard_preselect_valid', { country, module: moduleKey, category_id: parsed.id });
        setPreselectStatus('ok');
      } catch (err) {
        await trackEvent('wizard_preselect_invalid', { reason: 'error', country, module: moduleKey, category_id: parsed?.id });
        navigate('/ilan-ver/kategori-secimi', { replace: true });
        setPreselectStatus('redirect');
      }
    };

    validatePreselect();
  }, [editListingId, navigate, trackEvent]);

  if (preselectStatus === 'checking') {
    return (
      <div className="max-w-4xl mx-auto py-12 px-4 text-sm text-slate-500" data-testid="wizard-preselect-loading">
        Kategori doğrulanıyor...
      </div>
    );
  }

  return (
    <WizardProvider editListingId={editListingId}>
      <WizardContent />
    </WizardProvider>
  );
};

export default WizardContainer;
