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
  const { createDraft, loading, setStep, completedSteps, setCompletedSteps, schemaNotice } = useWizard();
  const [categories, setCategories] = useState([]);
  const [activeParentId, setActiveParentId] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [error, setError] = useState('');
  const [preselectedCategory, setPreselectedCategory] = useState(null);
  const [preselectApplied, setPreselectApplied] = useState(false);
  const [moduleKey] = useState(() => localStorage.getItem('ilan_ver_module') || 'vehicle');

  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const country = (localStorage.getItem('selected_country') || 'DE').toUpperCase();
        const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/categories?module=${moduleKey}&country=${country}`);
        if (res.ok) {
          const data = await res.json();
          setCategories(data || []);
        }
      } catch (e) {
        console.error('Category fetch error', e);
      }
    };
    fetchCategories();
  }, [moduleKey]);

  useEffect(() => {
    const stored = localStorage.getItem('ilan_ver_category');
    if (!stored) return;
    try {
      const parsed = JSON.parse(stored);
      if (parsed) {
        setPreselectedCategory(parsed);
      }
    } catch (err) {
      console.error('Preselected category parse error', err);
    }
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
    if (!activeParentId && rootCategories.length > 0 && !preselectedCategory) {
      setActiveParentId(rootCategories[0].id);
    }
  }, [activeParentId, rootCategories, preselectedCategory]);

  useEffect(() => {
    if (!preselectedCategory || preselectApplied || categories.length === 0) return;
    const match = categories.find((cat) => cat.id === preselectedCategory.id) || preselectedCategory;
    setSelectedCategory(match);
    if (match.parent_id) {
      setActiveParentId(match.parent_id);
    } else if (match.id) {
      setActiveParentId(match.id);
    }

    const applyPreselect = async () => {
      const ok = await createDraft(match, { autoAdvance: true });
      if (!ok) {
        setError('Kategori kaydedilemedi.');
        setPreselectApplied(true);
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
      setPreselectApplied(true);
      setStep(2);
    };

    applyPreselect();
  }, [preselectedCategory, preselectApplied, categories, createDraft, setCompletedSteps, setStep]);

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
                    className={`px-6 py-3 rounded-lg ${
                      selectedCategory?.id === cat.id ? 'bg-blue-600 text-white' : 'bg-blue-100 text-blue-700'
                    }`}
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
                  className={`p-6 border rounded-xl transition flex flex-col items-center gap-2 text-center ${
                    selectedCategory?.id === cat.id
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-border hover:border-blue-600 hover:bg-blue-50'
                  }`}
                >
                  <span className="text-4xl">{getIcon(cat)}</span>
                  <span className="font-medium text-lg">{cat.name}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {error && (
        <div className="text-sm text-red-600" data-testid="category-error">{error}</div>
      )}

      {schemaNotice && (
        <div className="text-sm text-amber-600" data-testid="category-schema-notice">{schemaNotice}</div>
      )}

      <div className="flex items-center justify-end gap-3" data-testid="category-actions">
        <div title={nextDisabled ? 'Önce bu adımı tamamlayın.' : ''} data-testid="category-next-tooltip">
          <button
            type="button"
            onClick={() => setStep(2)}
            disabled={nextDisabled}
            className="px-4 py-2 border rounded-md text-sm disabled:opacity-50"
            data-testid="category-next"
          >
            Next
          </button>
        </div>
        <button
          type="button"
          onClick={handleComplete}
          disabled={loading}
          className="px-5 py-2 bg-blue-600 text-white rounded-md disabled:opacity-60"
          data-testid="category-complete"
        >
          Tamam
        </button>
      </div>
    </div>
  );
};

export default CategorySelector;
