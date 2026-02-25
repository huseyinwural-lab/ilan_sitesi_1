import React, { useMemo } from 'react';
import { useWizard } from './WizardContext';

const ReviewSubmit = () => {
  const {
    category,
    basicInfo,
    coreFields,
    moduleData,
    media,
    publishListing,
    saveDraft,
    setStep,
    loading,
    validationErrors,
    dynamicValues,
    detailGroups,
    schema,
  } = useWizard();

  const handleDraftSave = async () => {
    await saveDraft({
      core_fields: {
        title: coreFields.title,
        description: coreFields.description,
        price: {
          price_type: coreFields.price_type || 'FIXED',
          amount: coreFields.price_type === 'FIXED' && coreFields.price_amount ? Number(coreFields.price_amount) : null,
          hourly_rate: coreFields.price_type === 'HOURLY' && coreFields.hourly_rate ? Number(coreFields.hourly_rate) : null,
          currency_primary: coreFields.currency_primary,
          currency_secondary: coreFields.secondary_enabled && coreFields.price_type === 'FIXED' ? coreFields.currency_secondary : null,
          secondary_amount: coreFields.secondary_enabled && coreFields.price_type === 'FIXED' && coreFields.secondary_amount ? Number(coreFields.secondary_amount) : null,
          decimal_places: coreFields.decimal_places,
        },
      },
      attributes: {
        mileage_km: basicInfo.mileage_km,
        fuel_type: basicInfo.fuel_type,
        transmission: basicInfo.transmission,
        drive_type: basicInfo.drive_type,
        body_type: basicInfo.body_type,
        color: basicInfo.color,
        damage_status: basicInfo.damage_status,
        engine_cc: basicInfo.engine_cc,
        engine_hp: basicInfo.engine_hp,
        trade_in: basicInfo.trade_in,
      },
      modules: moduleData,
    });
  };

  const priceLabel = coreFields.price_type === 'HOURLY'
    ? `${coreFields.hourly_display || coreFields.hourly_rate || '-'} ${coreFields.currency_primary} / saat`
    : `${coreFields.price_display || coreFields.price_amount || '-'} ${coreFields.currency_primary}`;

  const coverMedia = media.find((item) => item.is_cover) || media[0];
  const makeLabel = basicInfo.make_label || basicInfo.make_key || '-';
  const modelLabel = basicInfo.model_label || basicInfo.model_key || '-';
  const trimLabel = basicInfo.manual_trim_flag
    ? `Manuel: ${basicInfo.manual_trim_text || '-'}`
    : (basicInfo.vehicle_trim_label || basicInfo.trim_key || '-');
  const priceTypeLabel = coreFields.price_type === 'HOURLY' ? 'Saatlik Ücret' : 'Fiyat';

  const dynamicSummary = useMemo(() => {
    const fields = schema?.dynamic_fields || [];
    return fields
      .map((field) => {
        const value = dynamicValues?.[field.key];
        if (value === undefined || value === null || value === '') return null;
        return { key: field.key, label: field.label || field.key, value };
      })
      .filter(Boolean);
  }, [schema, dynamicValues]);

  const detailSummary = useMemo(() => {
    const groups = schema?.detail_groups || [];
    return groups
      .map((group) => {
        const selections = detailGroups?.[group.id] || [];
        if (!selections.length) return null;
        return {
          id: group.id,
          title: group.title || group.id,
          selections,
        };
      })
      .filter(Boolean);
  }, [schema, detailGroups]);

  return (
    <div className="max-w-2xl mx-auto space-y-8" data-testid="wizard-review">
      <h2 className="text-2xl font-bold" data-testid="wizard-review-title">Önizleme & Yayınla</h2>

      {Array.isArray(validationErrors) && validationErrors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4" data-testid="wizard-submit-errors">
          <div className="text-red-800 font-medium mb-2">Yayınlama hataları</div>
          <ul className="text-red-700 text-sm space-y-1">
            {validationErrors.map((e, idx) => (
              <li key={idx}>• <code>{e.field}</code> ({e.code}): {e.message}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="bg-white border rounded-xl overflow-hidden shadow-sm" data-testid="wizard-review-card">
        <div className="h-48 bg-gray-200 w-full relative" data-testid="wizard-review-cover">
          {coverMedia ? (
            <img src={coverMedia.url} alt="cover" className="w-full h-full object-cover" data-testid="wizard-review-cover-image" />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400" data-testid="wizard-review-no-image">No Image</div>
          )}
          <span className="absolute bottom-4 left-4 bg-white px-3 py-1 rounded-full text-sm font-bold shadow" data-testid="wizard-review-price">
            {priceLabel}
          </span>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <h3 className="text-xl font-bold text-gray-900" data-testid="wizard-review-title-line">
              {coreFields.title || `${makeLabel} ${modelLabel} ${basicInfo.year || ''}`.trim()}
            </h3>
            <p className="text-gray-500 text-sm" data-testid="wizard-review-category">Segment: {category?.name || '-'}</p>
            <p className="text-sm text-gray-600 mt-1" data-testid="wizard-review-brand-line">
              {makeLabel} / {modelLabel} / {basicInfo.year || '-'} / {trimLabel}
            </p>
          </div>

          <div className="text-sm text-gray-600" data-testid="wizard-review-description">
            {coreFields.description || 'Açıklama girilmedi'}
          </div>

          <div className="grid grid-cols-2 gap-4 py-4 border-t border-b" data-testid="wizard-review-specs">
            {[
              ['KM', basicInfo.mileage_km],
              ['Yakıt', basicInfo.fuel_type],
              ['Vites', basicInfo.transmission],
              ['Çekiş', basicInfo.drive_type],
              ['Kasa', basicInfo.body_type],
              ['Motor Hacmi', basicInfo.engine_cc ? `${basicInfo.engine_cc} cc` : '-'],
              ['Motor Gücü', basicInfo.engine_hp ? `${basicInfo.engine_hp} hp` : '-'],
              ['Renk', basicInfo.color],
              ['Hasar', basicInfo.damage_status],
              ['Takas', basicInfo.trade_in === true ? 'Var' : basicInfo.trade_in === false ? 'Yok' : '-'],
              ['Fiyat Tipi', priceTypeLabel],
            ].map(([key, val]) => {
              const testId = String(key).toLowerCase().replace(/[^a-z0-9]+/g, '-');
              return (
                <div key={key} data-testid={`wizard-review-spec-${testId}`}>
                  <span className="text-gray-500 text-sm">{key}:</span>
                  <span className="ml-2 font-medium">{val?.toString() || '-'}</span>
                </div>
              );
            })}
          </div>

          <div className="space-y-2" data-testid="wizard-review-gallery">
            <div className="text-sm font-semibold text-gray-700">Galeri</div>
            {media.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {media.map((item, idx) => (
                  <img
                    key={item.media_id || item.url || idx}
                    src={item.url}
                    alt="gallery"
                    className="h-16 w-24 rounded-md object-cover"
                    data-testid={`wizard-review-gallery-image-${idx}`}
                  />
                ))}
              </div>
            ) : (
              <div className="text-sm text-gray-500" data-testid="wizard-review-gallery-empty">Fotoğraf yok.</div>
            )}
          </div>

          <div className="text-sm text-gray-600" data-testid="wizard-review-location">
            Konum: {moduleData.address?.city || '-'} {moduleData.address?.street || ''}
          </div>

          <div className="space-y-3" data-testid="wizard-review-features">
            <div className="text-sm font-semibold text-gray-700">Seçilen Özellikler</div>
            {(dynamicSummary.length === 0 && detailSummary.length === 0) && (
              <div className="text-sm text-gray-500" data-testid="wizard-review-features-empty">Ek özellik seçilmedi.</div>
            )}
            {dynamicSummary.length > 0 && (
              <div className="space-y-1" data-testid="wizard-review-dynamic-list">
                {dynamicSummary.map((item) => {
                  const safeKey = String(item.key).toLowerCase().replace(/[^a-z0-9]+/g, '-');
                  return (
                    <div key={item.key} className="text-sm" data-testid={`wizard-review-dynamic-${safeKey}`}>
                      <span className="text-gray-500">{item.label}:</span>
                      <span className="ml-2 font-medium">{item.value}</span>
                    </div>
                  );
                })}
              </div>
            )}
            {detailSummary.length > 0 && (
              <div className="space-y-2" data-testid="wizard-review-detail-list">
                {detailSummary.map((group) => {
                  const safeGroup = String(group.id).toLowerCase().replace(/[^a-z0-9]+/g, '-');
                  return (
                    <div key={group.id} data-testid={`wizard-review-detail-${safeGroup}`}>
                      <div className="text-xs uppercase text-gray-400">{group.title}</div>
                      <div className="text-sm text-gray-700">
                        {(group.selections || []).join(', ')}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="bg-yellow-50 p-4 rounded-lg text-sm text-yellow-800" data-testid="wizard-review-note">
            <strong>Not:</strong> Yayınla’ya bastığınızda ilanınız moderasyona gönderilir.
          </div>
        </div>
      </div>

      <div className="flex flex-wrap justify-end gap-4" data-testid="wizard-review-actions">
        <button
          type="button"
          onClick={() => setStep(5)}
          className="px-6 py-3 text-gray-600 hover:bg-gray-100 rounded-lg"
          data-testid="wizard-review-edit"
        >
          Düzenle
        </button>
        <button
          type="button"
          onClick={handleDraftSave}
          className="px-6 py-3 border rounded-lg"
          data-testid="wizard-review-draft"
        >
          Taslak Kaydet
        </button>
        <button
          onClick={publishListing}
          disabled={loading}
          className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 font-medium disabled:opacity-50"
          data-testid="wizard-publish"
        >
          {loading ? 'Yayınlanıyor...' : 'Yayınla'}
        </button>
      </div>
    </div>
  );
};

export default ReviewSubmit;
