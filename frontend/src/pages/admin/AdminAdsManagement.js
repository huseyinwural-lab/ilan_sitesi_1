import React, { useEffect, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const emptyForm = {
  placement: '',
  format: '',
  start_at: '',
  end_at: '',
  priority: 0,
  is_active: true,
  target_url: '',
};

export default function AdminAdsManagement() {
  const [ads, setAds] = useState([]);
  const [placements, setPlacements] = useState({});
  const [formatRules, setFormatRules] = useState({});
  const [formatLabels, setFormatLabels] = useState({});
  const [form, setForm] = useState(emptyForm);
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState('');
  const [activeTab, setActiveTab] = useState('manage');
  const [groupBy, setGroupBy] = useState('ad');
  const [analytics, setAnalytics] = useState(null);
  const [analyticsStatus, setAnalyticsStatus] = useState('idle');
  const [range, setRange] = useState('30d');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  const authHeader = { Authorization: `Bearer ${localStorage.getItem('access_token')}` };

  const getAllowedFormats = (placement) => formatRules?.[placement] || [];
  const formatLabel = (value) => formatLabels?.[value] || value;
  const adLabel = (item) => item?.target_url || item?.asset_url || `Reklam ${item?.id?.slice(0, 8)}`;

  const fetchAds = async () => {
    const res = await axios.get(`${API}/admin/ads`, { headers: authHeader });
    const items = res.data?.items || [];
    const rules = res.data?.format_rules || {};
    const labels = res.data?.format_labels || {};
    const normalizedItems = items.map((item) => {
      const allowed = rules[item.placement] || [];
      return {
        ...item,
        format: item.format || allowed[0] || '',
      };
    });
    setAds(normalizedItems);
    setPlacements(res.data?.placements || {});
    setFormatRules(rules);
    setFormatLabels(labels);
    if (!form.placement && res.data?.placements) {
      const first = Object.keys(res.data.placements)[0];
      const defaultFormat = rules[first]?.[0] || '';
      setForm((prev) => ({ ...prev, placement: first || '', format: defaultFormat }));
    }
  };

  useEffect(() => {
    fetchAds();
  }, []);

  useEffect(() => {
    const allowed = getAllowedFormats(form.placement);
    if (!allowed.length) return;
    if (!form.format || !allowed.includes(form.format)) {
      setForm((prev) => ({ ...prev, format: allowed[0] }));
    }
  }, [form.placement, formatRules]);

  const fetchAnalytics = async (overrideRange, overrideGroup) => {
    setAnalyticsStatus('loading');
    try {
      const selectedRange = overrideRange || range;
      const selectedGroup = overrideGroup || groupBy;
      const params = { group_by: selectedGroup };
      if (selectedRange === 'custom') {
        if (!customStart || !customEnd) {
          setAnalyticsStatus('error');
          return;
        }
        params.start_at = customStart;
        params.end_at = customEnd;
      } else {
        params.range = selectedRange;
      }
      const res = await axios.get(`${API}/admin/ads/analytics`, { params, headers: authHeader });
      setAnalytics(res.data);
      setAnalyticsStatus('ok');
    } catch (err) {
      setAnalyticsStatus('error');
    }
  };

  useEffect(() => {
    if (activeTab !== 'performance') return;
    if (range === 'custom' && (!customStart || !customEnd)) return;
    fetchAnalytics();
  }, [activeTab, range, customStart, customEnd, groupBy]);

  const totals = analytics?.totals || { impressions: 0, clicks: 0, ctr: 0, active_ads: 0 };
  const breakdownRows = Array.isArray(analytics?.groups) ? analytics.groups : [];
  const breakdownTitle = groupBy === 'campaign' ? 'Kampanya Kırılımı' : 'Reklam Kırılımı';

  const activeConflict = form.is_active && form.placement
    ? ads.find((ad) => ad.is_active && ad.placement === form.placement)
    : null;
  const createDisabled = Boolean(activeConflict);

  const handleCreate = async () => {
    setStatus('');
    const payload = {
      placement: form.placement,
      format: form.format || null,
      start_at: form.start_at || null,
      end_at: form.end_at || null,
      priority: Number(form.priority) || 0,
      is_active: Boolean(form.is_active),
      target_url: form.target_url || null,
    };
    const res = await axios.post(`${API}/admin/ads`, payload, { headers: authHeader });
    const adId = res.data?.id;
    if (file && adId) {
      const fd = new FormData();
      fd.append('file', file);
      await axios.post(`${API}/admin/ads/${adId}/upload`, fd, { headers: authHeader });
    }
    setStatus('Reklam oluşturuldu');
    setForm(emptyForm);
    setFile(null);
    fetchAds();
  };

  const handleUpdate = async (item) => {
    await axios.patch(
      `${API}/admin/ads/${item.id}`,
      {
        start_at: item.start_at || null,
        end_at: item.end_at || null,
        priority: Number(item.priority) || 0,
        is_active: Boolean(item.is_active),
        target_url: item.target_url || null,
        format: item.format || null,
      },
      { headers: authHeader }
    );
    fetchAds();
  };

  const handleUpload = async (itemId, uploadFile) => {
    if (!uploadFile) return;
    const fd = new FormData();
    fd.append('file', uploadFile);
    await axios.post(`${API}/admin/ads/${itemId}/upload`, fd, { headers: authHeader });
    fetchAds();
  };

  return (
    <div className="space-y-6" data-testid="admin-ads-management">
      <div>
        <h1 className="text-2xl font-semibold" data-testid="admin-ads-title">Reklam Yönetimi</h1>
        <p className="text-sm text-muted-foreground" data-testid="admin-ads-subtitle">
          Placement bazlı reklam slotlarını yönetin.
        </p>
      </div>

      <div className="flex flex-wrap gap-2" data-testid="admin-ads-tabs">
        <button
          type="button"
          onClick={() => setActiveTab('manage')}
          className={`h-9 px-4 rounded-md text-sm border ${activeTab === 'manage' ? 'bg-primary text-primary-foreground' : 'bg-white'}`}
          data-testid="admin-ads-tab-manage"
        >
          Reklam Yönetimi
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('performance')}
          className={`h-9 px-4 rounded-md text-sm border ${activeTab === 'performance' ? 'bg-primary text-primary-foreground' : 'bg-white'}`}
          data-testid="admin-ads-tab-performance"
        >
          Reklam Performans
        </button>
      </div>

      {activeTab === 'manage' && (
        <>

      <div className="rounded-lg border bg-white p-4 space-y-3" data-testid="admin-ads-create">
        <div className="text-sm font-semibold">Yeni Reklam</div>
        <div className="grid gap-3 md:grid-cols-2">
          <div>
            <label className="text-xs">Placement</label>
            <select
              className="mt-1 h-9 w-full rounded-md border px-2"
              value={form.placement}
              onChange={(e) => setForm((prev) => ({ ...prev, placement: e.target.value }))}
              data-testid="admin-ads-placement"
            >
              {Object.entries(placements).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs">Format</label>
            <select
              className="mt-1 h-9 w-full rounded-md border px-2"
              value={form.format}
              onChange={(e) => setForm((prev) => ({ ...prev, format: e.target.value }))}
              data-testid="admin-ads-format"
            >
              {getAllowedFormats(form.placement).map((fmt) => (
                <option key={fmt} value={fmt}>{formatLabel(fmt)}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs">Priority</label>
            <input
              type="number"
              className="mt-1 h-9 w-full rounded-md border px-2"
              value={form.priority}
              onChange={(e) => setForm((prev) => ({ ...prev, priority: e.target.value }))}
              data-testid="admin-ads-priority"
            />
          </div>
          <div>
            <label className="text-xs">Start</label>
            <input
              type="datetime-local"
              className="mt-1 h-9 w-full rounded-md border px-2"
              value={form.start_at}
              onChange={(e) => setForm((prev) => ({ ...prev, start_at: e.target.value }))}
              data-testid="admin-ads-start"
            />
          </div>
          <div>
            <label className="text-xs">End</label>
            <input
              type="datetime-local"
              className="mt-1 h-9 w-full rounded-md border px-2"
              value={form.end_at}
              onChange={(e) => setForm((prev) => ({ ...prev, end_at: e.target.value }))}
              data-testid="admin-ads-end"
            />
          </div>
          <div>
            <label className="text-xs">Target URL</label>
            <input
              className="mt-1 h-9 w-full rounded-md border px-2"
              value={form.target_url}
              onChange={(e) => setForm((prev) => ({ ...prev, target_url: e.target.value }))}
              data-testid="admin-ads-target"
            />
          </div>
          <div className="flex items-center gap-2 mt-5">
            <input
              type="checkbox"
              checked={form.is_active}
              onChange={(e) => setForm((prev) => ({ ...prev, is_active: e.target.checked }))}
              data-testid="admin-ads-active"
            />
            <span className="text-xs">Aktif</span>
          </div>
          <div>
            <label className="text-xs">Dosya</label>
            <input
              type="file"
              accept=".png,.jpg,.jpeg,.webp"
              className="mt-1 block w-full"
              onChange={(e) => setFile(e.target.files?.[0] || null)}
              data-testid="admin-ads-file"
            />
          </div>
        </div>
        {activeConflict && (
          <div className="text-xs text-rose-600" data-testid="admin-ads-active-conflict">
            Bu alanda zaten aktif reklam var: {adLabel(activeConflict)}. Önce pasife alın.
          </div>
        )}
        {status && (
          <div className="text-xs text-emerald-600" data-testid="admin-ads-status">{status}</div>
        )}
        <button
          type="button"
          onClick={handleCreate}
          disabled={createDisabled}
          className={`h-9 px-4 rounded-md text-sm ${createDisabled ? 'bg-slate-200 text-slate-500 cursor-not-allowed' : 'bg-primary text-primary-foreground'}`}
          data-testid="admin-ads-create-button"
        >
          Reklam Oluştur
        </button>
      </div>

      <div className="rounded-lg border bg-white p-4" data-testid="admin-ads-list">
        <div className="text-sm font-semibold mb-3">Mevcut Reklamlar</div>
        <div className="space-y-4">
          {ads.map((ad) => (
            <div key={ad.id} className="border rounded-md p-3 space-y-2" data-testid={`admin-ads-item-${ad.id}`}>
              <div className="text-xs text-muted-foreground">{placements[ad.placement] || ad.placement}</div>
              {ad.asset_url && (
                <img src={ad.asset_url} alt="ad" className="h-20 object-cover" data-testid={`admin-ads-image-${ad.id}`} />
              )}
              <div className="grid gap-2 md:grid-cols-2">
                <input
                  type="datetime-local"
                  className="h-9 rounded-md border px-2"
                  value={ad.start_at ? ad.start_at.slice(0, 16) : ''}
                  onChange={(e) => {
                    const value = e.target.value;
                    setAds((prev) => prev.map((item) => (item.id === ad.id ? { ...item, start_at: value } : item)));
                  }}
                  data-testid={`admin-ads-item-start-${ad.id}`}
                />
                <input
                  type="datetime-local"
                  className="h-9 rounded-md border px-2"
                  value={ad.end_at ? ad.end_at.slice(0, 16) : ''}
                  onChange={(e) => {
                    const value = e.target.value;
                    setAds((prev) => prev.map((item) => (item.id === ad.id ? { ...item, end_at: value } : item)));
                  }}
                  data-testid={`admin-ads-item-end-${ad.id}`}
                />
                <input
                  className="h-9 rounded-md border px-2"
                  value={ad.target_url || ''}
                  onChange={(e) => {
                    const value = e.target.value;
                    setAds((prev) => prev.map((item) => (item.id === ad.id ? { ...item, target_url: value } : item)));
                  }}
                  data-testid={`admin-ads-item-target-${ad.id}`}
                />
                <input
                  type="number"
                  className="h-9 rounded-md border px-2"
                  value={ad.priority}
                  onChange={(e) => {
                    const value = e.target.value;
                    setAds((prev) => prev.map((item) => (item.id === ad.id ? { ...item, priority: value } : item)));
                  }}
                  data-testid={`admin-ads-item-priority-${ad.id}`}
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={ad.is_active}
                  onChange={(e) => {
                    const value = e.target.checked;
                    setAds((prev) => prev.map((item) => (item.id === ad.id ? { ...item, is_active: value } : item)));
                  }}
                  data-testid={`admin-ads-item-active-${ad.id}`}
                />
                <span className="text-xs">Aktif</span>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <input
                  type="file"
                  accept=".png,.jpg,.jpeg,.webp"
                  onChange={(e) => handleUpload(ad.id, e.target.files?.[0])}
                  data-testid={`admin-ads-item-file-${ad.id}`}
                />
                <button
                  type="button"
                  onClick={() => handleUpdate(ad)}
                  className="h-9 px-3 rounded-md border text-sm"
                  data-testid={`admin-ads-item-save-${ad.id}`}
                >
                  Kaydet
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
        </>
      )}

      {activeTab === 'performance' && (
        <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="admin-ads-performance">
          <div className="flex flex-wrap items-end gap-3" data-testid="admin-ads-analytics-filters">
            <div>
              <label className="text-xs">Zaman Aralığı</label>
              <select
                className="mt-1 h-9 w-full rounded-md border px-2"
                value={range}
                onChange={(e) => setRange(e.target.value)}
                data-testid="admin-ads-analytics-range"
              >
                <option value="30d">Son 30 Gün</option>
                <option value="7d">Son 7 Gün</option>
                <option value="custom">Özel Aralık</option>
              </select>
            </div>

            {range === 'custom' && (
              <>
                <div>
                  <label className="text-xs">Başlangıç</label>
                  <input
                    type="date"
                    className="mt-1 h-9 w-full rounded-md border px-2"
                    value={customStart}
                    onChange={(e) => setCustomStart(e.target.value)}
                    data-testid="admin-ads-analytics-start"
                  />
                </div>
                <div>
                  <label className="text-xs">Bitiş</label>
                  <input
                    type="date"
                    className="mt-1 h-9 w-full rounded-md border px-2"
                    value={customEnd}
                    onChange={(e) => setCustomEnd(e.target.value)}
                    data-testid="admin-ads-analytics-end"
                  />
                </div>
                <button
                  type="button"
                  onClick={() => fetchAnalytics('custom')}
                  className="h-9 px-4 rounded-md border text-sm"
                  data-testid="admin-ads-analytics-apply"
                >
                  Uygula
                </button>
              </>
            )}
          </div>

          <div className="flex flex-wrap gap-2" data-testid="admin-ads-analytics-group-tabs">
            <button
              type="button"
              onClick={() => setGroupBy('ad')}
              className={`h-9 px-4 rounded-md text-sm border ${groupBy === 'ad' ? 'bg-primary text-primary-foreground' : 'bg-white'}`}
              data-testid="admin-ads-analytics-group-ad"
            >
              Reklam Bazlı
            </button>
            <button
              type="button"
              onClick={() => setGroupBy('campaign')}
              className={`h-9 px-4 rounded-md text-sm border ${groupBy === 'campaign' ? 'bg-primary text-primary-foreground' : 'bg-white'}`}
              data-testid="admin-ads-analytics-group-campaign"
            >
              Kampanya Bazlı
            </button>
          </div>

          {analyticsStatus === 'loading' && (
            <div className="text-sm text-muted-foreground" data-testid="admin-ads-analytics-loading">Yükleniyor...</div>
          )}
          {analyticsStatus === 'error' && (
            <div className="text-sm text-rose-600" data-testid="admin-ads-analytics-error">Performans verileri alınamadı.</div>
          )}
          {analyticsStatus === 'ok' && (
            <div className="space-y-4" data-testid="admin-ads-analytics-content">
              <div className="grid gap-3 md:grid-cols-4" data-testid="admin-ads-analytics-totals">
                <div className="rounded-md border p-3" data-testid="admin-ads-analytics-total-impressions">
                  <div className="text-xs text-muted-foreground">Toplam Gösterim</div>
                  <div className="text-lg font-semibold">{totals.impressions}</div>
                </div>
                <div className="rounded-md border p-3" data-testid="admin-ads-analytics-total-clicks">
                  <div className="text-xs text-muted-foreground">Toplam Tıklama</div>
                  <div className="text-lg font-semibold">{totals.clicks}</div>
                </div>
                <div className="rounded-md border p-3" data-testid="admin-ads-analytics-total-ctr">
                  <div className="text-xs text-muted-foreground">CTR (%)</div>
                  <div className="text-lg font-semibold">{totals.ctr}</div>
                </div>
                <div className="rounded-md border p-3" data-testid="admin-ads-analytics-total-active">
                  <div className="text-xs text-muted-foreground">Aktif Reklam Sayısı</div>
                  <div className="text-lg font-semibold">{totals.active_ads}</div>
                </div>
              </div>

              <div className="rounded-md border" data-testid="admin-ads-analytics-breakdown">
                <div className="px-4 py-3 border-b text-sm font-semibold" data-testid="admin-ads-analytics-breakdown-title">{breakdownTitle}</div>
                <div className="divide-y">
                  {breakdownRows.map((item) => (
                    <div
                      key={item.key}
                      className="grid grid-cols-4 gap-2 px-4 py-2 text-sm"
                      data-testid={`admin-ads-analytics-row-${item.key}`}
                    >
                      <div data-testid={`admin-ads-analytics-label-${item.key}`}>{item.label || item.key}</div>
                      <div data-testid={`admin-ads-analytics-impressions-${item.key}`}>{item.impressions}</div>
                      <div data-testid={`admin-ads-analytics-clicks-${item.key}`}>{item.clicks}</div>
                      <div data-testid={`admin-ads-analytics-ctr-${item.key}`}>{item.ctr}</div>
                    </div>
                  ))}
                  {breakdownRows.length === 0 && (
                    <div className="px-4 py-3 text-sm text-muted-foreground" data-testid="admin-ads-analytics-empty">
                      Veri bulunamadı.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
