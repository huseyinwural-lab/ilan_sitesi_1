import React, { useState } from 'react';
import { useWizard } from './WizardContext';

const PricingLocation = () => {
  const {
    coreFields,
    setCoreFields,
    schema,
    moduleData,
    setModuleData,
    saveStep,
    saveDraft,
    loading,
  } = useWizard();

  const [errors, setErrors] = useState({});
  const [draftSaved, setDraftSaved] = useState(false);

  const priceConfig = schema?.core_fields?.price || {};
  const titleConfig = schema?.core_fields?.title || {};
  const descriptionConfig = schema?.core_fields?.description || {};
  const priceType = (coreFields.price_type || 'FIXED').toUpperCase();
  const allowedPriceTypes = priceConfig.allowed_types || (priceConfig.hourly_enabled === false ? ['FIXED'] : ['FIXED', 'HOURLY']);

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

  const handleHourlyChange = (value) => {
    const decimals = priceConfig.decimal_places ?? 0;
    const formatted = formatNumberInput(value, decimals);
    setCoreFields((prev) => ({
      ...prev,
      hourly_display: formatted.display,
      hourly_rate: formatted.numeric === '' ? '' : formatted.numeric.toString(),
    }));
  };

  const handlePriceTypeChange = (nextType) => {
    setCoreFields((prev) => ({
      ...prev,
      price_type: nextType,
      price_amount: nextType === 'FIXED' ? prev.price_amount : '',
      price_display: nextType === 'FIXED' ? prev.price_display : '',
      hourly_rate: nextType === 'HOURLY' ? prev.hourly_rate : '',
      hourly_display: nextType === 'HOURLY' ? prev.hourly_display : '',
      secondary_amount: nextType === 'FIXED' ? prev.secondary_amount : '',
      secondary_display: nextType === 'FIXED' ? prev.secondary_display : '',
    }));
    setErrors((prev) => ({ ...prev, price_amount: undefined, hourly_rate: undefined }));
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

  const validate = () => {
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
    }

    if (priceType === 'FIXED') {
      if (priceConfig.required && !coreFields.price_amount) {
        errs.price_amount = 'Fiyat giriniz.';
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
    } else {
      if (priceConfig.required && !coreFields.hourly_rate) {
        errs.hourly_rate = 'Saatlik ücret giriniz.';
      }
      if (coreFields.hourly_rate && Number(coreFields.hourly_rate) <= 0) {
        errs.hourly_rate = 'Saatlik ücret giriniz.';
      }
    }

    return errs;
  };

  const handleSaveDraft = async () => {
    await saveDraft({
      core_fields: {
        title: coreFields.title,
        description: coreFields.description,
        price: {
          amount: coreFields.price_amount ? Number(coreFields.price_amount) : null,
          currency_primary: coreFields.currency_primary,
          currency_secondary: coreFields.secondary_enabled ? coreFields.currency_secondary : null,
          secondary_amount: coreFields.secondary_amount ? Number(coreFields.secondary_amount) : null,
          decimal_places: coreFields.decimal_places,
        },
      },
      modules: moduleData,
    });
    setDraftSaved(true);
    setTimeout(() => setDraftSaved(false), 1500);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const errs = validate();
    setErrors(errs);
    if (Object.keys(errs).length > 0) return;

    await saveStep({
      coreFields,
      moduleData,
    });
  };

  const descriptionCount = coreFields.description?.length || 0;

  return (
    <form onSubmit={handleSubmit} className="space-y-6" data-testid="listing-pricing-form">
      <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4" data-testid="listing-price-section">
        <h3 className="font-semibold text-gray-900" data-testid="listing-price-title">Fiyat ve Başlık</h3>
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

      {schema?.modules?.address?.enabled && (
        <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4" data-testid="listing-location-section">
          <h3 className="font-semibold text-gray-900" data-testid="listing-location-title">Konum Bilgileri</h3>
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
        <div className="bg-white p-6 rounded-lg shadow-sm border space-y-4" data-testid="listing-contact-section">
          <h3 className="font-semibold text-gray-900" data-testid="listing-contact-title">İletişim Tercihleri</h3>
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

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleSaveDraft}
            className="h-10 px-4 rounded-md border text-sm"
            data-testid="listing-pricing-draft"
          >
            Taslak Kaydet
          </button>
          {draftSaved && (
            <span className="text-xs text-emerald-600" data-testid="listing-pricing-draft-saved">Kaydedildi</span>
          )}
        </div>
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 font-medium"
          data-testid="listing-pricing-next"
        >
          Sonraki: Fotoğraflar
        </button>
      </div>
    </form>
  );
};

export default PricingLocation;
