import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

const ListingDetails = () => {
  const navigate = useNavigate();
  const selectedCategory = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('ilan_ver_category') || 'null');
    } catch (e) {
      return null;
    }
  }, []);

  const selectedVehicle = useMemo(() => {
    try {
      return JSON.parse(localStorage.getItem('ilan_ver_vehicle_selection') || 'null');
    } catch (e) {
      return null;
    }
  }, []);

  const vehicleLabel = useMemo(() => {
    if (!selectedVehicle) return null;
    const makeLabel = selectedVehicle?.make?.label || selectedVehicle?.make?.key || '';
    const modelLabel = selectedVehicle?.model?.label || selectedVehicle?.model?.key || '';
    const trimLabel = selectedVehicle?.manual_trim_flag
      ? `Manuel Trim: ${selectedVehicle?.manual_trim || ''}`
      : selectedVehicle?.trim_label || '';
    return [selectedVehicle.year, makeLabel, modelLabel, trimLabel].filter(Boolean).join(' / ');
  }, [selectedVehicle]);

  return (
    <div className="mx-auto max-w-4xl space-y-6" data-testid="ilan-ver-details-page">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="ilan-ver-details-title">İlan Detayları</h1>
          <p className="text-sm text-slate-600" data-testid="ilan-ver-details-subtitle">
            Detay formu bir sonraki adımda özelleştirilecek.
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/ilan-ver/kategori-secimi')}
          className="rounded-md border px-4 py-2 text-sm"
          data-testid="ilan-ver-details-back"
        >
          Kategoriye geri dön
        </button>
      </div>

      <div className="rounded-xl border bg-white p-4" data-testid="ilan-ver-details-summary">
        <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Seçilen kategori</div>
        <div className="mt-2 text-lg font-semibold text-slate-900" data-testid="ilan-ver-details-category">
          {selectedCategory?.name || 'Kategori seçilmedi'}
        </div>
      </div>

      <div className="rounded-xl border border-dashed bg-white p-6 text-sm text-slate-600" data-testid="ilan-ver-details-placeholder">
        Altıncı madde adımının detay formu bu sayfada uygulanacak.
      </div>
    </div>
  );
};

export default ListingDetails;
