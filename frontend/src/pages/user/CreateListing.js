import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const CreateListing = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    module: 'vehicle',
    category: '',
    title: '',
    price: '',
  });

  const handleNext = () => {
    // In real app: Save draft to backend here
    setStep(step + 1);
  };

  const handlePublish = () => {
    // In real app: API call to /publish
    alert("Listing Published!");
    navigate('/account/listings');
  };

  return (
    <div className="max-w-2xl mx-auto bg-white p-8 rounded-lg shadow">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex justify-between mb-2">
          <span className={`text-sm ${step >= 1 ? 'text-blue-600 font-bold' : 'text-gray-400'}`}>1. Category</span>
          <span className={`text-sm ${step >= 2 ? 'text-blue-600 font-bold' : 'text-gray-400'}`}>2. Details</span>
          <span className={`text-sm ${step >= 3 ? 'text-blue-600 font-bold' : 'text-gray-400'}`}>3. Photos</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full">
          <div className="h-2 bg-blue-600 rounded-full transition-all duration-300" style={{ width: `${(step / 3) * 100}%` }}></div>
        </div>
      </div>

      {/* Step 1: Category */}
      {step === 1 && (
        <div>
          <h2 className="text-xl font-bold mb-4">What are you selling?</h2>
          <div className="grid grid-cols-2 gap-4">
            {['Vehicle', 'Real Estate', 'Electronics', 'Services'].map((cat) => (
              <button
                key={cat}
                onClick={() => setFormData({ ...formData, module: cat.toLowerCase() })}
                className={`p-4 border rounded-lg hover:border-blue-500 text-left ${formData.module === cat.toLowerCase() ? 'border-blue-500 bg-blue-50' : ''}`}
              >
                <div className="font-bold">{cat}</div>
              </button>
            ))}
          </div>
          <div className="mt-6 flex justify-end">
            <button onClick={handleNext} className="bg-blue-600 text-white px-6 py-2 rounded-lg">Next: Details</button>
          </div>
        </div>
      )}

      {/* Step 2: Details */}
      {step === 2 && (
        <div>
          <h2 className="text-xl font-bold mb-4">Listing Details</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Title</label>
              <input 
                type="text" 
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2 border"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Price (€)</label>
              <input 
                type="number" 
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm p-2 border"
                value={formData.price}
                onChange={(e) => setFormData({...formData, price: e.target.value})}
              />
            </div>
          </div>
          <div className="mt-6 flex justify-between">
            <button onClick={() => setStep(1)} className="text-gray-600">Back</button>
            <button onClick={handleNext} className="bg-blue-600 text-white px-6 py-2 rounded-lg">Next: Photos</button>
          </div>
        </div>
      )}

      {/* Step 3: Photos & Publish */}
      {step === 3 && (
        <div>
          <h2 className="text-xl font-bold mb-4">Upload Photos</h2>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-12 text-center text-gray-500">
            <p>Drag and drop photos here</p>
            <p className="text-xs mt-2">(Simulated for V1)</p>
          </div>
          <div className="mt-6 flex justify-between">
            <button onClick={() => setStep(2)} className="text-gray-600">Back</button>
            <button onClick={handlePublish} className="bg-green-600 text-white px-6 py-2 rounded-lg font-bold">Publish Listing</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CreateListing;
