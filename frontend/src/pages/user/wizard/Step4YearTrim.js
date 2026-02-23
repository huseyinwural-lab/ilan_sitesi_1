import React, { useEffect, useMemo, useRef, useState } from 'react';
import { toast } from '@/components/ui/use-toast';
import { useWizard } from './WizardContext';

const YearTrimStep = () => {
  const {
    basicInfo,
    setBasicInfo,
    saveDraft,
    setStep,
    completedSteps,
    setCompletedSteps,
    loading,
    trackWizardEvent,
    setAutosaveStatus,
  } = useWizard();

  const [saving, setSaving] = useState(false);
  const saveLockRef = useRef(false);

  const [year, setYear] = useState(basicInfo.year || '');
  const [trimKey, setTrimKey] = useState(basicInfo.trim_key || '');
  const [error, setError] = useState('');

  useEffect(() => {
    setYear(basicInfo.year ? String(basicInfo.year) : '');
    setTrimKey(basicInfo.trim_key || '');
  }, [basicInfo.year, basicInfo.trim_key]);

  const yearOptions = useMemo(() => {
    const start = 2026;
    const end = 2010;
    const years = [];
    for (let y = start; y >= end; y -= 1) {
      years.push(y);
    }
    return years;
  }, []);

  const scrollToError = () => {
    setTimeout(() => {
      const el = document.querySelector('[data-testid="year-error"]');
      if (el) {
        el.scrollIntoView({ behavior: window.innerWidth < 768 ? 'smooth' : 'auto', block: 'center' });
      }
    }, 0);
  };

  const handleComplete = async () => {
    if (saving || saveLockRef.current) return false;
    saveLockRef.current = true;
    setSaving(true);
    try {
      if (!year) {
        setError('Yıl seçiniz.');
        scrollToError();
        return false;
      }

      const trimmedTrim = trimKey.trim();
      const ok = await saveDraft({
        vehicle: {
          make_key: basicInfo.make_key,
          make_id: basicInfo.make_id,
          model_key: basicInfo.model_key,
          model_id: basicInfo.model_id,
          year: Number(year),
          trim_key: trimmedTrim || null,
        },
      });

      if (!ok) {
        setError('Yıl kaydedilemedi.');
        scrollToError();
        return false;
      }

      setBasicInfo((prev) => ({
        ...prev,
        year: Number(year),
        trim_key: trimmedTrim || null,
      }));

      setCompletedSteps((prev) => ({
        ...prev,
        4: true,
        5: false,
        6: false,
      }));
      setError('');
      return true;
    } finally {
      setSaving(false);
      saveLockRef.current = false;
    }
  };

  const handleNext = async () => {
    if (saving) return;
    if (!year) {
      setError('Yıl seçiniz.');
      scrollToError();
      await trackWizardEvent('wizard_step_autosave_error', {
        step_id: 'year',
        category_id: basicInfo.category_id,
        module: basicInfo.module || 'vehicle',
        country: basicInfo.country || (localStorage.getItem('selected_country') || 'DE'),
        reason: 'missing_year',
      });
      setAutosaveStatus((prev) => ({
        ...prev,
        status: 'error',
        lastErrorAt: new Date().toISOString(),
      }));
      return;
    }
    if (!completedSteps[4]) {
      const ok = await handleComplete();
      if (!ok) {
        await trackWizardEvent('wizard_step_autosave_error', {
          step_id: 'year',
          category_id: basicInfo.category_id,
          module: basicInfo.module || 'vehicle',
          country: basicInfo.country || (localStorage.getItem('selected_country') || 'DE'),
          reason: 'save_failed',
        });
        setAutosaveStatus((prev) => ({
          ...prev,
          status: 'error',
          lastErrorAt: new Date().toISOString(),
        }));
        return;
      }
    }
    await trackWizardEvent('wizard_step_autosave_success', {
      step_id: 'year',
      category_id: basicInfo.category_id,
      module: basicInfo.module || 'vehicle',
      country: basicInfo.country || (localStorage.getItem('selected_country') || 'DE'),
    });
    setAutosaveStatus((prev) => ({
      ...prev,
      status: 'success',
      lastSuccessAt: new Date().toISOString(),
    }));
    toast({
      title: 'Kaydedildi',
      duration: 2500,
      dismissible: false,
      'data-testid': 'wizard-autosave-toast',
    });
    setStep(5);
  };

  const nextDisabled = !year || loading || saving;

  if (!basicInfo.model_key) {
    return (
      <div className="bg-white border rounded-xl p-6 text-center" data-testid="wizard-year-locked">
        <h2 className="text-xl font-bold mb-2">Yıl seçimi kilitli</h2>
        <p className="text-sm text-muted-foreground">Önce bir model seçmelisiniz.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="wizard-year-step">
      <div className="space-y-1">
        <h2 className="text-2xl font-bold" data-testid="wizard-year-title">Yıl ve Versiyon</h2>
        <p className="text-sm text-muted-foreground" data-testid="wizard-year-subtitle">
          Yıl seçimi zorunlu, versiyon/donanım alanı isteğe bağlıdır.
        </p>
      </div>

      <div className="bg-white rounded-xl border p-5 space-y-4" data-testid="wizard-year-form">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Yıl *</label>
          <select
            className="w-full p-2 border rounded-md"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            data-testid="year-select"
          >
            <option value="">Seçiniz</option>
            {yearOptions.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Versiyon / Donanım (Opsiyonel)</label>
          <input
            className="w-full p-2 border rounded-md"
            value={trimKey}
            onChange={(e) => setTrimKey(e.target.value)}
            placeholder="Örn: Comfortline, Premium"
            data-testid="trim-input"
          />
          <p className="text-xs text-gray-500 mt-1" data-testid="trim-help">
            Bu alan opsiyoneldir. Girmediğinizde boş bırakabilirsiniz.
          </p>
        </div>

        {error && (
          <div className="text-sm text-red-600" data-testid="year-error">{error}</div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setStep(3)}
          className="px-4 py-2 text-sm text-gray-500"
          data-testid="year-back"
        >
          Geri
        </button>
        <div className="flex items-center gap-3">
          <div title={nextDisabled ? 'Önce bu adımı tamamlayın.' : ''} data-testid="year-next-tooltip">
            <button
              type="button"
              onClick={handleNext}
              disabled={nextDisabled}
              className="px-4 py-2 border rounded-md text-sm disabled:opacity-50"
              data-testid="year-next"
            >
              Next
            </button>
          </div>
          <button
            type="button"
            onClick={handleComplete}
            disabled={loading || saving}
            className="px-5 py-2 bg-blue-600 text-white rounded-md disabled:opacity-60"
            data-testid="year-complete"
          >
            Tamam
          </button>
        </div>
      </div>
    </div>
  );
};

export default YearTrimStep;
