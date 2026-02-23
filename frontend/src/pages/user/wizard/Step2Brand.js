import React, { useEffect, useMemo, useState } from 'react';
import { toast } from '@/components/ui/use-toast';
import { useWizard } from './WizardContext';

const CACHE_TTL = 1000 * 60 * 60 * 12;
const POPULAR_LIMIT = 12;

const BrandStep = () => {
  const {
    basicInfo,
    setBasicInfo,
    saveDraft,
    setStep,
    completedSteps,
    setCompletedSteps,
    loading,
    trackWizardEvent,
  } = useWizard();

  const [saving, setSaving] = useState(false);

  const [makes, setMakes] = useState([]);
  const [search, setSearch] = useState('');
  const [selectedMake, setSelectedMake] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const cached = localStorage.getItem(`vehicle_makes_cache_${basicInfo.country}`);
    if (cached) {
      try {
        const payload = JSON.parse(cached);
        if (Date.now() - payload.ts < CACHE_TTL) {
          setMakes(payload.items || []);
        }
      } catch (err) {
        console.warn('Makes cache parse failed', err);
      }
    }

    const fetchMakes = async () => {
      try {
        const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v2/vehicle/makes?country=${basicInfo.country}`);
        const data = await res.json();
        const items = data.items || [];
        setMakes(items);
        localStorage.setItem(`vehicle_makes_cache_${basicInfo.country}`, JSON.stringify({ ts: Date.now(), items }));
      } catch (err) {
        console.error('Fetch makes error', err);
      }
    };

    fetchMakes();
  }, [basicInfo.country]);

  useEffect(() => {
    if (!basicInfo.make_key || makes.length === 0) return;
    const found = makes.find((make) => make.key === basicInfo.make_key);
    if (found) setSelectedMake(found);
  }, [basicInfo.make_key, makes]);

  const filteredMakes = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!term) return makes;
    return makes.filter((make) => (make.label || make.name || '').toLowerCase().includes(term));
  }, [makes, search]);

  const popularMakes = useMemo(() => {
    const popular = makes.filter((make) => make.popular);
    if (popular.length > 0) return popular.slice(0, POPULAR_LIMIT);
    return makes.slice(0, POPULAR_LIMIT);
  }, [makes]);

  const handleSelect = (make) => {
    setSelectedMake(make);
    setError('');
  };

  const scrollToError = () => {
    const el = document.querySelector('[data-testid="brand-error"]');
    if (el) {
      el.scrollIntoView({ behavior: window.innerWidth < 768 ? 'smooth' : 'auto', block: 'center' });
    }
  };

  const handleComplete = async () => {
    if (saving) return false;
    setSaving(true);
    if (!selectedMake) {
      setError('Lütfen marka seçin.');
      scrollToError();
      setSaving(false);
      return false;
    }

    const makeLabel = selectedMake.label || selectedMake.name || selectedMake.key;

    const ok = await saveDraft({
      vehicle: {
        make_key: selectedMake.key,
        make_id: selectedMake.id,
      },
    });

    if (!ok) {
      setError('Marka kaydedilemedi.');
      return false;
    }

    setBasicInfo((prev) => ({
      ...prev,
      make_key: selectedMake.key,
      make_id: selectedMake.id,
      make_label: makeLabel,
      model_key: null,
      model_id: null,
      model_label: null,
      year: null,
      trim_key: null,
    }));

    setCompletedSteps((prev) => ({
      ...prev,
      2: true,
      3: false,
      4: false,
      5: false,
      6: false,
    }));
    setError('');
    return true;
  };

  const handleNext = async () => {
    if (!selectedMake) {
      setError('Lütfen marka seçin.');
      return;
    }
    if (!completedSteps[2]) {
      const ok = await handleComplete();
      if (!ok) return;
    }
    setStep(3);
  };

  const nextDisabled = !selectedMake || loading;

  return (
    <div className="space-y-6" data-testid="wizard-brand-step">
      <div className="space-y-1">
        <h2 className="text-2xl font-bold" data-testid="wizard-brand-title">Marka Seçin</h2>
        <p className="text-sm text-muted-foreground" data-testid="wizard-brand-subtitle">Popüler markalardan seçin veya arayın.</p>
      </div>

      <div className="bg-white rounded-xl border p-5 space-y-4" data-testid="wizard-brand-search">
        <input
          type="text"
          className="w-full p-2 border rounded-md"
          placeholder="Marka ara"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          data-testid="brand-search-input"
        />

        {!search && (
          <div className="space-y-3" data-testid="brand-popular-section">
            <div className="text-sm font-semibold text-gray-700">Popüler Markalar</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="brand-popular-grid">
              {popularMakes.map((make) => {
                const label = make.label || make.name || make.key;
                const isActive = selectedMake?.key === make.key;
                return (
                  <button
                    key={make.key}
                    type="button"
                    onClick={() => handleSelect(make)}
                    className={`border rounded-lg p-3 flex items-center gap-3 transition ${isActive ? 'border-blue-600 bg-blue-50' : 'border-gray-200 hover:border-blue-400'}`}
                    data-testid={`brand-card-${make.key}`}
                  >
                    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-sm font-bold">
                      {label ? label[0] : '?'}
                    </div>
                    <span className="font-medium text-sm">{label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {search && (
          <div className="space-y-3" data-testid="brand-search-results">
            <div className="text-sm font-semibold text-gray-700">Arama Sonuçları</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3" data-testid="brand-search-grid">
              {filteredMakes.map((make) => {
                const label = make.label || make.name || make.key;
                const isActive = selectedMake?.key === make.key;
                return (
                  <button
                    key={make.key}
                    type="button"
                    onClick={() => handleSelect(make)}
                    className={`border rounded-lg p-3 flex items-center gap-3 transition ${isActive ? 'border-blue-600 bg-blue-50' : 'border-gray-200 hover:border-blue-400'}`}
                    data-testid={`brand-search-card-${make.key}`}
                  >
                    <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center text-sm font-bold">
                      {label ? label[0] : '?'}
                    </div>
                    <span className="font-medium text-sm">{label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {error && (
          <div className="text-sm text-red-600" data-testid="brand-error">{error}</div>
        )}
      </div>

      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setStep(1)}
          className="px-4 py-2 text-sm text-gray-500"
          data-testid="brand-back"
        >
          Geri
        </button>
        <div className="flex items-center gap-3">
          <div title={nextDisabled ? 'Önce bu adımı tamamlayın.' : ''} data-testid="brand-next-tooltip">
            <button
              type="button"
              onClick={handleNext}
              disabled={nextDisabled}
              className="px-4 py-2 border rounded-md text-sm disabled:opacity-50"
              data-testid="brand-next"
            >
              Next
            </button>
          </div>
          <button
            type="button"
            onClick={handleComplete}
            disabled={loading}
            className="px-5 py-2 bg-blue-600 text-white rounded-md disabled:opacity-60"
            data-testid="brand-complete"
          >
            Tamam
          </button>
        </div>
      </div>
    </div>
  );
};

export default BrandStep;
