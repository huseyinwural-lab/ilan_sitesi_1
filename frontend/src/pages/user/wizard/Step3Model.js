import React, { useEffect, useMemo, useState } from 'react';
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
  } = useWizard();

  const [models, setModels] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedModel, setSelectedModel] = useState(null);
  const [loadingModels, setLoadingModels] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!basicInfo.make_key) {
      setModels([]);
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
        const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v2/vehicle/models?country=${basicInfo.country}&make_key=${basicInfo.make_key}`);
        const data = await res.json();
        const items = data.items || [];
        setModels(items);
        localStorage.setItem(cacheKey, JSON.stringify({ ts: Date.now(), items }));
      } catch (err) {
        console.error('Fetch models error', err);
      }
    };

    fetchModels();
  }, [basicInfo.country, basicInfo.make_key]);

  useEffect(() => {
    if (!basicInfo.model_key || models.length === 0) return;
    const found = models.find((model) => model.key === basicInfo.model_key);
    if (found) setSelectedModel(found);
  }, [basicInfo.model_key, models]);

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

  const handleComplete = async () => {
    if (!selectedModel) {
      setError('Lütfen model seçin.');
      return;
    }

    const ok = await saveDraft({
      vehicle: {
        make_key: basicInfo.make_key,
        make_id: basicInfo.make_id,
        model_key: selectedModel.key,
        model_id: selectedModel.id,
      },
    });

    if (!ok) {
      setError('Model kaydedilemedi.');
      return;
    }

    setBasicInfo((prev) => ({
      ...prev,
      model_key: selectedModel.key,
      model_id: selectedModel.id,
      year: null,
      trim_key: null,
    }));

    setCompletedSteps((prev) => ({
      ...prev,
      3: true,
      4: false,
      5: false,
      6: false,
    }));
    setError('');
  };

  const nextDisabled = !completedSteps[3];

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
          </div>
        )}

        {search && (
          <div className="space-y-3" data-testid="model-search-results">
            <div className="text-sm font-semibold text-gray-700">Arama Sonuçları</div>
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
              onClick={() => setStep(4)}
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
            disabled={loading}
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
