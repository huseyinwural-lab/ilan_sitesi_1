import React, { useMemo, useRef, useState } from 'react';
import { toast } from '@/components/ui/use-toast';
import { useWizard } from './WizardContext';

const formatNumberInput = (value, decimals) => {
  const numericValue = value.replace(/[^\d.,]/g, '').replace(',', '.');
  if (numericValue === '') return { display: '', numeric: '' };
  const parsed = parseFloat(numericValue);
  if (Number.isNaN(parsed)) return { display: '', numeric: '' };
  const fixed = parsed.toFixed(decimals);
  return {
    display: new Intl.NumberFormat('de-DE', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    }).format(fixed),
    numeric: fixed,
  };
};

const CoreFieldsStep = () => {
  const {
    basicInfo,
    setBasicInfo,
    coreFields,
    setCoreFields,
    moduleData,
    setModuleData,
    attributes,
    setAttributes,
    schema,
    saveDraft,
    trackWizardEvent,
    setAutosaveStatus,
    setStep,
    completedSteps,
    setCompletedSteps,
    loading,
  } = useWizard();

  const moduleKey = useMemo(() => localStorage.getItem('ilan_ver_module') || 'vehicle', []);
  const isVehicleModule = moduleKey === 'vehicle';

  const priceConfig = schema?.core_fields?.price || {};
  const titleConfig = schema?.core_fields?.title || {};
  const descriptionConfig = schema?.core_fields?.description || {};
  const priceType = (coreFields.price_type || 'FIXED').toUpperCase();
  const allowedPriceTypes = priceConfig.allowed_types || (priceConfig.hourly_enabled === false ? ['FIXED'] : ['FIXED', 'HOURLY']);

  const [title, setTitle] = useState(coreFields.title || '');
  const [description, setDescription] = useState(coreFields.description || '');
  const [mileageKm, setMileageKm] = useState(basicInfo.mileage_km || '');
  const [fuelType, setFuelType] = useState(basicInfo.fuel_type || '');
  const [transmission, setTransmission] = useState(basicInfo.transmission || '');
  const [driveType, setDriveType] = useState(basicInfo.drive_type || '');
  const [bodyType, setBodyType] = useState(basicInfo.body_type || '');
  const [color, setColor] = useState(basicInfo.color || '');
  const [damageStatus, setDamageStatus] = useState(basicInfo.damage_status || '');
  const [engineCc, setEngineCc] = useState(basicInfo.engine_cc || '');
  const [engineHp, setEngineHp] = useState(basicInfo.engine_hp || '');
  const [tradeIn, setTradeIn] = useState(
    basicInfo.trade_in === true ? 'true' : basicInfo.trade_in === false ? 'false' : ''
  );
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const saveLockRef = useRef(false);

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

  const validate = () => {
    const nextErrors = {};

    if (titleConfig.required && !title.trim()) {
      nextErrors.title = 'Başlık zorunlu.';
    }
    if (descriptionConfig.required && !description.trim()) {
      nextErrors.description = 'Açıklama zorunlu.';
    }

    if (priceType === 'FIXED') {
      if (priceConfig.required && !coreFields.price_amount) {
        nextErrors.price_amount = 'Fiyat giriniz.';
      }
    } else {
      if (priceConfig.required && !coreFields.hourly_rate) {
        nextErrors.hourly_rate = 'Saatlik ücret giriniz.';
      }
    }

    if (isVehicleModule) {
      if (!mileageKm) nextErrors.mileage_km = 'Km zorunlu.';
      if (!fuelType) nextErrors.fuel_type = 'Yakıt seçiniz.';
      if (!transmission) nextErrors.transmission = 'Vites seçiniz.';
      if (!driveType) nextErrors.drive_type = 'Çekiş seçiniz.';
      if (!bodyType) nextErrors.body_type = 'Kasa tipi seçiniz.';
      if (!color) nextErrors.color = 'Renk seçiniz.';
      if (!damageStatus) nextErrors.damage_status = 'Hasar bilgisi seçiniz.';
      if (!engineCc) nextErrors.engine_cc = 'Motor hacmi giriniz.';
      if (!engineHp) nextErrors.engine_hp = 'Motor gücü giriniz.';
      if (tradeIn === '') nextErrors.trade_in = 'Takas seçiniz.';
    }
    if (!moduleData.address?.city) nextErrors.address_city = 'Şehir bilgisi zorunlu.';

    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const scrollToFirstError = () => {
    setTimeout(() => {
      const container = document.querySelector('[data-testid="wizard-core-step"]');
      const target = container?.querySelector('[data-testid$="-error"]');
      if (target) {
        target.scrollIntoView({ behavior: window.innerWidth < 768 ? 'smooth' : 'auto', block: 'center' });
      }
    }, 0);
  };

  const handleComplete = async () => {
    if (saving || saveLockRef.current) return false;
    saveLockRef.current = true;
    if (!validate()) {
      scrollToFirstError();
      saveLockRef.current = false;
      return false;
    }
    setSaving(true);

    const vehicleAttributes = isVehicleModule
      ? {
        mileage_km: mileageKm,
        fuel_type: fuelType,
        transmission,
        drive_type: driveType,
        body_type: bodyType,
        color,
        damage_status: damageStatus,
        engine_cc: engineCc,
        engine_hp: engineHp,
        trade_in: tradeIn === 'true',
      }
      : {};

    const nextAttributes = {
      ...attributes,
      ...vehicleAttributes,
    };

    const ok = await saveDraft({
      core_fields: {
        title: title.trim(),
        description: description.trim(),
        price: {
          price_type: priceType,
          amount: priceType === 'FIXED' && coreFields.price_amount ? Number(coreFields.price_amount) : null,
          hourly_rate: priceType === 'HOURLY' && coreFields.hourly_rate ? Number(coreFields.hourly_rate) : null,
          currency_primary: coreFields.currency_primary,
          currency_secondary: coreFields.secondary_enabled && priceType === 'FIXED' ? coreFields.currency_secondary : null,
          secondary_amount: coreFields.secondary_enabled && priceType === 'FIXED' && coreFields.secondary_amount ? Number(coreFields.secondary_amount) : null,
          decimal_places: coreFields.decimal_places,
        },
      },
      attributes: nextAttributes,
      modules: moduleData,
    });

    if (!ok) {
      setErrors((prev) => ({ ...prev, submit: 'Kaydetme başarısız.' }));
      scrollToFirstError();
      setSaving(false);
      saveLockRef.current = false;
      return false;
    }

    setCoreFields((prev) => ({
      ...prev,
      title: title.trim(),
      description: description.trim(),
      price_type: priceType,
    }));

    setBasicInfo((prev) => ({
      ...prev,
      ...(isVehicleModule
        ? {
          mileage_km: mileageKm,
          fuel_type: fuelType,
          transmission,
          drive_type: driveType,
          body_type: bodyType,
          color,
          damage_status: damageStatus,
          engine_cc: engineCc,
          engine_hp: engineHp,
          trade_in: tradeIn === 'true',
        }
        : {}),
    }));
    setAttributes(nextAttributes);

    setCompletedSteps((prev) => ({
      ...prev,
      5: true,
      6: false,
    }));
    setSaving(false);
    saveLockRef.current = false;
    return true;
  };

  const handleNext = async () => {
    if (!validate()) {
      scrollToFirstError();
      await trackWizardEvent('wizard_step_autosave_error', {
        step_id: 'core',
        category_id: basicInfo.category_id,
        module: basicInfo.module || 'vehicle',
        country: basicInfo.country || (localStorage.getItem('selected_country') || 'DE'),
        reason: 'validation_failed',
      });
      setAutosaveStatus((prev) => ({
        ...prev,
        status: 'error',
        lastErrorAt: new Date().toISOString(),
      }));
      return;
    }
    if (!completedSteps[5]) {
      const ok = await handleComplete();
      if (!ok) {
        await trackWizardEvent('wizard_step_autosave_error', {
          step_id: 'core',
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
    }
    await trackWizardEvent('wizard_step_autosave_success', {
      step_id: 'core',
      category_id: basicInfo.category_id,
      module: basicInfo.module || 'vehicle',
      country: basicInfo.country || (localStorage.getItem('selected_country') || 'DE'),
    });
    setAutosaveStatus((prev) => ({
      ...prev,
      status: 'success',
      lastSuccessAt: new Date().toISOString(),
    }));
    toast({
      title: 'Kaydedildi',
      duration: 2500,
      dismissible: false,
      'data-testid': 'wizard-autosave-toast',
    });
    setStep(6);
  };

  const nextDisabled = saving;

  return (
    <form className="space-y-8" data-testid="wizard-core-step" onSubmit={(e) => e.preventDefault()}>
      <div className="bg-white p-6 rounded-xl shadow-sm border space-y-4" data-testid="core-main-section">
        <h3 className="text-lg font-semibold">Fiyat ve Başlık</h3>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Başlık *</label>
          <input
            type="text"
            className="w-full p-2 border rounded-md"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="İlan başlığı"
            data-testid="core-title-input"
          />
          {errors.title && <div className="text-xs text-red-600 mt-1" data-testid="core-title-error">{errors.title}</div>}
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Açıklama *</label>
          <textarea
            className="w-full p-2 border rounded-md h-28"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Açıklama"
            data-testid="core-description-input"
          />
          {errors.description && <div className="text-xs text-red-600 mt-1" data-testid="core-description-error">{errors.description}</div>}
        </div>

        <div className="space-y-2" data-testid="core-price-type-section">
          <label className="block text-sm font-medium text-gray-700">Fiyat Tipi</label>
          <div className="inline-flex rounded-lg border bg-gray-100 p-1" data-testid="core-price-type-toggle">
            {allowedPriceTypes.includes('FIXED') && (
              <button
                type="button"
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${priceType === 'FIXED' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'}`}
                onClick={() => handlePriceTypeChange('FIXED')}
                data-testid="core-price-type-fixed"
              >
                Fiyat
              </button>
            )}
            {allowedPriceTypes.includes('HOURLY') && (
              <button
                type="button"
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${priceType === 'HOURLY' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500'}`}
                onClick={() => handlePriceTypeChange('HOURLY')}
                data-testid="core-price-type-hourly"
              >
                Saatlik Ücret
              </button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {priceType === 'FIXED' ? 'Fiyat' : 'Saatlik Ücret'} ({coreFields.currency_primary}) *
            </label>
            <input
              type="text"
              className="w-full p-2 border rounded-md"
              value={priceType === 'FIXED' ? coreFields.price_display : coreFields.hourly_display}
              onChange={(e) =>
                priceType === 'FIXED' ? handlePriceChange(e.target.value) : handleHourlyChange(e.target.value)
              }
              placeholder={priceType === 'FIXED' ? 'Fiyat' : 'Saatlik Ücret'}
              data-testid={priceType === 'FIXED' ? 'core-price-input' : 'core-hourly-input'}
            />
            {priceType === 'FIXED' && errors.price_amount && (
              <div className="text-xs text-red-600 mt-1" data-testid="core-price-error">{errors.price_amount}</div>
            )}
            {priceType === 'HOURLY' && errors.hourly_rate && (
              <div className="text-xs text-red-600 mt-1" data-testid="core-hourly-error">{errors.hourly_rate}</div>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Birincil Para Birimi</label>
            <select
              className="w-full p-2 border rounded-md"
              value={coreFields.currency_primary}
              onChange={(e) => setCoreFields((prev) => ({ ...prev, currency_primary: e.target.value }))}
              data-testid="core-currency-select"
            >
              <option value="EUR">EUR</option>
              <option value="CHF">CHF</option>
            </select>
          </div>
        </div>
      </div>

      {isVehicleModule && (
        <div className="bg-white p-6 rounded-xl shadow-sm border space-y-4" data-testid="core-auto-section">
          <h3 className="text-lg font-semibold">Otomobil Bilgileri</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Km *</label>
            <input
              type="number"
              className="w-full p-2 border rounded-md"
              value={mileageKm}
              onChange={(e) => setMileageKm(e.target.value)}
              data-testid="core-mileage-input"
            />
            {errors.mileage_km && <div className="text-xs text-red-600 mt-1" data-testid="core-mileage-error">{errors.mileage_km}</div>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Yakıt *</label>
            <select
              className="w-full p-2 border rounded-md"
              value={fuelType}
              onChange={(e) => setFuelType(e.target.value)}
              data-testid="core-fuel-select"
            >
              <option value="">Seçiniz</option>
              <option value="petrol">Benzin</option>
              <option value="diesel">Dizel</option>
              <option value="hybrid">Hybrid</option>
              <option value="electric">Elektrik</option>
            </select>
            {errors.fuel_type && <div className="text-xs text-red-600 mt-1" data-testid="core-fuel-error">{errors.fuel_type}</div>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Vites *</label>
            <select
              className="w-full p-2 border rounded-md"
              value={transmission}
              onChange={(e) => setTransmission(e.target.value)}
              data-testid="core-transmission-select"
            >
              <option value="">Seçiniz</option>
              <option value="manual">Manuel</option>
              <option value="automatic">Otomatik</option>
            </select>
            {errors.transmission && <div className="text-xs text-red-600 mt-1" data-testid="core-transmission-error">{errors.transmission}</div>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Çekiş *</label>
            <select
              className="w-full p-2 border rounded-md"
              value={driveType}
              onChange={(e) => setDriveType(e.target.value)}
              data-testid="core-drive-select"
            >
              <option value="">Seçiniz</option>
              <option value="fwd">Ön Çekiş</option>
              <option value="rwd">Arka Çekiş</option>
              <option value="awd">4x4</option>
            </select>
            {errors.drive_type && <div className="text-xs text-red-600 mt-1" data-testid="core-drive-error">{errors.drive_type}</div>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Kasa Tipi *</label>
            <select
              className="w-full p-2 border rounded-md"
              value={bodyType}
              onChange={(e) => setBodyType(e.target.value)}
              data-testid="core-body-select"
            >
              <option value="">Seçiniz</option>
              <option value="sedan">Sedan</option>
              <option value="hatchback">Hatchback</option>
              <option value="suv">SUV</option>
              <option value="coupe">Coupe</option>
              <option value="wagon">Station</option>
            </select>
            {errors.body_type && <div className="text-xs text-red-600 mt-1" data-testid="core-body-error">{errors.body_type}</div>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Motor Hacmi (cc) *</label>
            <input
              type="number"
              className="w-full p-2 border rounded-md"
              value={engineCc}
              onChange={(e) => setEngineCc(e.target.value)}
              data-testid="core-engine-cc-input"
            />
            {errors.engine_cc && <div className="text-xs text-red-600 mt-1" data-testid="core-engine-cc-error">{errors.engine_cc}</div>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Motor Gücü (hp) *</label>
            <input
              type="number"
              className="w-full p-2 border rounded-md"
              value={engineHp}
              onChange={(e) => setEngineHp(e.target.value)}
              data-testid="core-engine-hp-input"
            />
            {errors.engine_hp && <div className="text-xs text-red-600 mt-1" data-testid="core-engine-hp-error">{errors.engine_hp}</div>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Renk *</label>
            <input
              type="text"
              className="w-full p-2 border rounded-md"
              value={color}
              onChange={(e) => setColor(e.target.value)}
              data-testid="core-color-input"
            />
            {errors.color && <div className="text-xs text-red-600 mt-1" data-testid="core-color-error">{errors.color}</div>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Hasar Durumu *</label>
            <select
              className="w-full p-2 border rounded-md"
              value={damageStatus}
              onChange={(e) => setDamageStatus(e.target.value)}
              data-testid="core-damage-select"
            >
              <option value="">Seçiniz</option>
              <option value="none">Hasarsız</option>
              <option value="minor">Hafif Hasarlı</option>
              <option value="major">Ağır Hasarlı</option>
            </select>
            {errors.damage_status && <div className="text-xs text-red-600 mt-1" data-testid="core-damage-error">{errors.damage_status}</div>}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Takas *</label>
            <select
              className="w-full p-2 border rounded-md"
              value={tradeIn}
              onChange={(e) => setTradeIn(e.target.value)}
              data-testid="core-trade-select"
            >
              <option value="">Seçiniz</option>
              <option value="true">Var</option>
              <option value="false">Yok</option>
            </select>
            {errors.trade_in && <div className="text-xs text-red-600 mt-1" data-testid="core-trade-error">{errors.trade_in}</div>}
          </div>
        </div>
      </div>
      )}

      <div className="bg-white p-6 rounded-xl shadow-sm border space-y-4" data-testid="core-location-section">
        <h3 className="text-lg font-semibold">Konum Bilgileri</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <input
            type="text"
            className="w-full p-2 border rounded-md"
            value={moduleData.address?.street || ''}
            onChange={(e) => setModuleData((prev) => ({
              ...prev,
              address: { ...prev.address, street: e.target.value },
            }))}
            placeholder="Sokak"
            data-testid="core-address-street"
          />
          <div>
            <input
              type="text"
              className="w-full p-2 border rounded-md"
              value={moduleData.address?.city || ''}
              onChange={(e) => setModuleData((prev) => ({
                ...prev,
                address: { ...prev.address, city: e.target.value },
              }))}
              placeholder="Şehir"
              data-testid="core-address-city"
            />
            {errors.address_city && (
              <div className="text-xs text-red-600 mt-1" data-testid="core-address-city-error">{errors.address_city}</div>
            )}
          </div>
          <input
            type="text"
            className="w-full p-2 border rounded-md"
            value={moduleData.address?.postal_code || ''}
            onChange={(e) => setModuleData((prev) => ({
              ...prev,
              address: { ...prev.address, postal_code: e.target.value },
            }))}
            placeholder="Posta Kodu"
            data-testid="core-address-postal"
          />
        </div>
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border space-y-4" data-testid="core-contact-section">
        <h3 className="text-lg font-semibold">İletişim Tercihleri</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            type="text"
            className="w-full p-2 border rounded-md"
            value={moduleData.contact?.phone || ''}
            onChange={(e) => setModuleData((prev) => ({
              ...prev,
              contact: { ...prev.contact, phone: e.target.value },
            }))}
            placeholder="Telefon"
            data-testid="core-contact-phone"
          />
          <input
            type="text"
            className="w-full p-2 border rounded-md"
            value={moduleData.contact?.email || ''}
            onChange={(e) => setModuleData((prev) => ({
              ...prev,
              contact: { ...prev.contact, email: e.target.value },
            }))}
            placeholder="Email"
            data-testid="core-contact-email"
          />
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={Boolean(moduleData.contact_option_phone)}
              onChange={(e) => setModuleData((prev) => ({
                ...prev,
                contact_option_phone: e.target.checked,
              }))}
              data-testid="core-contact-phone-option"
            />
            Telefonla iletişim
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={Boolean(moduleData.contact_option_message)}
              onChange={(e) => setModuleData((prev) => ({
                ...prev,
                contact_option_message: e.target.checked,
              }))}
              data-testid="core-contact-message-option"
            />
            Mesaj ile iletişim
          </label>
        </div>
      </div>

      <div className="flex items-center justify-between" data-testid="core-actions">
        <button
          type="button"
          onClick={() => setStep(4)}
          className="px-4 py-2 text-sm text-gray-500"
          data-testid="core-back"
        >
          Geri
        </button>
        <div className="flex items-center gap-3">
          <div title={nextDisabled ? 'Önce bu adımı tamamlayın.' : ''} data-testid="core-next-tooltip">
            <button
              type="button"
              onClick={handleNext}
              disabled={nextDisabled}
              className="px-4 py-2 border rounded-md text-sm disabled:opacity-50"
              data-testid="core-next"
            >
              Next
            </button>
          </div>
          <button
            type="button"
            onClick={handleComplete}
            disabled={loading || saving}
            className="px-5 py-2 bg-blue-600 text-white rounded-md disabled:opacity-60"
            data-testid="core-complete"
          >
            Tamam
          </button>
        </div>
      </div>

      {errors.submit && (
        <div className="text-sm text-red-600" data-testid="core-submit-error">{errors.submit}</div>
      )}
    </form>
  );
};

export default CoreFieldsStep;
