import React from 'react';
import { useWizard } from './WizardContext';

const ReviewSubmit = () => {
  const { category, basicInfo, media, publishListing, loading, validationErrors } = useWizard();

  return (
    <div className="max-w-2xl mx-auto space-y-8" data-testid="wizard-review">
      <h2 className="text-2xl font-bold">Önizleme & Yayınla</h2>

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

      <div className="bg-white border rounded-xl overflow-hidden shadow-sm">
        {/* Header / Cover */}
        <div className="h-48 bg-gray-200 w-full relative">
          {media[0] ? (
            <img src={media[0]} alt="cover" className="w-full h-full object-cover" />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400">No Image</div>
          )}
          <span className="absolute bottom-4 left-4 bg-white px-3 py-1 rounded-full text-sm font-bold shadow">
            €{basicInfo.price_eur || '-'}
          </span>
        </div>

        <div className="p-6 space-y-4">
          <div>
            <h3 className="text-xl font-bold text-gray-900">{basicInfo.make_key || ''} {basicInfo.model_key || ''} {basicInfo.year || ''}</h3>
            <p className="text-gray-500 text-sm">Segment: {category?.name}</p>
          </div>

          <div className="grid grid-cols-2 gap-4 py-4 border-t border-b">
            {[
              ['KM', basicInfo.mileage_km],
              ['Yakıt', basicInfo.fuel_type],
              ['Vites', basicInfo.transmission],
              ['Kondisyon', basicInfo.condition],
            ].map(([key, val]) => (
              <div key={key}>
                <span className="text-gray-500 text-sm">{key}:</span>
                <span className="ml-2 font-medium">{val?.toString() || '-'}</span>
              </div>
            ))}
          </div>

          <div className="bg-yellow-50 p-4 rounded-lg text-sm text-yellow-800">
            <strong>Not:</strong> Yayınla’ya bastığınızda ilanınız yayınlanacaktır (MVP).
          </div>
        </div>
      </div>

      <div className="flex justify-end gap-4">
        <button className="px-6 py-3 text-gray-600 hover:bg-gray-100 rounded-lg" data-testid="wizard-review-edit">Edit</button>
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
