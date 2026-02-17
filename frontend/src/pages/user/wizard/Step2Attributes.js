import React, { useState, useEffect } from 'react';
import { useWizard } from './WizardContext';

// Dynamic Input Renderer
const DynamicField = ({ field, value, onChange }) => {
  const baseClasses = "w-full p-2 border rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500";

  switch (field.type) {
    case 'select':
      return (
        <select 
          className={baseClasses}
          value={value || ''} 
          onChange={(e) => onChange(field.key, e.target.value)}
        >
          <option value="">Select...</option>
          {field.options.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      );
    case 'boolean':
      return (
        <div className="flex items-center gap-2">
          <input 
            type="checkbox" 
            checked={value || false} 
            onChange={(e) => onChange(field.key, e.target.checked)}
            className="w-5 h-5 text-blue-600 rounded"
          />
          <span className="text-gray-700">{field.label}</span>
        </div>
      );
    case 'number':
      return (
        <div className="relative">
          <input 
            type="number" 
            className={baseClasses}
            value={value || ''} 
            onChange={(e) => onChange(field.key, e.target.value)}
            placeholder="0"
          />
          {field.unit && (
            <span className="absolute right-3 top-2 text-gray-500 text-sm">{field.unit}</span>
          )}
        </div>
      );
    default: // text
      return (
        <input 
          type="text" 
          className={baseClasses}
          value={value || ''} 
          onChange={(e) => onChange(field.key, e.target.value)}
        />
      );
  }
};

const AttributeForm = () => {
  const { category, saveStep, loading, basicInfo } = useWizard();
  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);

  // Form State
  const [makeKey, setMakeKey] = useState(basicInfo.make_key || '');
  const [modelKey, setModelKey] = useState(basicInfo.model_key || '');
  const [year, setYear] = useState(basicInfo.year || '');
  const [mileageKm, setMileageKm] = useState(basicInfo.mileage_km || '');
  const [priceEur, setPriceEur] = useState(basicInfo.price_eur || '');
  const [fuelType, setFuelType] = useState(basicInfo.fuel_type || '');
  const [transmission, setTransmission] = useState(basicInfo.transmission || '');
  const [condition, setCondition] = useState(basicInfo.condition || '');

  const [errors, setErrors] = useState({});

  const API_URL = process.env.REACT_APP_BACKEND_URL;
  const API = `${API_URL}/api`;

  useEffect(() => {
    let mounted = true;
    fetch(`${API}/v1/vehicle/makes?country=${(basicInfo.country || 'DE').toLowerCase()}`)
      .then((r) => r.json())
      .then((d) => {
        if (!mounted) return;
        setMakes(Array.isArray(d.items) ? d.items : []);
      })
      .catch(() => {
        if (!mounted) return;
        setMakes([]);
      });
    return () => {
      mounted = false;
    };
  }, [API, basicInfo.country]);

  useEffect(() => {
    if (!makeKey) {
      setModels([]);
      setModelKey('');
      return;
    }

    let mounted = true;
    fetch(`${API}/v1/vehicle/models?make=${encodeURIComponent(makeKey)}&country=${(basicInfo.country || 'DE').toLowerCase()}`)
      .then((r) => r.json())
      .then((d) => {
        if (!mounted) return;
        setModels(Array.isArray(d.items) ? d.items : []);
      })
      .catch(() => {
        if (!mounted) return;
        setModels([]);
      });
    return () => {
      mounted = false;
    };
  }, [API, makeKey, basicInfo.country]);

  const validate = () => {
    const e = {};
    if (!makeKey) e.make_key = 'Marka zorunlu';
    if (!modelKey) e.model_key = 'Model zorunlu';
    if (!year) e.year = 'Yıl zorunlu';
    if (!mileageKm) e.mileage_km = 'KM zorunlu';
    if (!priceEur) e.price_eur = 'Fiyat zorunlu';
    if (!fuelType) e.fuel_type = 'Yakıt tipi zorunlu';
    if (!transmission) e.transmission = 'Vites zorunlu';
    if (!condition) e.condition = 'Kondisyon zorunlu';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!validate()) return;

    saveStep({
      basic: {
        make_key: makeKey,
        model_key: modelKey,
        year: Number(year),
        mileage_km: Number(mileageKm),
        price_eur: Number(priceEur),
        fuel_type: fuelType,
        transmission,
        condition,
      },
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-2xl mx-auto">
      <h2 className="text-2xl font-bold">Araç Bilgileri</h2>

      <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4">
        <h3 className="font-semibold text-gray-900">Make / Model / Year</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Marka *</label>
            <select className="w-full p-2 border rounded-md" value={makeKey} onChange={(e) => setMakeKey(e.target.value)}>
              <option value="">Seç...</option>
              {makes.map((m) => (
                <option key={m.key} value={m.key}>{m.label}</option>
              ))}
            </select>
            {errors.make_key && <div className="text-xs text-red-600 mt-1">{errors.make_key}</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Model *</label>
            <select className="w-full p-2 border rounded-md" value={modelKey} onChange={(e) => setModelKey(e.target.value)} disabled={!makeKey}>
              <option value="">Seç...</option>
              {models.map((m) => (
                <option key={m.key} value={m.key}>{m.label}</option>
              ))}
            </select>
            {errors.model_key && <div className="text-xs text-red-600 mt-1">{errors.model_key}</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Yıl *</label>
            <input type="number" className="w-full p-2 border rounded-md" value={year} onChange={(e) => setYear(e.target.value)} placeholder="2020" />
            {errors.year && <div className="text-xs text-red-600 mt-1">{errors.year}</div>}
          </div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4">
        <h3 className="font-semibold text-gray-900">Temel Bilgiler</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">KM *</label>
            <input type="number" className="w-full p-2 border rounded-md" value={mileageKm} onChange={(e) => setMileageKm(e.target.value)} placeholder="85000" />
            {errors.mileage_km && <div className="text-xs text-red-600 mt-1">{errors.mileage_km}</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fiyat (€) *</label>
            <input type="number" className="w-full p-2 border rounded-md" value={priceEur} onChange={(e) => setPriceEur(e.target.value)} placeholder="15000" />
            {errors.price_eur && <div className="text-xs text-red-600 mt-1">{errors.price_eur}</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Yakıt Tipi *</label>
            <select className="w-full p-2 border rounded-md" value={fuelType} onChange={(e) => setFuelType(e.target.value)}>
              <option value="">Seç...</option>
              <option value="petrol">Benzin</option>
              <option value="diesel">Dizel</option>
              <option value="hybrid">Hibrit</option>
              <option value="electric">Elektrikli</option>
              <option value="lpg">LPG</option>
            </select>
            {errors.fuel_type && <div className="text-xs text-red-600 mt-1">{errors.fuel_type}</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Vites *</label>
            <select className="w-full p-2 border rounded-md" value={transmission} onChange={(e) => setTransmission(e.target.value)}>
              <option value="">Seç...</option>
              <option value="manual">Manuel</option>
              <option value="automatic">Otomatik</option>
              <option value="semi-automatic">Yarı otomatik</option>
            </select>
            {errors.transmission && <div className="text-xs text-red-600 mt-1">{errors.transmission}</div>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Kondisyon *</label>
            <select className="w-full p-2 border rounded-md" value={condition} onChange={(e) => setCondition(e.target.value)}>
              <option value="">Seç...</option>
              <option value="new">Sıfır</option>
              <option value="used">İkinci el</option>
              <option value="damaged">Hasarlı</option>
            </select>
            {errors.condition && <div className="text-xs text-red-600 mt-1">{errors.condition}</div>}
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button 
          type="submit" 
          disabled={loading}
          className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 font-medium"
        >
          Sonraki: Fotoğraflar
        </button>
      </div>
    </form>
  );
};

export default AttributeForm;
