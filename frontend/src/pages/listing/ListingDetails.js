import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

const ListingDetails = () => {
  const navigate = useNavigate();
  const [acceptedTerms, setAcceptedTerms] = useState(false);
  const [previewReady, setPreviewReady] = useState(false);
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

  const selectedPath = useMemo(() => {
    try {
      const parsed = JSON.parse(localStorage.getItem('ilan_ver_category_path') || '[]');
      return Array.isArray(parsed) ? parsed : [];
    } catch (_error) {
      return [];
    }
  }, []);

  const pathLabel = selectedPath.length > 0
    ? selectedPath.map((item) => item?.name).filter(Boolean).join(' > ')
    : (selectedCategory?.name || 'Kategori seçilmedi');

  const campaignCards = [
    { id: 'starter', title: 'Bireysel Başlangıç', price: '€9 / 7 gün' },
    { id: 'plus', title: 'Bireysel Plus', price: '€19 / 15 gün' },
    { id: 'pro', title: 'Kurumsal Pro', price: '€49 / 30 gün' },
  ];

  const handleContinue = () => {
    if (!acceptedTerms) return;
    setPreviewReady(true);
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6" data-testid="ilan-ver-details-page">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="ilan-ver-details-title">İlan Verme Formu</h1>
          <p className="text-sm text-slate-600" data-testid="ilan-ver-details-subtitle">
            Çekirdek alanlar tek sayfada listelenmiştir. Sıra PDF akışına göre uygulanmıştır.
          </p>
        </div>
        <button
          type="button"
          onClick={() => navigate('/ilan-ver')}
          className="rounded-md border px-4 py-2 text-sm"
          data-testid="ilan-ver-details-back"
        >
          Kategoriye geri dön
        </button>
      </div>

      <div className="rounded-xl border bg-white p-4 space-y-2" data-testid="ilan-ver-details-summary">
        <div className="text-xs uppercase tracking-[0.2em] text-slate-400" data-testid="ilan-ver-details-breadcrumb-label">Seçim Yolu</div>
        <div className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-details-breadcrumb">{pathLabel}</div>
        <div className="text-xs text-slate-500" data-testid="ilan-ver-details-category">
          Ana kategori {'>'} 1. alt kategori akışı aktif.
        </div>
      </div>

      {selectedVehicle && (
        <div className="rounded-xl border bg-white p-4" data-testid="ilan-ver-details-vehicle">
          <div className="text-xs uppercase tracking-[0.2em] text-slate-400">Araç Seçimi</div>
          <div className="mt-2 text-lg font-semibold text-slate-900" data-testid="ilan-ver-details-vehicle-label">
            {vehicleLabel || 'Araç seçimi yapılmadı'}
          </div>
          {selectedVehicle.manual_trim_flag && (
            <div className="mt-1 text-xs text-amber-600" data-testid="ilan-ver-details-manual-trim">
              Manuel trim işaretlendi
            </div>
          )}
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2" data-testid="ilan-ver-core-sections-grid">
        <section className="rounded-xl border bg-white p-4" data-testid="ilan-ver-core-section-1">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-core-section-1-title">1. Çekirdek Alanlar</h2>
          <p className="mt-1 text-xs text-slate-600" data-testid="ilan-ver-core-section-1-desc">Başlık, fiyat, açıklama gibi adminde tanımlı zorunlu alanlar.</p>
        </section>

        <section className="rounded-xl border bg-white p-4" data-testid="ilan-ver-core-section-2">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-core-section-2-title">2. Parametre Alanı (2a)</h2>
          <p className="mt-1 text-xs text-slate-600" data-testid="ilan-ver-core-section-2-desc">Adminde oluşturulan tüm parametreler bu alana yansır.</p>
        </section>

        <section className="rounded-xl border bg-white p-4" data-testid="ilan-ver-core-section-3">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-core-section-3-title">3. Adres Formu</h2>
          <p className="mt-1 text-xs text-slate-600" data-testid="ilan-ver-core-section-3-desc">Adres alanları admin yapılandırmasından gelir.</p>
        </section>

        <section className="rounded-xl border bg-white p-4" data-testid="ilan-ver-core-section-4">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-core-section-4-title">4. Detay Gruplar (2c)</h2>
          <p className="mt-1 text-xs text-slate-600" data-testid="ilan-ver-core-section-4-desc">Detay gruplar admin paneldeki tanımlara göre yüklenir.</p>
        </section>

        <section className="rounded-xl border bg-white p-4" data-testid="ilan-ver-core-section-5">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-core-section-5-title">5. Fotoğraf ve Video</h2>
          <p className="mt-1 text-xs text-slate-600" data-testid="ilan-ver-core-section-5-desc">Medya yükleme alanları admindeki kurallara göre açılır.</p>
        </section>

        <section className="rounded-xl border bg-white p-4" data-testid="ilan-ver-core-section-6">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-core-section-6-title">6. İletişim Bilgisi</h2>
          <p className="mt-1 text-xs text-slate-600" data-testid="ilan-ver-core-section-6-desc">İletişim formu admindeki alan setinden gelir.</p>
        </section>
      </div>

      <section className="rounded-xl border bg-white p-4" data-testid="ilan-ver-core-section-7">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-core-section-7-title">7. Kampanya Seçimi</h2>
          <button type="button" className="text-xs font-semibold text-blue-600" data-testid="ilan-ver-campaign-detail-link">Detaylı bilgi</button>
        </div>
        <p className="mt-1 text-xs text-slate-600" data-testid="ilan-ver-core-section-7-desc">Bireysel/kurumsal kampanyalar satır-sütun yapısında listelenir.</p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3" data-testid="ilan-ver-campaign-grid">
          {campaignCards.map((campaign) => (
            <article key={campaign.id} className="rounded-lg border bg-slate-50 p-3" data-testid={`ilan-ver-campaign-card-${campaign.id}`}>
              <div className="text-sm font-semibold text-slate-900" data-testid={`ilan-ver-campaign-title-${campaign.id}`}>{campaign.title}</div>
              <div className="mt-1 text-xs text-slate-600" data-testid={`ilan-ver-campaign-price-${campaign.id}`}>{campaign.price}</div>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-xl border bg-white p-4" data-testid="ilan-ver-core-section-8">
        <label className="flex items-start gap-3" data-testid="ilan-ver-terms-label">
          <input
            type="checkbox"
            checked={acceptedTerms}
            onChange={(event) => setAcceptedTerms(event.target.checked)}
            className="mt-1 h-4 w-4"
            data-testid="ilan-ver-terms-checkbox"
          />
          <span className="text-sm text-slate-700" data-testid="ilan-ver-terms-text">İlan verme kurallarını okudum, kabul ediyorum.</span>
        </label>
      </section>

      <section className="rounded-xl border bg-white p-4" data-testid="ilan-ver-next-steps">
        <h2 className="text-sm font-semibold text-slate-900" data-testid="ilan-ver-next-steps-title">Sonraki Akış</h2>
        <ol className="mt-2 list-decimal space-y-1 pl-4 text-xs text-slate-600" data-testid="ilan-ver-next-steps-list">
          <li data-testid="ilan-ver-next-step-preview">Ön izleme ekranı</li>
          <li data-testid="ilan-ver-next-step-doping">Doping sayfası</li>
          <li data-testid="ilan-ver-next-step-admin">Onay için admine gönderim</li>
        </ol>
      </section>

      <div className="flex flex-wrap items-center justify-end gap-3" data-testid="ilan-ver-details-actions">
        <button
          type="button"
          onClick={handleContinue}
          disabled={!acceptedTerms}
          className="rounded-md bg-blue-600 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50"
          data-testid="ilan-ver-details-continue"
        >
          Devam
        </button>
      </div>

      {previewReady && (
        <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700" data-testid="ilan-ver-details-preview-ready">
          Ön izleme adımına geçiş hazırlandı. Sonraki sprintte akış endpointleri ile bağlanacaktır.
        </div>
      )}
    </div>
  );
};

export default ListingDetails;
