import React, { useMemo, useState } from 'react';
import { useWizard } from './WizardContext';

const YearTrimStep = () => {
  const {
    basicInfo,
    setBasicInfo,
    schema,
    saveDraft,
    setStep,
    completedSteps,
    setCompletedSteps,
    loading,
  } = useWizard();

  const [year, setYear] = useState(basicInfo.year || '');
  const [trimKey, setTrimKey] = useState(basicInfo.trim_key || '');
  const [error, setError] = useState('');

  const yearOptions = useMemo(() => {
    const start = 2026;
    const years = [];
    for (let y = start; y >= 1980; y -= 1) {
      years.push(y);
    }
    return years;
  }, []);

  const trimOptions = schema?.vehicle_trims || [];

  const handleComplete = async () => {
    if (!year) {
      setError('Yıl seçiniz.');
      return;
    }

    const ok = await saveDraft({
      vehicle: {
        make_key: basicInfo.make_key,
        make_id: basicInfo.make_id,
        model_key: basicInfo.model_key,
        model_id: basicInfo.model_id,
        year: Number(year),
        trim_key: trimKey || null,
      },
    });

    if (!ok) {
      setError('Yıl kaydedilemedi.');
      return;
    }

    setBasicInfo((prev) => ({
      ...prev,
      year: Number(year),
      trim_key: trimKey || null,
    }));

    setCompletedSteps((prev) => ({
      ...prev,
      4: true,
      5: false,
      6: false,
    }));
    setError('');
  };

  const nextDisabled = !completedSteps[4];

  return (
    <div className="space-y-6" data-testid="wizard-year-step">
      <div className="space-y-1">
        <h2 className="text-2xl font-bold" data-testid="wizard-year-title">Yıl ve Versiyon</h2>
        <p className="text-sm text-muted-foreground" data-testid="wizard-year-subtitle">Yıl seçimi zorunlu, trim varsa opsiyoneldir.</p>
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

        {trimOptions.length > 0 && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Versiyon (Opsiyonel)</label>
            <select
              className="w-full p-2 border rounded-md"
              value={trimKey}
              onChange={(e) => setTrimKey(e.target.value)}
              data-testid="trim-select"
            >
              <option value="">Seçiniz</option>
              {trimOptions.map((trim) => (
                <option key={trim.key || trim.id} value={trim.key || trim.id}>{trim.label || trim.name}</option>
              ))}
            </select>
          </div>
        )}

        {trimOptions.length === 0 && (
          <div className="text-sm text-gray-500" data-testid="trim-disabled-note">
            Trim bilgisi bulunmuyor, bu adım kapalı.
          </div>
        )}

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
              onClick={() => setStep(5)}
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
            disabled={loading}
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
