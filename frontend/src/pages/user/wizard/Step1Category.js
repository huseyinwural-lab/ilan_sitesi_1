import React, { useEffect, useMemo, useState } from 'react';
import { useWizard } from './WizardContext';

const CATEGORY_ICONS = {
  otomobil: '🚗',
  'arazi-suv-pickup': '🚙',
  motosiklet: '🏍️',
  'minivan-panelvan': '🚐',
  'ticari-arac': '🚚',
  'karavan-camper': '🏕️',
};

const CategorySelector = () => {
  const { createDraft, loading, setStep, completedSteps, setCompletedSteps } = useWizard();
  const [categories, setCategories] = useState([]);
  const [activeParentId, setActiveParentId] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const country = (localStorage.getItem('selected_country') || 'DE').toUpperCase();
        const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/categories?module=vehicle&country=${country}`);
        if (res.ok) {
          const data = await res.json();
          setCategories(data || []);
        }
      } catch (e) {
        console.error('Category fetch error', e);
      }
    };
    fetchCategories();
  }, []);

  const rootCategories = useMemo(
    () => categories.filter((cat) => !cat.parent_id),
    [categories]
  );

  const childCategories = useMemo(
    () => categories.filter((cat) => cat.parent_id === activeParentId),
    [categories, activeParentId]
  );

  useEffect(() => {
    if (!activeParentId && rootCategories.length > 0) {
      setActiveParentId(rootCategories[0].id);
    }
  }, [activeParentId, rootCategories]);

  const handleParentSelect = (category) => {
    setActiveParentId(category.id);
  };

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
    setError('');
  };

  const getIcon = (category) => CATEGORY_ICONS[category.slug] || '🚗';

  const handleComplete = async () => {
    if (!selectedCategory) {
      setError('Kategori seçiniz.');
      return;
    }
    const ok = await createDraft(selectedCategory, { autoAdvance: false });
    if (!ok) {
      setError('Kategori kaydedilemedi.');
      return;
    }
    setCompletedSteps((prev) => ({
      ...prev,
      1: true,
      2: false,
      3: false,
      4: false,
      5: false,
      6: false,
    }));
    setError('');
  };

  const nextDisabled = !completedSteps[1];

  return (
    <div className="space-y-6" data-testid="listing-category-selector">
      <h2 className="text-2xl font-bold" data-testid="listing-category-title">Kategori Seç</h2>
      <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr] gap-6">
        <div className="space-y-2" data-testid="listing-category-parents">
          {rootCategories.map((cat) => (
            <button
              key={cat.id}
              disabled={loading}
              onClick={() => handleParentSelect(cat)}
              data-testid={`category-parent-${cat.id}`}
              className={`w-full px-4 py-3 border rounded-xl text-left transition ${
                activeParentId === cat.id
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-border hover:border-blue-600 hover:bg-blue-50'
              }`}
            >
              <span className="font-medium">{cat.name}</span>
            </button>
          ))}
        </div>

        <div className="space-y-4" data-testid="listing-category-children">
          {childCategories.length === 0 && activeParentId ? (
            <div className="p-6 border rounded-xl text-center" data-testid="listing-category-empty">
              <p className="text-muted-foreground mb-4" data-testid="listing-category-empty-text">Bu kategori altında alt kategori yok.</p>
              {rootCategories
                .filter((cat) => cat.id === activeParentId)
                .map((cat) => (
                  <button
                    key={cat.id}
                    disabled={loading}
                    onClick={() => handleCategorySelect(cat)}
                    data-testid={`category-select-${cat.id}`}
                    className="px-6 py-3 rounded-lg bg-blue-600 text-white"
                  >
                    {cat.name} seç
                  </button>
                ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {childCategories.map((cat) => (
                <button
                  key={cat.id}
                  disabled={loading}
                  onClick={() => handleCategorySelect(cat)}
                  data-testid={`category-select-${cat.id}`}
                  className="p-6 border rounded-xl hover:border-blue-600 hover:bg-blue-50 transition flex flex-col items-center gap-2 text-center"
                >
                  <span className="text-4xl">{getIcon(cat)}</span>
                  <span className="font-medium text-lg">{cat.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CategorySelector;
