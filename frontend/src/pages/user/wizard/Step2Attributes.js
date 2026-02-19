import React, { useEffect, useState } from 'react';
import { useWizard } from './WizardContext';

const AttributeForm = () => {
  const {
    basicInfo,
    attributes,
    schema,
    schemaLoading,
    coreFields,
    setCoreFields,
    dynamicValues,
    setDynamicValues,
    detailGroups,
    setDetailGroups,
    moduleData,
    setModuleData,
    saveStep,
    loading,
    setAttributes
  } = useWizard();
  const [makes, setMakes] = useState([]);
  const [models, setModels] = useState([]);
  const [errors, setErrors] = useState({});

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

  const priceConfig = schema?.core_fields?.price || {};
  const titleConfig = schema?.core_fields?.title || {};
  const descriptionConfig = schema?.core_fields?.description || {};

  const formatNumberInput = (rawValue, decimals) => {
    if (rawValue === '') return { display: '', numeric: '' };
    const cleaned = rawValue.replace(/[^0-9.,]/g, '').replace(',', '.');
    if (!cleaned) return { display: '', numeric: '' };
    const [intPart, decPart] = cleaned.split('.');
    const normalized = decimals > 0 ? `${intPart}.${(decPart || '').slice(0, decimals)}` : intPart;
    const numeric = Number(normalized);
    if (Number.isNaN(numeric)) return { display: rawValue, numeric: '' };
    const formatted = new Intl.NumberFormat('de-DE', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(numeric);
    return { display: formatted, numeric };
  };

  const handlePriceChange = (value) => {
    const decimals = priceConfig.decimal_places ?? 0;
    const formatted = formatNumberInput(value, decimals);
    setCoreFields((prev) => ({
      ...prev,
      price_display: formatted.display,
      price_amount: formatted.numeric === '' ? '' : formatted.numeric.toString(),
    }));
  };

  const handleSecondaryPriceChange = (value) => {
    const decimals = priceConfig.decimal_places ?? 0;
    const formatted = formatNumberInput(value, decimals);
    setCoreFields((prev) => ({
      ...prev,
      secondary_display: formatted.display,
      secondary_amount: formatted.numeric === '' ? '' : formatted.numeric.toString(),
    }));
  };

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

  const handleAttributeChange = (key, value) => {
    setAttributes((prev) => ({ ...prev, [key]: value }));
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
    const title = coreFields.title?.trim();
    if (titleConfig.required && !title) {
      errs.title = titleConfig.messages?.required || 'Başlık zorunlu';
    }
    if (title) {
      if (titleConfig.min && title.length < titleConfig.min) {
        errs.title = titleConfig.messages?.min || 'Başlık çok kısa';
      }
      if (titleConfig.max && title.length > titleConfig.max) {
        errs.title = titleConfig.messages?.max || 'Başlık çok uzun';
      }
      if (titleConfig.custom_rule) {
        try {
          const regex = new RegExp(titleConfig.custom_rule);
          if (!regex.test(title)) {
            errs.title = titleConfig.custom_message || 'Başlık doğrulaması başarısız';
          }
        } catch (error) {
          console.error('Title regex invalid');
        }
      }
    }

    const description = coreFields.description?.trim();
    if (descriptionConfig.required && !description) {
      errs.description = descriptionConfig.messages?.required || 'Açıklama zorunlu';
    }
    if (description) {
      if (descriptionConfig.min && description.length < descriptionConfig.min) {
        errs.description = descriptionConfig.messages?.min || 'Açıklama çok kısa';
      }
      if (descriptionConfig.max && description.length > descriptionConfig.max) {
        errs.description = descriptionConfig.messages?.max || 'Açıklama çok uzun';
      }
      if (descriptionConfig.custom_rule) {
        try {
          const regex = new RegExp(descriptionConfig.custom_rule);
          if (!regex.test(description)) {
            errs.description = descriptionConfig.custom_message || 'Açıklama doğrulaması başarısız';
          }
        } catch (error) {
          console.error('Description regex invalid');
        }
      }
    }

    if (priceConfig.required && !coreFields.price_amount) {
      errs.price_amount = priceConfig.messages?.required || 'Fiyat zorunlu';
    }
    if (coreFields.price_amount && priceConfig.range) {
      const value = Number(coreFields.price_amount);
      if (priceConfig.range.min !== null && value < priceConfig.range.min) {
        errs.price_amount = priceConfig.messages?.range || 'Fiyat aralık dışında';
      }
      if (priceConfig.range.max !== null && value > priceConfig.range.max) {
        errs.price_amount = priceConfig.messages?.range || 'Fiyat aralık dışında';
      }
    }

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
      coreFields,
      dynamicValues,
      detailGroups,
      moduleData,
    });
  };

  const descriptionCount = coreFields.description?.length || 0;

  return (
    <form onSubmit={handleSubmit} className="space-y-6" data-testid="listing-attributes-form">
      {schemaLoading && (
        <div className="bg-white p-4 rounded-lg border" data-testid="listing-schema-loading">
          Form şablonu yükleniyor...
        </div>
      )}

      <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4">
        <h3 className="font-semibold text-gray-900">İlan Çekirdek Alanları</h3>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Başlık *</label>
          <input
            type="text"
            className="w-full p-2 border rounded-md font-semibold"
            value={coreFields.title}
            onChange={(e) => setCoreFields((prev) => ({ ...prev, title: e.target.value }))}
            placeholder="İlan başlığı"
            data-testid="listing-title-input"
          />
          {errors.title && <div className="text-xs text-red-600 mt-1" data-testid="listing-title-error">{errors.title}</div>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Açıklama *</label>
          <textarea
            rows={descriptionConfig.ui?.min_rows || 6}
            className="w-full p-2 border rounded-md"
            value={coreFields.description}
            onChange={(e) => setCoreFields((prev) => ({ ...prev, description: e.target.value }))}
            onInput={(e) => {
              if (descriptionConfig.ui?.auto_grow) {
                e.target.style.height = 'auto';
                e.target.style.height = `${e.target.scrollHeight}px`;
              }
            }}
            placeholder="Açıklama"
            data-testid="listing-description-textarea"
          />
          <div className="flex items-center justify-between text-xs text-gray-500 mt-1">
            <span data-testid="listing-description-counter">{descriptionCount}</span>
            <span>min: {descriptionConfig.min || 0} / max: {descriptionConfig.max || 0}</span>
          </div>
          {errors.description && <div className="text-xs text-red-600 mt-1" data-testid="listing-description-error">{errors.description}</div>}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fiyat ({coreFields.currency_primary}) *</label>
            <input
              type="text"
              className="w-full p-2 border rounded-md"
              value={coreFields.price_display}
              onChange={(e) => handlePriceChange(e.target.value)}
              placeholder="15.000"
              data-testid="listing-price-input"
            />
            {errors.price_amount && <div className="text-xs text-red-600 mt-1" data-testid="listing-price-error">{errors.price_amount}</div>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Birincil Para Birimi</label>
            <select
              className="w-full p-2 border rounded-md"
              value={coreFields.currency_primary}
              onChange={(e) => setCoreFields((prev) => ({ ...prev, currency_primary: e.target.value }))}
              data-testid="listing-primary-currency"
            >
              <option value="EUR">EUR</option>
              <option value="CHF">CHF</option>
            </select>
          </div>
        </div>

        {coreFields.secondary_enabled && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">İkincil Fiyat ({coreFields.currency_secondary})</label>
              <input
                type="text"
                className="w-full p-2 border rounded-md"
                value={coreFields.secondary_display}
                onChange={(e) => handleSecondaryPriceChange(e.target.value)}
                placeholder="16.500"
                data-testid="listing-secondary-price-input"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">İkincil Para Birimi</label>
              <select
                className="w-full p-2 border rounded-md"
                value={coreFields.currency_secondary}
                onChange={(e) => setCoreFields((prev) => ({ ...prev, currency_secondary: e.target.value }))}
                data-testid="listing-secondary-currency"
              >
                <option value="EUR">EUR</option>
                <option value="CHF">CHF</option>
              </select>
            </div>
          </div>
        )}
      </div>

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

      {schema?.dynamic_fields?.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4">
          <h3 className="font-semibold text-gray-900">Kategori Parametre Alanları</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {schema.dynamic_fields.map((field, index) => (
              <div key={field.id || field.key}>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {field.label || field.key} {field.required ? '*' : ''}
                </label>
                {field.type === 'radio' && (
                  <div className="flex flex-wrap gap-3" data-testid={`listing-dynamic-radio-${index}`}>
                    {field.options?.map((opt) => (
                      <label key={opt} className="flex items-center gap-2 text-sm">
                        <input
                          type="radio"
                          name={`dynamic-${field.key}`}
                          checked={dynamicValues[field.key] === opt}
                          onChange={() => handleDynamicValueChange(field.key, opt)}
                          data-testid={`listing-dynamic-radio-${field.key}-${opt}`}
                        />
                        {opt}
                      </label>
                    ))}
                  </div>
                )}
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
                <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
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

      {schema?.modules?.address?.enabled && (
        <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4">
          <h3 className="font-semibold text-gray-900">Adres Bilgileri</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <input
              type="text"
              className="w-full p-2 border rounded-md"
              placeholder="Sokak"
              value={moduleData.address.street}
              onChange={(e) => setModuleData((prev) => ({ ...prev, address: { ...prev.address, street: e.target.value } }))}
              data-testid="listing-address-street"
            />
            <input
              type="text"
              className="w-full p-2 border rounded-md"
              placeholder="Şehir"
              value={moduleData.address.city}
              onChange={(e) => setModuleData((prev) => ({ ...prev, address: { ...prev.address, city: e.target.value } }))}
              data-testid="listing-address-city"
            />
            <input
              type="text"
              className="w-full p-2 border rounded-md"
              placeholder="Posta Kodu"
              value={moduleData.address.postal_code}
              onChange={(e) => setModuleData((prev) => ({ ...prev, address: { ...prev.address, postal_code: e.target.value } }))}
              data-testid="listing-address-postal"
            />
          </div>
        </div>
      )}

      {schema?.modules?.contact?.enabled && (
        <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4">
          <h3 className="font-semibold text-gray-900">İletişim Tercihleri</h3>
          <input
            type="text"
            className="w-full p-2 border rounded-md"
            placeholder="Telefon"
            value={moduleData.contact.phone}
            onChange={(e) => setModuleData((prev) => ({ ...prev, contact: { ...prev.contact, phone: e.target.value } }))}
            data-testid="listing-contact-phone"
          />
          <div className="flex gap-6 text-sm">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={moduleData.contact.allow_phone}
                onChange={(e) => setModuleData((prev) => ({ ...prev, contact: { ...prev.contact, allow_phone: e.target.checked } }))}
                data-testid="listing-contact-allow-phone"
              />
              Telefonla iletişim
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={moduleData.contact.allow_message}
                onChange={(e) => setModuleData((prev) => ({ ...prev, contact: { ...prev.contact, allow_message: e.target.checked } }))}
                data-testid="listing-contact-allow-message"
              />
              Mesaj ile iletişim
            </label>
          </div>
        </div>
      )}

      {schema?.modules?.payment?.enabled && (
        <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4">
          <h3 className="font-semibold text-gray-900">Ödeme Seçenekleri</h3>
          <div className="flex gap-6 text-sm">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={moduleData.payment.package_selected}
                onChange={(e) => setModuleData((prev) => ({ ...prev, payment: { ...prev.payment, package_selected: e.target.checked } }))}
                data-testid="listing-payment-package"
              />
              Paket
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={moduleData.payment.doping_selected}
                onChange={(e) => setModuleData((prev) => ({ ...prev, payment: { ...prev.payment, doping_selected: e.target.checked } }))}
                data-testid="listing-payment-doping"
              />
              Doping
            </label>
          </div>
        </div>
      )}

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

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 font-medium"
          data-testid="listing-attributes-submit"
        >
          Sonraki: Fotoğraflar
        </button>
      </div>
    </form>
  );
};

export default AttributeForm;
