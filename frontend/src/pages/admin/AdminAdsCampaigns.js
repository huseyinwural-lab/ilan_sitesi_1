import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { Link } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const STATUS_LABELS = {
  draft: 'Taslak',
  active: 'Aktif',
  paused: 'Duraklatıldı',
  expired: 'Süresi Doldu',
};

const emptyForm = {
  name: '',
  advertiser: '',
  budget: '',
  currency: 'EUR',
  start_at: '',
  end_at: '',
  status: 'draft',
};

export default function AdminAdsCampaigns() {
  const [campaigns, setCampaigns] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [detail, setDetail] = useState(null);
  const [detailForm, setDetailForm] = useState(null);
  const [detailTab, setDetailTab] = useState('detail');
  const [form, setForm] = useState(emptyForm);
  const [status, setStatus] = useState('');
  const [detailStatus, setDetailStatus] = useState('');
  const [adsOptions, setAdsOptions] = useState([]);
  const [linkAdId, setLinkAdId] = useState('');
  const [placements, setPlacements] = useState({});
  const [formatLabels, setFormatLabels] = useState({});

  const authHeader = { Authorization: `Bearer ${localStorage.getItem('access_token')}` };

  const fetchCampaigns = async () => {
    const res = await axios.get(`${API}/admin/ads/campaigns`, { headers: authHeader });
    setCampaigns(res.data?.items || []);
  };

  const fetchCampaignDetail = async (id) => {
    if (!id) return;
    const res = await axios.get(`${API}/admin/ads/campaigns/${id}`, { headers: authHeader });
    setDetail(res.data);
  };

  const fetchAdsOptions = async () => {
    const res = await axios.get(`${API}/admin/ads`, { headers: authHeader });
    setAdsOptions(res.data?.items || []);
    setPlacements(res.data?.placements || {});
    setFormatLabels(res.data?.format_labels || {});
  };

  useEffect(() => {
    fetchCampaigns();
    fetchAdsOptions();
  }, []);

  useEffect(() => {
    if (!selectedId) return;
    fetchCampaignDetail(selectedId);
  }, [selectedId]);

  useEffect(() => {
    if (!detail?.campaign) return;
    const campaign = detail.campaign;
    setDetailForm({
      name: campaign.name || '',
      advertiser: campaign.advertiser || '',
      budget: campaign.budget ?? '',
      currency: campaign.currency || 'EUR',
      start_at: campaign.start_at ? campaign.start_at.slice(0, 16) : '',
      end_at: campaign.end_at ? campaign.end_at.slice(0, 16) : '',
      status: campaign.status || 'draft',
    });
  }, [detail]);

  const handleCreate = async () => {
    setStatus('');
    await axios.post(
      `${API}/admin/ads/campaigns`,
      {
        name: form.name,
        advertiser: form.advertiser || null,
        budget: form.budget !== '' ? Number(form.budget) : null,
        currency: form.currency || 'EUR',
        start_at: form.start_at || null,
        end_at: form.end_at || null,
        status: form.status || 'draft',
      },
      { headers: authHeader }
    );
    setStatus('Kampanya oluşturuldu');
    setForm(emptyForm);
    fetchCampaigns();
    fetchAdsOptions();
  };

  const handleUpdate = async () => {
    if (!selectedId || !detailForm) return;
    setDetailStatus('');
    await axios.patch(
      `${API}/admin/ads/campaigns/${selectedId}`,
      {
        name: detailForm.name,
        advertiser: detailForm.advertiser || null,
        budget: detailForm.budget !== '' ? Number(detailForm.budget) : null,
        currency: detailForm.currency || 'EUR',
        start_at: detailForm.start_at || null,
        end_at: detailForm.end_at || null,
        status: detailForm.status,
      },
      { headers: authHeader }
    );
    setDetailStatus('Kampanya güncellendi');
    fetchCampaigns();
    fetchCampaignDetail(selectedId);
  };

  const handleLinkAd = async () => {
    if (!selectedId || !linkAdId) return;
    await axios.post(`${API}/admin/ads/campaigns/${selectedId}/ads/${linkAdId}`, {}, { headers: authHeader });
    setLinkAdId('');
    fetchCampaignDetail(selectedId);
    fetchCampaigns();
    fetchAdsOptions();
  };

  const handleUnlinkAd = async (adId) => {
    if (!selectedId) return;
    await axios.delete(`${API}/admin/ads/campaigns/${selectedId}/ads/${adId}`, { headers: authHeader });
    fetchCampaignDetail(selectedId);
    fetchCampaigns();
    fetchAdsOptions();
  };

  const linkedAds = detail?.ads || [];
  const linkedAdIds = new Set(linkedAds.map((ad) => ad.id));
  const availableAds = useMemo(
    () => adsOptions.filter((ad) => !linkedAdIds.has(ad.id) && !ad.campaign_id),
    [adsOptions, linkedAdIds]
  );
  const warnings = detail?.warnings || [];

  return (
    <div className="space-y-6" data-testid="admin-ads-campaigns">
      <div>
        <h1 className="text-2xl font-semibold" data-testid="admin-campaigns-title">Reklam Kampanyaları</h1>
        <p className="text-sm text-muted-foreground" data-testid="admin-campaigns-subtitle">
          Kampanya oluşturma, bütçe ve süre yönetimini tek noktadan yönetin.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[2fr_3fr]">
        <div className="space-y-4">
          <div className="rounded-lg border bg-white p-4" data-testid="admin-campaigns-list">
            <div className="text-sm font-semibold mb-3">Kampanya Listesi</div>
            <div className="space-y-2">
              {campaigns.map((campaign) => (
                <button
                  key={campaign.id}
                  type="button"
                  onClick={() => setSelectedId(campaign.id)}
                  className={`w-full text-left border rounded-md p-3 hover:bg-slate-50 ${selectedId === campaign.id ? 'border-primary' : ''}`}
                  data-testid={`admin-campaigns-row-${campaign.id}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="font-semibold text-sm">{campaign.name}</div>
                    <div className="text-xs text-muted-foreground">{STATUS_LABELS[campaign.status] || campaign.status}</div>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {campaign.start_at ? campaign.start_at.slice(0, 10) : '—'} → {campaign.end_at ? campaign.end_at.slice(0, 10) : '—'}
                  </div>
                  <div className="text-xs mt-1">
                    Bütçe: {campaign.budget ?? '—'} {campaign.currency || ''}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Bağlı reklam: {campaign.total_ads} | Aktif: {campaign.active_ads}
                  </div>
                </button>
              ))}
              {campaigns.length === 0 && (
                <div className="text-xs text-muted-foreground" data-testid="admin-campaigns-empty">Kampanya bulunamadı.</div>
              )}
            </div>
          </div>

          <div className="rounded-lg border bg-white p-4 space-y-3" data-testid="admin-campaigns-create">
            <div className="text-sm font-semibold">Yeni Kampanya</div>
            <div className="grid gap-3 md:grid-cols-2">
              <input
                className="h-9 rounded-md border px-2"
                placeholder="Kampanya adı"
                value={form.name}
                onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                data-testid="admin-campaigns-create-name"
              />
              <input
                className="h-9 rounded-md border px-2"
                placeholder="Advertiser"
                value={form.advertiser}
                onChange={(e) => setForm((prev) => ({ ...prev, advertiser: e.target.value }))}
                data-testid="admin-campaigns-create-advertiser"
              />
              <input
                type="number"
                className="h-9 rounded-md border px-2"
                placeholder="Bütçe"
                value={form.budget}
                onChange={(e) => setForm((prev) => ({ ...prev, budget: e.target.value }))}
                data-testid="admin-campaigns-create-budget"
              />
              <input
                className="h-9 rounded-md border px-2"
                placeholder="Currency"
                value={form.currency}
                onChange={(e) => setForm((prev) => ({ ...prev, currency: e.target.value.toUpperCase() }))}
                data-testid="admin-campaigns-create-currency"
              />
              <input
                type="datetime-local"
                className="h-9 rounded-md border px-2"
                value={form.start_at}
                onChange={(e) => setForm((prev) => ({ ...prev, start_at: e.target.value }))}
                data-testid="admin-campaigns-create-start"
              />
              <input
                type="datetime-local"
                className="h-9 rounded-md border px-2"
                value={form.end_at}
                onChange={(e) => setForm((prev) => ({ ...prev, end_at: e.target.value }))}
                data-testid="admin-campaigns-create-end"
              />
              <select
                className="h-9 rounded-md border px-2"
                value={form.status}
                onChange={(e) => setForm((prev) => ({ ...prev, status: e.target.value }))}
                data-testid="admin-campaigns-create-status"
              >
                <option value="draft">Taslak</option>
                <option value="active">Aktif</option>
                <option value="paused">Duraklatıldı</option>
              </select>
            </div>
            {status && (
              <div className="text-xs text-emerald-600" data-testid="admin-campaigns-create-status-text">{status}</div>
            )}
            <button
              type="button"
              onClick={handleCreate}
              className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
              data-testid="admin-campaigns-create-button"
            >
              Kampanya Oluştur
            </button>
          </div>
        </div>

        <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="admin-campaigns-detail">
          {!detail ? (
            <div className="text-sm text-muted-foreground" data-testid="admin-campaigns-detail-empty">
              Detay görmek için bir kampanya seçin.
            </div>
          ) : (
            <>
              <div className="flex flex-wrap gap-2" data-testid="admin-campaigns-detail-tabs">
                <button
                  type="button"
                  onClick={() => setDetailTab('detail')}
                  className={`h-9 px-4 rounded-md text-sm border ${detailTab === 'detail' ? 'bg-primary text-primary-foreground' : 'bg-white'}`}
                  data-testid="admin-campaigns-tab-detail"
                >
                  Kampanya Detay
                </button>
                <button
                  type="button"
                  onClick={() => setDetailTab('ads')}
                  className={`h-9 px-4 rounded-md text-sm border ${detailTab === 'ads' ? 'bg-primary text-primary-foreground' : 'bg-white'}`}
                  data-testid="admin-campaigns-tab-ads"
                >
                  Bağlı Reklamlar
                </button>
              </div>

              {detailTab === 'detail' && detailForm && (
                <div className="space-y-3" data-testid="admin-campaigns-detail-form">
                  <div className="grid gap-3 md:grid-cols-2">
                    <input
                      className="h-9 rounded-md border px-2"
                      value={detailForm.name}
                      onChange={(e) => setDetailForm((prev) => ({ ...prev, name: e.target.value }))}
                      data-testid="admin-campaigns-detail-name"
                    />
                    <input
                      className="h-9 rounded-md border px-2"
                      value={detailForm.advertiser}
                      onChange={(e) => setDetailForm((prev) => ({ ...prev, advertiser: e.target.value }))}
                      data-testid="admin-campaigns-detail-advertiser"
                    />
                    <input
                      type="number"
                      className="h-9 rounded-md border px-2"
                      value={detailForm.budget}
                      onChange={(e) => setDetailForm((prev) => ({ ...prev, budget: e.target.value }))}
                      data-testid="admin-campaigns-detail-budget"
                    />
                    <input
                      className="h-9 rounded-md border px-2"
                      value={detailForm.currency}
                      onChange={(e) => setDetailForm((prev) => ({ ...prev, currency: e.target.value.toUpperCase() }))}
                      data-testid="admin-campaigns-detail-currency"
                    />
                    <input
                      type="datetime-local"
                      className="h-9 rounded-md border px-2"
                      value={detailForm.start_at}
                      onChange={(e) => setDetailForm((prev) => ({ ...prev, start_at: e.target.value }))}
                      data-testid="admin-campaigns-detail-start"
                    />
                    <input
                      type="datetime-local"
                      className="h-9 rounded-md border px-2"
                      value={detailForm.end_at}
                      onChange={(e) => setDetailForm((prev) => ({ ...prev, end_at: e.target.value }))}
                      data-testid="admin-campaigns-detail-end"
                    />
                    <select
                      className="h-9 rounded-md border px-2"
                      value={detailForm.status}
                      onChange={(e) => setDetailForm((prev) => ({ ...prev, status: e.target.value }))}
                      disabled={detail?.campaign?.status === 'expired'}
                      data-testid="admin-campaigns-detail-status"
                    >
                      {detail?.campaign?.status === 'draft' && (
                        <option value="draft">Taslak</option>
                      )}
                      <option value="active">Aktif</option>
                      <option value="paused">Duraklatıldı</option>
                    </select>
                  </div>
                  {detailStatus && (
                    <div className="text-xs text-emerald-600" data-testid="admin-campaigns-detail-status-text">{detailStatus}</div>
                  )}
                  <button
                    type="button"
                    onClick={handleUpdate}
                    className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
                    data-testid="admin-campaigns-detail-save"
                  >
                    Kaydet
                  </button>
                </div>
              )}

              {detailTab === 'ads' && (
                <div className="space-y-3" data-testid="admin-campaigns-ads-tab">
                  <div className="flex flex-wrap gap-2">
                    <select
                      className="h-9 rounded-md border px-2"
                      value={linkAdId}
                      onChange={(e) => setLinkAdId(e.target.value)}
                      data-testid="admin-campaigns-ads-select"
                    >
                      <option value="">Reklam seçin</option>
                      {availableAds.map((ad) => (
                        <option key={ad.id} value={ad.id}>
                          {placements[ad.placement] || ad.placement} · {ad.target_url || ad.asset_url || ad.id.slice(0, 8)}
                        </option>
                      ))}
                    </select>
                    <button
                      type="button"
                      onClick={handleLinkAd}
                      className="h-9 px-4 rounded-md border text-sm"
                      data-testid="admin-campaigns-ads-link"
                    >
                      Reklam Ekle
                    </button>
                  </div>

                  <div className="space-y-2">
                    {linkedAds.map((ad) => (
                      <div key={ad.id} className="border rounded-md p-3" data-testid={`admin-campaigns-ads-row-${ad.id}`}>
                        <div className="text-xs text-muted-foreground">
                          {placements[ad.placement] || ad.placement} · {formatLabels[ad.format] || ad.format || '—'}
                        </div>
                        <div className="text-sm">Aktif: {ad.is_active ? 'Evet' : 'Hayır'}</div>
                        <div className="flex flex-wrap gap-2 mt-2">
                          <Link
                            to="/admin/ads"
                            className="text-xs text-primary underline"
                            data-testid={`admin-campaigns-ads-link-${ad.id}`}
                          >
                            Reklama git
                          </Link>
                          <button
                            type="button"
                            onClick={() => handleUnlinkAd(ad.id)}
                            className="text-xs text-rose-600"
                            data-testid={`admin-campaigns-ads-unlink-${ad.id}`}
                          >
                            Çıkar
                          </button>
                        </div>
                      </div>
                    ))}
                    {linkedAds.length === 0 && (
                      <div className="text-xs text-muted-foreground" data-testid="admin-campaigns-ads-empty">
                        Bağlı reklam bulunamadı.
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
