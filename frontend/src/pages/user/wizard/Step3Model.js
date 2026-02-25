import React, { useEffect, useMemo, useRef, useState } from 'react';
import { toast } from '@/components/ui/use-toast';
import { useWizard } from './WizardContext';

const CACHE_TTL = 1000 * 60 * 60 * 6;
const POPULAR_LIMIT = 12;

const ModelStep = () => {
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

  const [models, setModels] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedModel, setSelectedModel] = useState(null);
  const [loadingModels, setLoadingModels] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!basicInfo.make_key) {
      setModels([]);
      setLoadingModels(false);
      return;
    }

    const cacheKey = `vehicle_models_cache_${basicInfo.country}_${basicInfo.make_key}`;
    const cached = localStorage.getItem(cacheKey);
    if (cached) {
      try {
        const payload = JSON.parse(cached);
        if (Date.now() - payload.ts < CACHE_TTL) {
          setModels(payload.items || []);
        }
      } catch (err) {
        console.warn('Models cache parse failed', err);
      }
    }

    const fetchModels = async () => {
      try {
        setLoadingModels(true);
        const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v2/vehicle/models?country=${basicInfo.country}&make_key=${basicInfo.make_key}`);
        const data = await res.json();
        const items = data.items || [];
        setModels(items);
        localStorage.setItem(cacheKey, JSON.stringify({ ts: Date.now(), items }));
      } catch (err) {
        console.error('Fetch models error', err);
      } finally {
        setLoadingModels(false);
      }
    };

    fetchModels();
  }, [basicInfo.country, basicInfo.make_key]);

  useEffect(() => {
    if (!basicInfo.model_key || models.length === 0) return;
    const found = models.find((model) => model.key === basicInfo.model_key);
    if (found) setSelectedModel(found);
  }, [basicInfo.model_key, models]);

  useEffect(() => {
    if (!basicInfo.model_key) {
      setSelectedModel(null);
    }
  }, [basicInfo.model_key]);

  useEffect(() => {
    setSelectedModel(null);
    setSearch('');
  }, [basicInfo.make_key]);

  const filteredModels = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return models;
    return models.filter((model) => (model.label || model.name || '').toLowerCase().includes(term));
  }, [models, search]);

  const popularModels = useMemo(() => {
    const popular = models.filter((model) => model.popular);
    if (popular.length > 0) return popular.slice(0, POPULAR_LIMIT);
    return models.slice(0, POPULAR_LIMIT);
  }, [models]);

  const handleSelect = (model) => {
    setSelectedModel(model);
    setError('');
  };

  const scrollToError = () => {
    setTimeout(() => {
      const el = document.querySelector('[data-testid="model-error"]');
      if (el) {
        el.scrollIntoView({ behavior: window.innerWidth < 768 ? 'smooth' : 'auto', block: 'center' });
      }
    }, 0);
  };

  const handleComplete = async () => {
    if (saving || saveLockRef.current) return { ok: false };
    saveLockRef.current = true;
    setSaving(true);
    try {
      if (!selectedModel) {
        setError('Lütfen model seçin.');
        scrollToError();
        return { ok: false };
      }

      const modelLabel = selectedModel.label || selectedModel.name || selectedModel.key;

      const result = await saveDraft({
        vehicle: {
          make_key: basicInfo.make_key,
          make_id: basicInfo.make_id,
          model_key: selectedModel.key,
          model_id: selectedModel.id,
          year: null,
          trim_key: null,
          vehicle_trim_id: null,
          vehicle_trim_label: null,
          manual_trim_flag: false,
          manual_trim_text: null,
          fuel_type: null,
          body: null,
          transmission: null,
          drive: null,
          engine_type: null,
        },
      });

      if (!result?.ok) {
        setError('Model kaydedilemedi.');
        scrollToError();
        return { ok: false };
      }

      setBasicInfo((prev) => ({
        ...prev,
        model_key: selectedModel.key,
        model_id: selectedModel.id,
        model_label: modelLabel,
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

      setCompletedSteps((prev) => ({
        ...prev,
        3: true,
        4: false,
        5: false,
        6: false,
      }));
      setError('');
      return { ok: true, updatedAt: result?.updatedAt || null };
    } finally {
      setSaving(false);
      saveLockRef.current = false;
    }
  };


  const handleNext = async () => {
    if (saving) return;
    if (!selectedModel) {
      setError('Lütfen model seçin.');
      scrollToError();
      await trackWizardEvent('wizard_step_autosave_error', {
        step_id: 'model',
        category_id: basicInfo.category_id,
        module: basicInfo.module || 'vehicle',
        country: basicInfo.country || (localStorage.getItem('selected_country') || 'DE'),
        reason: 'missing_model',
      });
      setAutosaveStatus((prev) => ({
        ...prev,
        status: 'error',
        lastErrorAt: new Date().toISOString(),
      }));
      return;
    }
    if (!completedSteps[3]) {
      const result = await handleComplete();
      if (!result?.ok) {
        await trackWizardEvent('wizard_step_autosave_error', {
          step_id: 'model',
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
      setAutosaveStatus((prev) => ({
        ...prev,
        status: 'success',
        lastSuccessAt: result?.updatedAt || new Date().toISOString(),
      }));
    }
    await trackWizardEvent('wizard_step_autosave_success', {
      step_id: 'model',
      category_id: basicInfo.category_id,
      module: basicInfo.module || 'vehicle',
      country: basicInfo.country || (localStorage.getItem('selected_country') || 'DE'),
    });
    if (completedSteps[3]) {
      setAutosaveStatus((prev) => ({
        ...prev,
        status: 'success',
        lastSuccessAt: prev.lastSuccessAt || new Date().toISOString(),
      }));
    }
    toast({
      title: 'Kaydedildi',
      duration: 2500,
      dismissible: false,
      'data-testid': 'wizard-autosave-toast',
    });
    setStep(4);
  };

  const nextDisabled = !selectedModel || loading || saving;

  if (!basicInfo.make_key) {
    return (
      <div className="bg-white border rounded-xl p-6 text-center" data-testid="wizard-model-locked">
        <h2 className="text-xl font-bold mb-2">Model seçimi kilitli</h2>
        <p className="text-sm text-muted-foreground">Önce bir marka seçmelisiniz.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="wizard-model-step">
      <div className="space-y-1">
        <h2 className="text-2xl font-bold" data-testid="wizard-model-title">Model Seçin</h2>
        <p className="text-sm text-muted-foreground" data-testid="wizard-model-subtitle">Marka seçiminize göre listelenir.</p>
      </div>

      <div className="bg-white rounded-xl border p-5 space-y-4" data-testid="wizard-model-search">
        <input
          type="text"
          className="w-full p-2 border rounded-md"
          placeholder="Model ara"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          data-testid="model-search-input"
        />

        {!search && (
          <div className="space-y-3" data-testid="model-popular-section">
            <div className="text-sm font-semibold text-gray-700">En Çok Aranan</div>
            {loadingModels ? (
              <div className="text-xs text-gray-500" data-testid="model-loading">Yükleniyor...</div>
            ) : popularModels.length === 0 ? (
              <div className="text-xs text-gray-500" data-testid="model-popular-empty">Model bulunamadı.</div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="model-popular-grid">
                {popularModels.map((model) => {
                  const label = model.label || model.name || model.key;
                  const isActive = selectedModel?.key === model.key;
                  return (
                    <button
                      key={model.key}
                      type="button"
                      onClick={() => handleSelect(model)}
                      className={`border rounded-lg p-3 text-left transition ${isActive ? 'border-blue-600 bg-blue-50' : 'border-gray-200 hover:border-blue-400'}`}
                      data-testid={`model-card-${model.key}`}
                    >
                      <div className="text-sm font-semibold">{label}</div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {search && (
          <div className="space-y-3" data-testid="model-search-results">
            <div className="text-sm font-semibold text-gray-700">Arama Sonuçları</div>
            {loadingModels ? (
              <div className="text-xs text-gray-500" data-testid="model-search-loading">Yükleniyor...</div>
            ) : filteredModels.length === 0 ? (
              <div className="text-xs text-gray-500" data-testid="model-search-empty">Sonuç bulunamadı.</div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="model-search-grid">
                {filteredModels.map((model) => {
                  const label = model.label || model.name || model.key;
                  const isActive = selectedModel?.key === model.key;
                  return (
                    <button
                      key={model.key}
                      type="button"
                      onClick={() => handleSelect(model)}
                      className={`border rounded-lg p-3 text-left transition ${isActive ? 'border-blue-600 bg-blue-50' : 'border-gray-200 hover:border-blue-400'}`}
                      data-testid={`model-search-card-${model.key}`}
                    >
                      <div className="text-sm font-semibold">{label}</div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="text-sm text-red-600" data-testid="model-error">{error}</div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setStep(2)}
          className="px-4 py-2 text-sm text-gray-500"
          data-testid="model-back"
        >
          Geri
        </button>
        <div className="flex items-center gap-3">
          <div title={nextDisabled ? 'Önce bu adımı tamamlayın.' : ''} data-testid="model-next-tooltip">
            <button
              type="button"
              onClick={handleNext}
              disabled={nextDisabled}
              className="px-4 py-2 border rounded-md text-sm disabled:opacity-50"
              data-testid="model-next"
            >
              Next
            </button>
          </div>
          <button
            type="button"
            onClick={handleComplete}
            disabled={loading || saving}
            className="px-5 py-2 bg-blue-600 text-white rounded-md disabled:opacity-60"
            data-testid="model-complete"
          >
            Tamam
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModelStep;
