import React from 'react';
import { useWizard } from './WizardContext';

const CategorySelector = () => {
  const { createDraft, loading } = useWizard();

  // Vehicle segments (LOCKED) - Elektrikli segment değildir (fuel_type attribute)
  const categories = [
    { id: 'otomobil', name: 'Otomobil', icon: '🚗' },
    { id: 'arazi-suv-pickup', name: 'Arazi / SUV / Pickup', icon: '🚙' },
    { id: 'motosiklet', name: 'Motosiklet', icon: '🏍️' },
    { id: 'minivan-panelvan', name: 'Minivan / Panelvan', icon: '🚐' },
    { id: 'ticari-arac', name: 'Ticari Araç', icon: '🚚' },
    { id: 'karavan-camper', name: 'Karavan / Camper', icon: '🏕️' },
  ];

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Segment Seç</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {categories.map((cat) => (
          <button
            key={cat.id}
            disabled={loading}
            onClick={() => createDraft(cat)}
            data-testid={`segment-${cat.id}`}
            className="p-6 border rounded-xl hover:border-blue-600 hover:bg-blue-50 transition flex flex-col items-center gap-2 text-center"
          >
            <span className="text-4xl">{cat.icon}</span>
            <span className="font-medium text-lg">{cat.name}</span>
          </button>
        ))}
      </div>
    </div>
  );
};

export default CategorySelector;
