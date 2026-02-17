import React from 'react';

const FilterPanel = ({ filters, onChange, onApply }) => {
  const handleChange = (key, value) => {
    onChange({ ...filters, [key]: value });
  };

  return (
    <div className="bg-white p-4 rounded-lg border space-y-6">
      <h3 className="font-bold text-gray-700 border-b pb-2">Filters</h3>

      {/* Price */}
      <div>
        <label className="text-sm font-medium text-gray-600 block mb-2">Price Range</label>
        <div className="flex gap-2">
          <input 
            type="number" 
            placeholder="Min" 
            className="w-full p-2 border rounded text-sm"
            value={filters.price_min || ''}
            onChange={(e) => handleChange('price_min', e.target.value)}
          />
          <input 
            type="number" 
            placeholder="Max" 
            className="w-full p-2 border rounded text-sm"
            value={filters.price_max || ''}
            onChange={(e) => handleChange('price_max', e.target.value)}
          />
        </div>
      </div>

      {/* City */}
      <div>
        <label className="text-sm font-medium text-gray-600 block mb-2">City</label>
        <input 
          type="text" 
          placeholder="e.g. Berlin" 
          className="w-full p-2 border rounded text-sm"
          value={filters.city || ''}
          onChange={(e) => handleChange('city', e.target.value)}
        />
      </div>

      <button 
        onClick={onApply}
        className="w-full bg-blue-600 text-white py-2 rounded-lg font-medium hover:bg-blue-700"
      >
        Apply Filters
      </button>
    </div>
  );
};

export default FilterPanel;
