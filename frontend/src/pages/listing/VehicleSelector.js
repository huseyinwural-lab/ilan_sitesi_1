import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const EMPTY_OPTIONS = {
  fuel_types: [],
  bodies: [],
  transmissions: [],
  drives: [],
  engine_types: [],
};

const getCountry = () => (localStorage.getItem('selected_country') || 'DE').toUpperCase();

export default function VehicleSelector() {
  const navigate = useNavigate();
  const [years, setYears] = useState([]);
  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);
  const [options, setOptions] = useState(EMPTY_OPTIONS);
  const [trims, setTrims] = useState([]);

  const [selectedYear, setSelectedYear] = useState('');
  const [selectedMake, setSelectedMake] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [selectedFuel, setSelectedFuel] = useState('');
  const [selectedBody, setSelectedBody] = useState('');
  const [selectedTransmission, setSelectedTransmission] = useState('');
  const [selectedDrive, setSelectedDrive] = useState('');
  const [selectedEngineType, setSelectedEngineType] = useState('');
  const [selectedTrim, setSelectedTrim] = useState(null);

  const [manualTrimEnabled, setManualTrimEnabled] = useState(false);
  const [manualTrimValue, setManualTrimValue] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const numericYear = useMemo(() => Number(selectedYear), [selectedYear]);
  const manualTrimAllowed = Number.isFinite(numericYear) && numericYear > 0 && numericYear < 2000;

  const fetchYears = async () => {
    try {
      const res = await fetch(`${API}/vehicle/years?country=${getCountry()}`);
      const data = await res.json();
      setYears(data?.items || []);
    } catch (err) {
      setYears([]);
    }
  };

  const fetchMakes = async (year) => {
    if (!year) return;
    try {
      const res = await fetch(`${API}/vehicle/makes?year=${year}&country=${getCountry()}`);
      const data = await res.json();
      setMakes(data?.items || []);
    } catch (err) {
      setMakes([]);
    }
  };

  const fetchModels = async (year, make) => {
    if (!year || !make) return;
    try {
      const res = await fetch(`${API}/vehicle/models?year=${year}&make=${make}&country=${getCountry()}`);
      const data = await res.json();
      setModels(data?.items || []);
    } catch (err) {
      setModels([]);
    }
  };

  const fetchOptions = async (year, make, model) => {
    if (!year || !make || !model) return;
    try {
      const res = await fetch(
        `${API}/vehicle/options?year=${year}&make=${make}&model=${model}&country=${getCountry()}`,
      );
      const data = await res.json();
      setOptions(data?.options || EMPTY_OPTIONS);
    } catch (err) {
      setOptions(EMPTY_OPTIONS);
    }
  };

  const fetchTrims = async () => {
    if (!selectedYear || !selectedMake || !selectedModel) return;
    try {
      setLoading(true);
      const params = new URLSearchParams({
        year: selectedYear,
        make: selectedMake,
        model: selectedModel,
      });
      if (selectedFuel) params.set('fuel_type', selectedFuel);
      if (selectedBody) params.set('body', selectedBody);
      if (selectedTransmission) params.set('transmission', selectedTransmission);
      if (selectedDrive) params.set('drive', selectedDrive);
      if (selectedEngineType) params.set('engine_type', selectedEngineType);
      params.set('country', getCountry());
      const res = await fetch(`${API}/vehicle/trims?${params.toString()}`);
      const data = await res.json();
      setTrims(data?.items || []);
    } catch (err) {
      setTrims([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchYears();
  }, []);

  useEffect(() => {
    if (!selectedYear) return;
    setSelectedMake('');
    setSelectedModel('');
    setSelectedFuel('');
    setSelectedBody('');
    setSelectedTransmission('');
    setSelectedDrive('');
    setSelectedEngineType('');
    setSelectedTrim(null);
    setManualTrimEnabled(false);
    setManualTrimValue('');
    setOptions(EMPTY_OPTIONS);
    setModels([]);
    fetchMakes(selectedYear);
  }, [selectedYear]);

  useEffect(() => {
    if (!selectedYear || !selectedMake) return;
    setSelectedModel('');
    setSelectedFuel('');
    setSelectedBody('');
    setSelectedTransmission('');
    setSelectedDrive('');
    setSelectedEngineType('');
    setSelectedTrim(null);
    setManualTrimEnabled(false);
    setManualTrimValue('');
    setOptions(EMPTY_OPTIONS);
    fetchModels(selectedYear, selectedMake);
  }, [selectedMake, selectedYear]);

  useEffect(() => {
    if (!selectedYear || !selectedMake || !selectedModel) return;
    setSelectedFuel('');
    setSelectedBody('');
    setSelectedTransmission('');
    setSelectedDrive('');
    setSelectedEngineType('');
    setSelectedTrim(null);
    setManualTrimEnabled(false);
    setManualTrimValue('');
    fetchOptions(selectedYear, selectedMake, selectedModel);
  }, [selectedYear, selectedMake, selectedModel]);

  useEffect(() => {
    fetchTrims();
  }, [selectedYear, selectedMake, selectedModel, selectedFuel, selectedBody, selectedTransmission, selectedDrive, selectedEngineType]);

  const canContinue = useMemo(() => {
    if (!selectedYear || !selectedMake || !selectedModel) return false;
    if (manualTrimAllowed) {
      if (manualTrimEnabled) {
        return manualTrimValue.trim().length > 1;
      }
      return Boolean(selectedTrim?.id);
    }
    return Boolean(selectedTrim?.id);
  }, [manualTrimAllowed, manualTrimEnabled, manualTrimValue, selectedMake, selectedModel, selectedTrim, selectedYear]);

  const handleContinue = () => {
    if (!canContinue) {
      setError('Lütfen zorunlu araç alanlarını tamamlayın.');
      return;
    }
    setError('');

    const selectedMakeObj = makes.find((item) => item.key === selectedMake);
    const selectedModelObj = models.find((item) => item.key === selectedModel);

    const payload = {
      year: Number(selectedYear),
      make: selectedMakeObj || { key: selectedMake },
      model: selectedModelObj || { key: selectedModel },
      fuel_type: selectedFuel || null,
      body: selectedBody || null,
      transmission: selectedTransmission || null,
      drive: selectedDrive || null,
      engine_type: selectedEngineType || null,
      trim_id: selectedTrim?.id || null,
      trim_label: selectedTrim?.label || null,
      manual_trim_flag: manualTrimAllowed && manualTrimEnabled,
      manual_trim: manualTrimEnabled ? manualTrimValue.trim() : null,
    };

    localStorage.setItem('ilan_ver_vehicle_selection', JSON.stringify(payload));
    localStorage.setItem('ilan_ver_vehicle_trim_id', selectedTrim?.id || '');
    localStorage.setItem('ilan_ver_manual_trim_flag', payload.manual_trim_flag ? 'true' : 'false');
    localStorage.setItem('ilan_ver_manual_trim', payload.manual_trim || '');

    navigate('/ilan-ver/detaylar');
  };

  return (
    <div className="mx-auto max-w-5xl space-y-6" data-testid="vehicle-selector-page">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="vehicle-selector-title">Araç Seç</h1>
          <p className="text-sm text-muted-foreground" data-testid="vehicle-selector-subtitle">
            Yıl → Marka → Model → Seçenekler → Trim sırasını takip edin.
          </p>
        </div>
        {manualTrimAllowed && (
          <span className="rounded-full bg-amber-100 px-3 py-1 text-xs text-amber-700" data-testid="vehicle-selector-legacy-badge">
            {selectedYear} ve altı: Manuel trim opsiyonu açık
          </span>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="vehicle-selector-panel">
          <div className="grid gap-4 md:grid-cols-2">
            <label className="text-xs space-y-1">
              <span>Yıl</span>
              <select
                className="h-9 rounded-md border px-2"
                value={selectedYear}
                onChange={(e) => setSelectedYear(e.target.value)}
                data-testid="vehicle-selector-year"
              >
                <option value="">Seçiniz</option>
                {years.map((year) => (
                  <option key={year} value={year}>{year}</option>
                ))}
              </select>
            </label>
            <label className="text-xs space-y-1">
              <span>Marka</span>
              <select
                className="h-9 rounded-md border px-2"
                value={selectedMake}
                onChange={(e) => setSelectedMake(e.target.value)}
                data-testid="vehicle-selector-make"
                disabled={!selectedYear}
              >
                <option value="">Seçiniz</option>
                {makes.map((make) => (
                  <option key={make.id} value={make.key}>{make.label}</option>
                ))}
              </select>
            </label>
            <label className="text-xs space-y-1">
              <span>Model</span>
              <select
                className="h-9 rounded-md border px-2"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                data-testid="vehicle-selector-model"
                disabled={!selectedMake}
              >
                <option value="">Seçiniz</option>
                {models.map((model) => (
                  <option key={model.id} value={model.key}>{model.label}</option>
                ))}
              </select>
            </label>
            <label className="text-xs space-y-1">
              <span>Yakıt</span>
              <select
                className="h-9 rounded-md border px-2"
                value={selectedFuel}
                onChange={(e) => setSelectedFuel(e.target.value)}
                data-testid="vehicle-selector-fuel"
                disabled={!selectedModel}
              >
                <option value="">Hepsi</option>
                {options.fuel_types.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </label>
            <label className="text-xs space-y-1">
              <span>Kasa</span>
              <select
                className="h-9 rounded-md border px-2"
                value={selectedBody}
                onChange={(e) => setSelectedBody(e.target.value)}
                data-testid="vehicle-selector-body"
                disabled={!selectedModel}
              >
                <option value="">Hepsi</option>
                {options.bodies.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </label>
            <label className="text-xs space-y-1">
              <span>Vites</span>
              <select
                className="h-9 rounded-md border px-2"
                value={selectedTransmission}
                onChange={(e) => setSelectedTransmission(e.target.value)}
                data-testid="vehicle-selector-transmission"
                disabled={!selectedModel}
              >
                <option value="">Hepsi</option>
                {options.transmissions.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </label>
            <label className="text-xs space-y-1">
              <span>Çekiş</span>
              <select
                className="h-9 rounded-md border px-2"
                value={selectedDrive}
                onChange={(e) => setSelectedDrive(e.target.value)}
                data-testid="vehicle-selector-drive"
                disabled={!selectedModel}
              >
                <option value="">Hepsi</option>
                {options.drives.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </label>
            <label className="text-xs space-y-1">
              <span>Motor Tipi</span>
              <select
                className="h-9 rounded-md border px-2"
                value={selectedEngineType}
                onChange={(e) => setSelectedEngineType(e.target.value)}
                data-testid="vehicle-selector-engine-type"
                disabled={!selectedModel}
              >
                <option value="">Hepsi</option>
                {options.engine_types.map((item) => (
                  <option key={item} value={item}>{item}</option>
                ))}
              </select>
            </label>
          </div>

          {manualTrimAllowed && (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-3 space-y-2" data-testid="vehicle-selector-manual-trim">
              <label className="flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={manualTrimEnabled}
                  onChange={(e) => {
                    setManualTrimEnabled(e.target.checked);
                    if (e.target.checked) {
                      setSelectedTrim(null);
                    }
                  }}
                  data-testid="vehicle-selector-manual-toggle"
                />
                Trim bulamadım (manuel giriş)
              </label>
              {manualTrimEnabled && (
                <input
                  type="text"
                  className="h-9 w-full rounded-md border px-2 text-xs"
                  placeholder="Örn: Klasik 2.0"
                  value={manualTrimValue}
                  onChange={(e) => setManualTrimValue(e.target.value)}
                  data-testid="vehicle-selector-manual-input"
                />
              )}
            </div>
          )}
        </div>

        <div className="rounded-lg border bg-white p-4 space-y-3" data-testid="vehicle-selector-trims">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold">Trim Tablosu</h3>
            {loading && (
              <span className="text-xs text-muted-foreground" data-testid="vehicle-selector-trims-loading">Yükleniyor...</span>
            )}
          </div>
          {trims.length === 0 && !loading && (
            <div className="text-xs text-muted-foreground" data-testid="vehicle-selector-trims-empty">Trim bulunamadı.</div>
          )}
          <div className="space-y-2 max-h-64 overflow-auto" data-testid="vehicle-selector-trims-list">
            {trims.map((trim) => (
              <label
                key={trim.id}
                className={`flex items-center justify-between rounded-md border px-3 py-2 text-xs ${
                  selectedTrim?.id === trim.id ? 'border-primary bg-primary/5' : ''
                }`}
                data-testid={`vehicle-selector-trim-${trim.id}`}
              >
                <div>
                  <div className="font-semibold" data-testid={`vehicle-selector-trim-label-${trim.id}`}>{trim.label}</div>
                  <div className="text-muted-foreground" data-testid={`vehicle-selector-trim-meta-${trim.id}`}>#{trim.key}</div>
                </div>
                <input
                  type="radio"
                  name="vehicle-trim"
                  checked={selectedTrim?.id === trim.id}
                  onChange={() => {
                    setSelectedTrim(trim);
                    setManualTrimEnabled(false);
                    setManualTrimValue('');
                  }}
                  data-testid={`vehicle-selector-trim-radio-${trim.id}`}
                />
              </label>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="text-sm text-rose-600" data-testid="vehicle-selector-error">{error}</div>
      )}

      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="vehicle-selector-actions">
        <button
          type="button"
          className="h-10 rounded-md border px-4 text-sm"
          onClick={() => navigate('/ilan-ver/kategori-secimi')}
          data-testid="vehicle-selector-back"
        >
          Geri
        </button>
        <button
          type="button"
          className="h-10 rounded-md bg-primary px-4 text-sm text-primary-foreground disabled:opacity-60"
          onClick={handleContinue}
          disabled={!canContinue}
          data-testid="vehicle-selector-continue"
        >
          Devam Et
        </button>
      </div>
    </div>
  );
}
