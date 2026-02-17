import React from 'react';
import { WizardProvider, useWizard } from './WizardContext';
import Step1Category from './Step1Category';
import Step2Attributes from './Step2Attributes';
import Step3Media from './Step3Media';
import Step4Review from './Step4Review';

const WizardSteps = () => {
  const { step, setStep } = useWizard();

  const renderStep = () => {
    switch (step) {
      case 1: return <Step1Category />; // Segment
      case 2: return <Step2Attributes />; // Make/Model/Year + Basic
      case 3: return <Step3Media />; // Photos
      case 4: return <Step4Review />; // Preview + Publish
      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-20">
      {/* Header */}
      <div className="bg-white border-b sticky top-0 z-10">
        <div className="max-w-3xl mx-auto px-4 h-16 flex items-center justify-between">
          <h1 className="font-bold text-lg">Vasıta İlanı Oluştur</h1>
          <div className="text-sm text-gray-500">Adım {step} / 4</div>
        </div>
        {/* Progress Bar */}
        <div className="h-1 bg-gray-100">
          <div 
            className="h-full bg-blue-600 transition-all duration-500" 
            style={{ width: `${(step / 4) * 100}%` }}
          />
        </div>
      </div>

      {/* Content */}
      <div className="max-w-3xl mx-auto p-4 md:p-8">
        {renderStep()}
      </div>
    </div>
  );
};

const WizardContainer = () => {
  return (
    <WizardProvider>
      <WizardSteps />
    </WizardProvider>
  );
};

export default WizardContainer;
