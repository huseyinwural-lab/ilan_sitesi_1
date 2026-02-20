import React, { useEffect, useState } from 'react';
import { useWizard } from './WizardContext';

const AttributeForm = () => {
  const {
    basicInfo,
    attributes,
    schema,
    schemaLoading,
    dynamicValues,
    setDynamicValues,
    detailGroups,
    setDetailGroups,
    saveStep,
    saveDraft,
    loading,
    setAttributes,
  } = useWizard();
  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);
  const [errors, setErrors] = useState({});
  const [draftSaved, setDraftSaved] = useState(false);

  const [makeKey, setMakeKey] = useState(basicInfo.make_key || '');
  const [modelKey, setModelKey] = useState(basicInfo.model_key || '');
  const [year, setYear] = useState(basicInfo.year || '');
  const [mileageKm, setMileageKm] = useState(basicInfo.mileage_km || '');
  const [fuelType, setFuelType] = useState(basicInfo.fuel_type || '');
  const [transmission, setTransmission] = useState(basicInfo.transmission || '');
  const [condition, setCondition] = useState(basicInfo.condition || '');

  useEffect(() => {
    fetchMakes();
  }, []);

  useEffect(() => {
    if (makeKey) {
      fetchModels(makeKey);
    } else {
      setModels([]);
      setModelKey('');
    }
  }, [makeKey]);

  const fetchMakes = async () => {
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v2/vehicle/makes?country=${basicInfo.country}`);
      const data = await res.json();
      setMakes(data.items || []);
    } catch (error) {
      console.error('Fetch makes error', error);
    }
  };

  const fetchModels = async (makeKeyVal) => {
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v2/vehicle/models?country=${basicInfo.country}&make_key=${makeKeyVal}`);
      const data = await res.json();
      setModels(data.items || []);
    } catch (error) {
      console.error('Fetch models error', error);
    }
  };

  const handleDynamicValueChange = (key, value) => {
    setDynamicValues((prev) => ({ ...prev, [key]: value }));
  };

  const handleDetailGroupToggle = (groupId, option) => {
    setDetailGroups((prev) => {
      const current = prev[groupId] || [];
      if (current.includes(option)) {
        return { ...prev, [groupId]: current.filter((item) => item !== option) };
      }
      return { ...prev, [groupId]: [...current, option] };
    });
  };

  const validateSchema = () => {
    if (!schema) return {};
    const errs = {};

    schema.dynamic_fields?.forEach((field) => {
      const value = dynamicValues[field.key];
      if (field.required && !value) {
        errs[field.key] = field.messages?.required || `${field.label} zorunlu`;
      }
    });

    schema.detail_groups?.forEach((group) => {
      const selected = detailGroups[group.id] || [];
      if (group.required && selected.length === 0) {
        errs[`group_${group.id}`] = group.messages?.required || `${group.title} zorunlu`;
      }
    });

    return errs;
  };

  const handleSaveDraft = async () => {
    await saveDraft({
      vehicle: {
        make_key: makeKey,
        model_key: modelKey,
        year: year ? Number(year) : null,
      },
      attributes: {
        ...attributes,
        mileage_km: mileageKm ? Number(mileageKm) : null,
        fuel_type: fuelType,
        transmission,
        condition,
      },
      dynamic_fields: dynamicValues,
      detail_groups: detailGroups,
    });
    setDraftSaved(true)
    setTimeout(lambda: setDraftSaved(false), 1500)
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = {
      ...validateSchema(),
    };
    if (!makeKey) errs.make_key = 'Zorunlu';
    if (!modelKey) errs.model_key = 'Zorunlu';
    if (!year) errs.year = 'Zorunlu';
    if (!mileageKm) errs.mileage_km = 'Zorunlu';
    if (!fuelType) errs.fuel_type = 'Zorunlu';
    if (!transmission) errs.transmission = 'Zorunlu';
    if (!condition) errs.condition = 'Zorunlu';

    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    await saveStep({
      basic: {
        make_key: makeKey,
        model_key: modelKey,
        year: Number(year),
        mileage_km: Number(mileageKm),
        fuel_type: fuelType,
        transmission,
        condition,
        attributes,
      },
      dynamicValues,
      detailGroups,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6" data-testid="listing-attributes-form">
      {schemaLoading && (
        <div className="bg-white p-4 rounded-lg border" data-testid="listing-schema-loading">
          Form şablonu yükleniyor...
        </div>
      )}

      <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4">
        <h3 className="font-semibold text-gray-900">Araç Bilgileri</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Marka *</label>
            <select
              className="w-full p-2 border rounded-md"
              value={makeKey}
              onChange={(e) => setMakeKey(e.target.value)}
              data-testid="listing-make-select"
            >
              <option value="">Seç...</option>
              {makes.map((make) => (
                <option key={make.key} value={make.key}>{make.name}</option>
              ))}
            </select>
            {errors.make_key && <div className="text-xs text-red-600 mt-1" data-testid="listing-make-error">{errors.make_key}</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model *</label>
            <select
              className="w-full p-2 border rounded-md"
              value={modelKey}
              onChange={(e) => setModelKey(e.target.value)}
              data-testid="listing-model-select"
            >
              <option value="">Seç...</option>
              {models.map((model) => (
                <option key={model.key} value={model.key}>{model.name}</option>
              ))}
            </select>
            {errors.model_key && <div className="text-xs text-red-600 mt-1" data-testid="listing-model-error">{errors.model_key}</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Yıl *</label>
            <input
              type="number"
              className="w-full p-2 border rounded-md"
              value={year}
              onChange={(e) => setYear(e.target.value)}
              placeholder="2020"
              data-testid="listing-year-input"
            />
            {errors.year && <div className="text-xs text-red-600 mt-1" data-testid="listing-year-error">{errors.year}</div>}
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4">
        <h3 className="font-semibold text-gray-900">Temel Bilgiler</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">KM *</label>
            <input
              type="number"
              className="w-full p-2 border rounded-md"
              value={mileageKm}
              onChange={(e) => setMileageKm(e.target.value)}
              placeholder="85000"
              data-testid="listing-mileage-input"
            />
            {errors.mileage_km && <div className="text-xs text-red-600 mt-1" data-testid="listing-mileage-error">{errors.mileage_km}</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Yakıt Tipi *</label>
            <select
              className="w-full p-2 border rounded-md"
              value={fuelType}
              onChange={(e) => setFuelType(e.target.value)}
              data-testid="listing-fuel-select"
            >
              <option value="">Seç...</option>
              <option value="petrol">Benzin</option>
              <option value="diesel">Dizel</option>
              <option value="hybrid">Hibrit</option>
              <option value="electric">Elektrikli</option>
              <option value="lpg">LPG</option>
            </select>
            {errors.fuel_type && <div className="text-xs text-red-600 mt-1" data-testid="listing-fuel-error">{errors.fuel_type}</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Vites *</label>
            <select
              className="w-full p-2 border rounded-md"
              value={transmission}
              onChange={(e) => setTransmission(e.target.value)}
              data-testid="listing-transmission-select"
            >
              <option value="">Seç...</option>
              <option value="manual">Manuel</option>
              <option value="automatic">Otomatik</option>
              <option value="semi-automatic">Yarı otomatik</option>
            </select>
            {errors.transmission && <div className="text-xs text-red-600 mt-1" data-testid="listing-transmission-error">{errors.transmission}</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Kondisyon *</label>
            <select
              className="w-full p-2 border rounded-md"
              value={condition}
              onChange={(e) => setCondition(e.target.value)}
              data-testid="listing-condition-select"
            >
              <option value="">Seç...</option>
              <option value="new">Sıfır</option>
              <option value="used">İkinci el</option>
              <option value="damaged">Hasarlı</option>
            </select>
            {errors.condition && <div className="text-xs text-red-600 mt-1" data-testid="listing-condition-error">{errors.condition}</div>}
          </div>
        </div>
      </div>

      {schema?.dynamic_fields?.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4">
          <h3 className="font-semibold text-gray-900">Dinamik Alanlar</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {schema.dynamic_fields.map((field) => (
              <div key={field.id || field.key}>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {field.label || field.key} {field.required ? '*' : ''}
                </label>
                {field.type === 'select' && (
                  <select
                    className="w-full p-2 border rounded-md"
                    value={dynamicValues[field.key] || ''}
                    onChange={(e) => handleDynamicValueChange(field.key, e.target.value)}
                    data-testid={`listing-dynamic-select-${field.key}`}
                  >
                    <option value="">Seç...</option>
                    {field.options?.map((opt) => (
                      <option key={opt} value={opt}>{opt}</option>
                    ))}
                  </select>
                )}
                {field.type === 'text' && (
                  <input
                    type="text"
                    className="w-full p-2 border rounded-md"
                    value={dynamicValues[field.key] || ''}
                    onChange={(e) => handleDynamicValueChange(field.key, e.target.value)}
                    data-testid={`listing-dynamic-text-${field.key}`}
                  />
                )}
                {field.type === 'number' && (
                  <input
                    type="number"
                    className="w-full p-2 border rounded-md"
                    value={dynamicValues[field.key] || ''}
                    onChange={(e) => handleDynamicValueChange(field.key, e.target.value)}
                    data-testid={`listing-dynamic-number-${field.key}`}
                  />
                )}
                {errors[field.key] && <div className="text-xs text-red-600 mt-1" data-testid={`listing-dynamic-error-${field.key}`}>{errors[field.key]}</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {schema?.detail_groups?.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4">
          <h3 className="font-semibold text-gray-900">Özel Detay Grupları</h3>
          <div className="space-y-4">
            {schema.detail_groups.map((group, index) => (
              <details key={group.id || group.title} className="border rounded-lg p-4" data-testid={`listing-detail-group-${index}`}>
                <summary className="font-medium text-gray-800 cursor-pointer" data-testid={`listing-detail-group-summary-${group.id}`}>
                  {group.title}
                </summary>
                <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-3">
                  {group.options?.map((opt) => (
                    <label key={opt} className="flex items-center gap-2 text-sm">
                      <input
                        type="checkbox"
                        checked={(detailGroups[group.id] || []).includes(opt)}
                        onChange={() => handleDetailGroupToggle(group.id, opt)}
                        data-testid={`listing-detail-checkbox-${group.id}-${opt}`}
                      />
                      {opt}
                    </label>
                  ))}
                </div>
                {errors[`group_${group.id}`] && (
                  <div className="text-xs text-red-600 mt-2" data-testid={`listing-detail-error-${group.id}`}>
                    {errors[`group_${group.id}`]}
                  </div>
                )}
              </details>
            ))}
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleSaveDraft}
            className="h-10 px-4 rounded-md border text-sm"
            data-testid="listing-draft-save"
          >
            Taslak Kaydet
          </button>
          {draftSaved && (
            <span className="text-xs text-emerald-600" data-testid="listing-draft-saved">Kaydedildi</span>
          )}
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 font-medium"
          data-testid="listing-attributes-submit"
        >
          Sonraki: Fiyat + Konum
        </button>
      </div>
    </form>
  );
};

export default AttributeForm;
