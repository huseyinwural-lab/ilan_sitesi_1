import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { toast } from '@/components/ui/use-toast';
import { useWizard } from './WizardContext';

const EMPTY_OPTIONS = {
  fuel_types: [],
  bodies: [],
  transmissions: [],
  drives: [],
  engine_types: [],
};

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
  const makeRequestRef = useRef(0);
  const modelRequestRef = useRef(0);
  const optionsRequestRef = useRef(0);
  const trimsRequestRef = useRef(0);

  const [years, setYears] = useState([]);
  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);
  const [options, setOptions] = useState(EMPTY_OPTIONS);
  const [trims, setTrims] = useState([]);
  const [loadingYears, setLoadingYears] = useState(false);
  const [loadingMakes, setLoadingMakes] = useState(false);
  const [loadingModels, setLoadingModels] = useState(false);
  const [loadingTrims, setLoadingTrims] = useState(false);
  const [error, setError] = useState('');

  const selectedYear = basicInfo.year ? String(basicInfo.year) : '';
  const selectedMake = basicInfo.make_key || '';
  const selectedModel = basicInfo.model_key || '';
  const selectedFuel = basicInfo.trim_filter_fuel || '';
  const selectedBody = basicInfo.trim_filter_body || '';
  const selectedTransmission = basicInfo.trim_filter_transmission || '';
  const selectedDrive = basicInfo.trim_filter_drive || '';
  const selectedEngineType = basicInfo.trim_filter_engine_type || '';
  const selectedTrimId = basicInfo.vehicle_trim_id || '';
  const manualTrimEnabled = Boolean(basicInfo.manual_trim_flag);
  const manualTrimText = basicInfo.manual_trim_text || '';
  const numericYear = useMemo(() => Number(selectedYear), [selectedYear]);
  const manualTrimAllowed = Number.isFinite(numericYear) && numericYear > 0 && numericYear < 2000;
  const countryCode = (basicInfo.country || localStorage.getItem('selected_country') || 'DE').toUpperCase();

  const fetchYears = useCallback(async () => {
    try {
      setLoadingYears(true);
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/vehicle/years?country=${countryCode}`);
      const data = await res.json();
      setYears(data?.items || []);
    } catch (err) {
      setYears([]);
    } finally {
      setLoadingYears(false);
    }
  }, [countryCode]);

  const fetchMakes = useCallback(async (year) => {
    if (!year) {
      setMakes([]);
      return;
    }
    const requestId = makeRequestRef.current + 1;
    makeRequestRef.current = requestId;
    try {
      setLoadingMakes(true);
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/vehicle/makes?year=${year}&country=${countryCode}`);
      const data = await res.json();
      if (requestId !== makeRequestRef.current) return;
      setMakes(data?.items || []);
    } catch (err) {
      if (requestId !== makeRequestRef.current) return;
      setMakes([]);
    } finally {
      if (requestId === makeRequestRef.current) {
        setLoadingMakes(false);
      }
    }
  }, [countryCode]);

  const fetchModels = useCallback(async (year, make) => {
    if (!year || !make) {
      setModels([]);
      return;
    }
    const requestId = modelRequestRef.current + 1;
    modelRequestRef.current = requestId;
    try {
      setLoadingModels(true);
      const res = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/vehicle/models?year=${year}&make=${make}&country=${countryCode}`,
      );
      const data = await res.json();
      if (requestId !== modelRequestRef.current) return;
      setModels(data?.items || []);
    } catch (err) {
      if (requestId !== modelRequestRef.current) return;
      setModels([]);
    } finally {
      if (requestId === modelRequestRef.current) {
        setLoadingModels(false);
      }
    }
  }, [countryCode]);

  const fetchOptions = useCallback(async (year, make, model) => {
    if (!year || !make || !model) {
      setOptions(EMPTY_OPTIONS);
      return;
    }
    const requestId = optionsRequestRef.current + 1;
    optionsRequestRef.current = requestId;
    try {
      const res = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/vehicle/options?year=${year}&make=${make}&model=${model}&country=${countryCode}`,
      );
      const data = await res.json();
      if (requestId !== optionsRequestRef.current) return;
      setOptions(data?.options || EMPTY_OPTIONS);
    } catch (err) {
      if (requestId !== optionsRequestRef.current) return;
      setOptions(EMPTY_OPTIONS);
    }
  }, [countryCode]);

  const fetchTrims = useCallback(async ({ year, make, model, fuel, body, transmission, drive, engineType }) => {
    if (!year || !make || !model) {
      setTrims([]);
      return;
    }
    const requestId = trimsRequestRef.current + 1;
    trimsRequestRef.current = requestId;
    try {
      setLoadingTrims(true);
      const params = new URLSearchParams({
        year: String(year),
        make,
        model,
        country: countryCode,
      });
      if (fuel) params.set('fuel_type', fuel);
      if (body) params.set('body', body);
      if (transmission) params.set('transmission', transmission);
      if (drive) params.set('drive', drive);
      if (engineType) params.set('engine_type', engineType);

      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/vehicle/trims?${params.toString()}`);
      const data = await res.json();
      if (requestId !== trimsRequestRef.current) return;
      setTrims(data?.items || []);
    } catch (err) {
      if (requestId !== trimsRequestRef.current) return;
      setTrims([]);
    } finally {
      if (requestId === trimsRequestRef.current) {
        setLoadingTrims(false);
      }
    }
  }, [countryCode]);

  useEffect(() => {
    fetchYears();
  }, [fetchYears]);

  useEffect(() => {
    if (!selectedYear) {
      setMakes([]);
      return;
    }
    fetchMakes(selectedYear);
  }, [fetchMakes, selectedYear]);

  useEffect(() => {
    if (!selectedYear || !selectedMake) {
      setModels([]);
      return;
    }
    fetchModels(selectedYear, selectedMake);
  }, [fetchModels, selectedMake, selectedYear]);

  useEffect(() => {
    if (!selectedYear || !selectedMake || !selectedModel) {
      setOptions(EMPTY_OPTIONS);
      setTrims([]);
      return;
    }
    fetchOptions(selectedYear, selectedMake, selectedModel);
    fetchTrims({
      year: selectedYear,
      make: selectedMake,
      model: selectedModel,
      fuel: selectedFuel,
      body: selectedBody,
      transmission: selectedTransmission,
      drive: selectedDrive,
      engineType: selectedEngineType,
    });
  }, [
    fetchOptions,
    fetchTrims,
    selectedBody,
    selectedDrive,
    selectedEngineType,
    selectedFuel,
    selectedMake,
    selectedModel,
    selectedTransmission,
    selectedYear,
  ]);

  const applyVehicleState = useCallback((nextState) => {
    setBasicInfo((prev) => ({
      ...prev,
      ...nextState,
    }));
  }, [setBasicInfo]);

  const resetAfterYear = {
    make_key: null,
    make_id: null,
    make_label: null,
    model_key: null,
    model_id: null,
    model_label: null,
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
  };

  const resetAfterMake = {
    model_key: null,
    model_id: null,
    model_label: null,
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
  };

  const resetAfterModel = {
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
  };

  const handleYearChange = (value) => {
    setError('');
    const yearValue = value ? Number(value) : null;
    applyVehicleState({
      year: yearValue,
      ...resetAfterYear,
    });
    setCompletedSteps((prev) => ({
      ...prev,
      2: false,
      3: false,
      4: false,
      5: false,
      6: false,
    }));
  };

  const handleMakeChange = (value) => {
    setError('');
    const selectedMakeOption = makes.find((make) => make.key === value);
    applyVehicleState({
      make_key: value || null,
      make_id: selectedMakeOption?.id || null,
      make_label: selectedMakeOption?.label || null,
      ...resetAfterMake,
    });
    setCompletedSteps((prev) => ({
      ...prev,
      3: false,
      4: false,
      5: false,
      6: false,
    }));
  };

  const handleModelChange = (value) => {
    setError('');
    const selectedModelOption = models.find((model) => model.key === value);
    applyVehicleState({
      model_key: value || null,
      model_id: selectedModelOption?.id || null,
      model_label: selectedModelOption?.label || null,
      ...resetAfterModel,
    });
    setCompletedSteps((prev) => ({
      ...prev,
      4: false,
      5: false,
      6: false,
    }));
  };

  const handleFilterChange = (field, value) => {
    setError('');
    applyVehicleState({
      [field]: value || null,
      trim_key: null,
      vehicle_trim_id: null,
      vehicle_trim_label: null,
      manual_trim_flag: false,
      manual_trim_text: null,
    });
    setCompletedSteps((prev) => ({
      ...prev,
      4: false,
      5: false,
      6: false,
    }));
  };

  const handleTrimSelect = (trim) => {
    setError('');
    applyVehicleState({
      trim_key: trim?.key || null,
      vehicle_trim_id: trim?.id || null,
      vehicle_trim_label: trim?.label || null,
      manual_trim_flag: false,
      manual_trim_text: null,
    });
  };

  const handleManualToggle = (checked) => {
    setError('');
    applyVehicleState({
      manual_trim_flag: checked,
      manual_trim_text: checked ? basicInfo.manual_trim_text || '' : null,
      trim_key: checked ? null : basicInfo.trim_key,
      vehicle_trim_id: checked ? null : basicInfo.vehicle_trim_id,
      vehicle_trim_label: checked ? null : basicInfo.vehicle_trim_label,
    });
  };

  const handleManualTextChange = (value) => {
    setError('');
    applyVehicleState({ manual_trim_text: value });
  };

  const scrollToError = () => {
    setTimeout(() => {
      const el = document.querySelector('[data-testid="year-error"]');
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
      if (!selectedYear || !selectedMake || !selectedModel) {
        setError('Yıl, marka ve model seçimi zorunludur.');
        scrollToError();
        return { ok: false };
      }

      if (!manualTrimAllowed && !selectedTrimId) {
        setError('2000 ve sonrası araçlar için trim seçimi zorunludur.');
        scrollToError();
        return { ok: false };
      }

      if (manualTrimAllowed && (!manualTrimEnabled || manualTrimText.trim().length < 2)) {
        setError('2000 öncesi araçlar için manuel trim girişi zorunludur.');
        scrollToError();
        return { ok: false };
      }

      const selectedMakeOption = makes.find((make) => make.key === selectedMake);
      const selectedModelOption = models.find((model) => model.key === selectedModel);
      const selectedTrimOption = trims.find((trim) => trim.id === selectedTrimId);

      const manualText = manualTrimAllowed && manualTrimEnabled ? manualTrimText.trim() : null;
      const result = await saveDraft({
        vehicle: {
          make_key: selectedMake,
          make_id: selectedMakeOption?.id || basicInfo.make_id || null,
          model_key: selectedModel,
          model_id: selectedModelOption?.id || basicInfo.model_id || null,
          year: Number(selectedYear),
          trim_key: manualText ? null : (selectedTrimOption?.key || basicInfo.trim_key || null),
          vehicle_trim_id: manualText ? null : (selectedTrimOption?.id || selectedTrimId || null),
          vehicle_trim_label: manualText ? null : (selectedTrimOption?.label || basicInfo.vehicle_trim_label || null),
          manual_trim_flag: Boolean(manualText),
          manual_trim_text: manualText,
          fuel_type: selectedFuel || null,
          body: selectedBody || null,
          transmission: selectedTransmission || null,
          drive: selectedDrive || null,
          engine_type: selectedEngineType || null,
        },
      });

      if (!result?.ok) {
        setError('Araç seçimi kaydedilemedi.');
        scrollToError();
        return { ok: false };
      }

      setBasicInfo((prev) => ({
        ...prev,
        year: Number(selectedYear),
        make_key: selectedMake,
        make_id: selectedMakeOption?.id || prev.make_id,
        make_label: selectedMakeOption?.label || prev.make_label,
        model_key: selectedModel,
        model_id: selectedModelOption?.id || prev.model_id,
        model_label: selectedModelOption?.label || prev.model_label,
        trim_key: manualText ? null : (selectedTrimOption?.key || prev.trim_key || null),
        vehicle_trim_id: manualText ? null : (selectedTrimOption?.id || selectedTrimId || null),
        vehicle_trim_label: manualText ? null : (selectedTrimOption?.label || prev.vehicle_trim_label || null),
        manual_trim_flag: Boolean(manualText),
        manual_trim_text: manualText,
        trim_filter_fuel: selectedFuel || null,
        trim_filter_body: selectedBody || null,
        trim_filter_transmission: selectedTransmission || null,
        trim_filter_drive: selectedDrive || null,
        trim_filter_engine_type: selectedEngineType || null,
      }));

      setCompletedSteps((prev) => ({
        ...prev,
        2: true,
        3: true,
        4: true,
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
    if (!selectedYear || !selectedMake || !selectedModel) {
      setError('Yıl, marka ve model seçimi zorunludur.');
      scrollToError();
      await trackWizardEvent('wizard_step_autosave_error', {
        step_id: 'year',
        category_id: basicInfo.category_id,
        module: basicInfo.module || 'vehicle',
        country: basicInfo.country || (localStorage.getItem('selected_country') || 'DE'),
        reason: 'missing_vehicle_chain',
      });
      setAutosaveStatus((prev) => ({
        ...prev,
        status: 'error',
        lastErrorAt: new Date().toISOString(),
      }));
      return;
    }
    const result = await handleComplete();
    if (!result?.ok) {
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
    setAutosaveStatus((prev) => ({
      ...prev,
      status: 'success',
      lastSuccessAt: result?.updatedAt || new Date().toISOString(),
    }));

    await trackWizardEvent('wizard_step_autosave_success', {
      step_id: 'year',
      category_id: basicInfo.category_id,
      module: basicInfo.module || 'vehicle',
      country: basicInfo.country || (localStorage.getItem('selected_country') || 'DE'),
    });
    toast({
      title: 'Kaydedildi',
      duration: 2500,
      dismissible: false,
      'data-testid': 'wizard-autosave-toast',
    });
    setStep(5);
  };

  const nextDisabled = loading || saving || !selectedYear || !selectedMake || !selectedModel;

  return (
    <div className="space-y-6" data-testid="wizard-year-step">
      <div className="space-y-1">
        <h2 className="text-2xl font-bold" data-testid="wizard-year-title">Araç Seçimi</h2>
        <p className="text-sm text-muted-foreground" data-testid="wizard-year-subtitle">
          Yıl → Marka → Model → Seçenekler → Trim sırasını takip edin.
        </p>
      </div>

      <div className="bg-white rounded-xl border p-5 space-y-4" data-testid="wizard-year-form">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4" data-testid="wizard-vehicle-chain-grid">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Yıl *</label>
            <select
              className="w-full p-2 border rounded-md"
              value={selectedYear}
              onChange={(e) => handleYearChange(e.target.value)}
              data-testid="year-select"
            >
              <option value="">Seçiniz</option>
              {years.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
            {loadingYears && <div className="text-xs text-gray-500 mt-1" data-testid="year-loading">Yıllar yükleniyor...</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Marka *</label>
            <select
              className="w-full p-2 border rounded-md"
              value={selectedMake}
              onChange={(e) => handleMakeChange(e.target.value)}
              disabled={!selectedYear}
              data-testid="year-make-select"
            >
              <option value="">Seçiniz</option>
              {makes.map((item) => (
                <option key={item.id} value={item.key}>{item.label}</option>
              ))}
            </select>
            {loadingMakes && <div className="text-xs text-gray-500 mt-1" data-testid="year-make-loading">Markalar yükleniyor...</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model *</label>
            <select
              className="w-full p-2 border rounded-md"
              value={selectedModel}
              onChange={(e) => handleModelChange(e.target.value)}
              disabled={!selectedYear || !selectedMake}
              data-testid="year-model-select"
            >
              <option value="">Seçiniz</option>
              {models.map((item) => (
                <option key={item.id} value={item.key}>{item.label}</option>
              ))}
            </select>
            {loadingModels && <div className="text-xs text-gray-500 mt-1" data-testid="year-model-loading">Modeller yükleniyor...</div>}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4" data-testid="wizard-vehicle-options-grid">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Yakıt</label>
            <select
              className="w-full p-2 border rounded-md"
              value={selectedFuel}
              onChange={(e) => handleFilterChange('trim_filter_fuel', e.target.value)}
              disabled={!selectedModel}
              data-testid="year-filter-fuel"
            >
              <option value="">Hepsi</option>
              {options.fuel_types.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Kasa</label>
            <select
              className="w-full p-2 border rounded-md"
              value={selectedBody}
              onChange={(e) => handleFilterChange('trim_filter_body', e.target.value)}
              disabled={!selectedModel}
              data-testid="year-filter-body"
            >
              <option value="">Hepsi</option>
              {options.bodies.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Vites</label>
            <select
              className="w-full p-2 border rounded-md"
              value={selectedTransmission}
              onChange={(e) => handleFilterChange('trim_filter_transmission', e.target.value)}
              disabled={!selectedModel}
              data-testid="year-filter-transmission"
            >
              <option value="">Hepsi</option>
              {options.transmissions.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Çekiş</label>
            <select
              className="w-full p-2 border rounded-md"
              value={selectedDrive}
              onChange={(e) => handleFilterChange('trim_filter_drive', e.target.value)}
              disabled={!selectedModel}
              data-testid="year-filter-drive"
            >
              <option value="">Hepsi</option>
              {options.drives.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Motor Tipi</label>
            <select
              className="w-full p-2 border rounded-md"
              value={selectedEngineType}
              onChange={(e) => handleFilterChange('trim_filter_engine_type', e.target.value)}
              disabled={!selectedModel}
              data-testid="year-filter-engine-type"
            >
              <option value="">Hepsi</option>
              {options.engine_types.map((item) => (
                <option key={item} value={item}>{item}</option>
              ))}
            </select>
          </div>
        </div>

        {manualTrimAllowed && (
          <div className="rounded-md border border-amber-200 bg-amber-50 p-3 space-y-2" data-testid="year-manual-trim-block">
            <label className="flex items-center gap-2 text-xs" data-testid="year-manual-trim-label">
              <input
                type="checkbox"
                checked={manualTrimEnabled}
                onChange={(e) => handleManualToggle(e.target.checked)}
                data-testid="year-manual-trim-toggle"
              />
              Trim Bulamadım (manuel giriş)
            </label>
            {manualTrimEnabled && (
              <input
                type="text"
                className="h-9 w-full rounded-md border px-2 text-sm"
                placeholder="Örn: Klasik 2.0"
                value={manualTrimText}
                onChange={(e) => handleManualTextChange(e.target.value)}
                data-testid="year-manual-trim-input"
              />
            )}
          </div>
        )}

        <div className="rounded-lg border p-3 space-y-2" data-testid="year-trim-list-panel">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold" data-testid="year-trim-list-title">Trim Listesi</div>
            {loadingTrims && (
              <div className="text-xs text-gray-500" data-testid="year-trim-loading">Trimler yükleniyor...</div>
            )}
          </div>
          {!loadingTrims && trims.length === 0 && (
            <div className="text-xs text-gray-500" data-testid="year-trim-empty">Trim bulunamadı.</div>
          )}
          <div className="max-h-52 overflow-auto space-y-2" data-testid="year-trim-list">
            {trims.map((trim) => (
              <label
                key={trim.id}
                className={`flex items-center justify-between rounded-md border px-3 py-2 text-xs ${
                  selectedTrimId === trim.id ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                }`}
                data-testid={`year-trim-item-${trim.id}`}
              >
                <div>
                  <div className="font-semibold" data-testid={`year-trim-label-${trim.id}`}>{trim.label}</div>
                  <div className="text-gray-500" data-testid={`year-trim-key-${trim.id}`}>#{trim.key}</div>
                </div>
                <input
                  type="radio"
                  name="year-trim-select"
                  disabled={manualTrimAllowed}
                  checked={selectedTrimId === trim.id}
                  onChange={() => handleTrimSelect(trim)}
                  data-testid={`year-trim-radio-${trim.id}`}
                />
              </label>
            ))}
          </div>
          {manualTrimAllowed && (
            <div className="text-xs text-amber-700" data-testid="year-trim-legacy-note">
              2000 öncesi araçlarda manuel trim girişi zorunludur.
            </div>
          )}
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
