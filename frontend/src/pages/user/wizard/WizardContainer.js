import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { WizardProvider, useWizard } from './WizardContext';
import Step1Category from './Step1Category';
import Step2Brand from './Step2Brand';
import Step3Model from './Step3Model';
import Step4YearTrim from './Step4YearTrim';
import Step5CoreFields from './Step5CoreFields';
import Step6FeaturesMedia from './Step6FeaturesMedia';
import Step7Review from './Step4Review';

const WizardContent = () => {
  const { step, loading, editLoading } = useWizard();

  const moduleKey = useMemo(() => localStorage.getItem('ilan_ver_module') || 'vehicle', []);
  const isVehicleModule = moduleKey === 'vehicle';

  const steps = useMemo(() => {
    if (isVehicleModule) {
      return [
        { step: 1, label: 'Kategori/Segment', display: 1 },
        { step: 2, label: 'Marka', display: 2 },
        { step: 3, label: 'Model', display: 3 },
        { step: 4, label: 'Yıl/Versiyon', display: 4 },
        { step: 5, label: 'Çekirdek Alanlar', display: 5 },
        { step: 6, label: 'Özellikler + Medya', display: 6 },
        { step: 7, label: 'Önizleme', display: 7 },
      ];
    }
    return [
      { step: 1, label: 'Kategori/Segment', display: 1 },
      { step: 5, label: 'Çekirdek Alanlar', display: 2 },
      { step: 6, label: 'Özellikler + Medya', display: 3 },
      { step: 7, label: 'Önizleme', display: 4 },
    ];
  }, [isVehicleModule]);

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <div className="bg-white rounded-xl shadow-sm border p-6 mb-6" data-testid="wizard-progress">
        <div className="flex items-center justify-between">
          {steps.map((s, index) => (
            <div key={s.step} className="flex items-center" data-testid={`wizard-step-${s.step}`}>
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold ${
                  step >= s.step ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-600'
                }`}
              >
                {s.step}
              </div>
              <span className={`ml-2 text-sm ${step >= s.step ? 'text-gray-900' : 'text-gray-500'}`}>
                {s.label}
              </span>
              {index < steps.length - 1 && (
                <div className={`w-12 h-0.5 mx-4 ${step > s.step ? 'bg-blue-600' : 'bg-gray-200'}`} />
              )}
            </div>
          ))}
        </div>
      </div>

      {(loading || editLoading) && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6" data-testid="wizard-loading">
          İşlem yapılıyor, lütfen bekleyin...
        </div>
      )}

      {step === 1 && <Step1Category />}
      {step === 2 && <Step2Brand />}
      {step === 3 && <Step3Model />}
      {step === 4 && <Step4YearTrim />}
      {step === 5 && <Step5CoreFields />}
      {step === 6 && <Step6FeaturesMedia />}
      {step === 7 && <Step7Review />}
    </div>
  );
};

const WizardContainer = () => {
  const [searchParams] = useSearchParams();
  const editListingId = searchParams.get('edit');

  return (
    <WizardProvider editListingId={editListingId}>
      <WizardContent />
    </WizardProvider>
  );
};

export default WizardContainer;
