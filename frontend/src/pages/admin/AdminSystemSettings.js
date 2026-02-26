import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ui/toaster';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const MODERATION_FREEZE_KEY = 'moderation.freeze.active';
const WATERMARK_PIPELINE_KEY = 'media.watermark.pipeline';
const DEFAULT_MEILI_INDEX_NAME = 'listings_index';

const resolveFreezeValue = (setting) => {
  const value = setting?.value;
  if (typeof value === 'boolean') return value;
  if (typeof value === 'string') return value.toLowerCase() === 'true';
  if (value && typeof value === 'object') {
    const candidate = value.enabled ?? value.active ?? value.value;
    if (typeof candidate === 'boolean') return candidate;
    if (typeof candidate === 'string') return candidate.toLowerCase() === 'true';
  }
  return false;
};

const parseValue = (raw) => {
  if (raw === '') return '';
  try {
    return JSON.parse(raw);
  } catch {
    return raw;
  }
};

const formatValue = (value) => {
  if (value === null || value === undefined) return '';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
};

export default function AdminSystemSettingsPage() {
  const { user } = useAuth();
  const { toast } = useToast();
  const isSuperAdmin = user?.role === 'super_admin';
  const isSystemAdmin = isSuperAdmin;
  const [cloudflareConfig, setCloudflareConfig] = useState({
    account_id_masked: '',
    zone_id_masked: '',
    account_id_last4: '',
    zone_id_last4: '',
    cf_ids_source: '',
    cf_ids_present: false,
    canary_status: 'UNKNOWN',
    canary_checked_at: null,
  });
  const [cloudflareForm, setCloudflareForm] = useState({ account_id: '', zone_id: '' });
  const [cloudflareLoading, setCloudflareLoading] = useState(true);
  const [cloudflareSaving, setCloudflareSaving] = useState(false);
  const [cloudflareError, setCloudflareError] = useState('');
  const [canaryLoading, setCanaryLoading] = useState(false);
  const [encryptionKeyPresent, setEncryptionKeyPresent] = useState(true);
  const [cfMetricsEnabled, setCfMetricsEnabled] = useState(false);
  const [configMissingReason, setConfigMissingReason] = useState('');
  const [items, setItems] = useState([]);
  const [freezeSetting, setFreezeSetting] = useState(null);
  const [freezeActive, setFreezeActive] = useState(false);
  const [freezeReason, setFreezeReason] = useState('');
  const [freezeSaving, setFreezeSaving] = useState(false);
  const [loading, setLoading] = useState(true);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({
    key: '',
    value: '',
    country_code: '',
    is_readonly: false,
    description: '',
  });
  const [filterKey, setFilterKey] = useState('');
  const [filterCountry, setFilterCountry] = useState('');
  const [error, setError] = useState(null);
  const [meiliTab, setMeiliTab] = useState('active');
  const [meiliLoading, setMeiliLoading] = useState(true);
  const [meiliError, setMeiliError] = useState('');
  const [meiliNotice, setMeiliNotice] = useState('');
  const [meiliSaving, setMeiliSaving] = useState(false);
  const [meiliTestingId, setMeiliTestingId] = useState(null);
  const [meiliActivatingId, setMeiliActivatingId] = useState(null);
  const [meiliRevokingId, setMeiliRevokingId] = useState(null);
  const [meiliLatestConfigId, setMeiliLatestConfigId] = useState(null);
  const [meiliEncryptionKeyPresent, setMeiliEncryptionKeyPresent] = useState(true);
  const [meiliActiveConfig, setMeiliActiveConfig] = useState(null);
  const [meiliHistory, setMeiliHistory] = useState([]);
  const [meiliForm, setMeiliForm] = useState({
    meili_url: '',
    meili_index_name: DEFAULT_MEILI_INDEX_NAME,
    meili_master_key: '',
  });
  const [watermarkLoading, setWatermarkLoading] = useState(true);
  const [watermarkSaving, setWatermarkSaving] = useState(false);
  const [watermarkError, setWatermarkError] = useState('');
  const [watermarkConfig, setWatermarkConfig] = useState({
    enabled: true,
    position: 'bottom_right',
    opacity: 0.35,
    web_max_width: 1800,
    thumb_max_width: 520,
  });
  const [watermarkLogoUrl, setWatermarkLogoUrl] = useState(null);
  const [watermarkPreviewUrl, setWatermarkPreviewUrl] = useState(null);
  const [watermarkPerf, setWatermarkPerf] = useState(null);
  const [healthDetail, setHealthDetail] = useState(null);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);



  const fetchSettings = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterCountry) params.set('country', filterCountry.toUpperCase());
      const res = await axios.get(`${API}/admin/system-settings?${params.toString()}`, { headers: authHeader });
      setItems(res.data.items || []);
    } catch (e) {
      console.error('Failed to fetch system settings', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchCloudflareConfig = async () => {
    setCloudflareLoading(true);
    setCloudflareError('');
    try {
      const res = await axios.get(`${API}/admin/system-settings/cloudflare`, { headers: authHeader });
      setCloudflareConfig(res.data || {});
    } catch (e) {
      setCloudflareError('Cloudflare konfigürasyonu alınamadı');
    } finally {
      setCloudflareLoading(false);
    }
  };

  const fetchHealthDetail = async () => {
    try {
      const res = await axios.get(`${API}/admin/system/health-detail`, { headers: authHeader });
      setHealthDetail(res.data || null);
      setEncryptionKeyPresent(Boolean(res.data?.encryption_key_present));
      setCfMetricsEnabled(Boolean(res.data?.cf_metrics_enabled));
      setConfigMissingReason(res.data?.config_missing_reason || '');
    } catch (e) {
      setHealthDetail(null);
      setEncryptionKeyPresent(false);
    }
  };

  const fetchMeiliActiveConfig = async () => {
    if (!isSystemAdmin) return;
    setMeiliLoading(true);
    setMeiliError('');
    try {
      const res = await axios.get(`${API}/admin/system-settings/meilisearch`, { headers: authHeader });
      setMeiliActiveConfig(res.data?.active_config || null);
      setMeiliEncryptionKeyPresent(Boolean(res.data?.encryption_key_present));
      if (!meiliForm.meili_index_name) {
        setMeiliForm((prev) => ({
          ...prev,
          meili_index_name: res.data?.default_index_name || DEFAULT_MEILI_INDEX_NAME,
        }));
      }
    } catch (e) {
      setMeiliError(e.response?.data?.detail || 'Meilisearch aktif konfig alınamadı');
    } finally {
      setMeiliLoading(false);
    }
  };

  const fetchMeiliHistory = async () => {
    if (!isSystemAdmin) return;
    try {
      const res = await axios.get(`${API}/admin/system-settings/meilisearch/history`, { headers: authHeader });
      setMeiliHistory(res.data?.items || []);
    } catch (e) {
      setMeiliError(e.response?.data?.detail || 'Meilisearch geçmişi alınamadı');
    }
  };

  const handleSaveMeiliConfig = async () => {
    if (!isSystemAdmin) return;
    if (!meiliEncryptionKeyPresent) {
      setMeiliError('Kaydedilemedi: CONFIG_ENCRYPTION_KEY eksik.');
      return;
    }
    if (!meiliForm.meili_url || !meiliForm.meili_master_key) {
      setMeiliError('Meili URL ve Master Key zorunludur.');
      return;
    }
    setMeiliSaving(true);
    setMeiliError('');
    setMeiliNotice('');
    try {
      const payload = {
        meili_url: meiliForm.meili_url,
        meili_index_name: meiliForm.meili_index_name || DEFAULT_MEILI_INDEX_NAME,
        meili_master_key: meiliForm.meili_master_key,
      };
      const res = await axios.post(`${API}/admin/system-settings/meilisearch`, payload, { headers: authHeader });
      const savedId = res.data?.config?.id;
      setMeiliLatestConfigId(savedId || null);
      setMeiliNotice('Konfig kaydedildi. Aktivasyon için Test PASS gereklidir.');
      setMeiliForm((prev) => ({
        ...prev,
        meili_master_key: '',
      }));
      await fetchMeiliActiveConfig();
      await fetchMeiliHistory();
      await fetchHealthDetail();
    } catch (e) {
      setMeiliError(e.response?.data?.detail || 'Konfig kaydedilemedi');
    } finally {
      setMeiliSaving(false);
    }
  };

  const handleTestMeiliConfig = async (configId) => {
    if (!isSystemAdmin || !configId) return;
    setMeiliTestingId(configId);
    setMeiliError('');
    setMeiliNotice('');
    try {
      const res = await axios.post(`${API}/admin/system-settings/meilisearch/${configId}/test`, {}, { headers: authHeader });
      const testStatus = res.data?.result?.status;
      const reasonCode = res.data?.result?.reason_code;
      setMeiliNotice(`Test sonucu: ${testStatus || 'UNKNOWN'} (${reasonCode || 'none'})`);
      await fetchMeiliActiveConfig();
      await fetchMeiliHistory();
      await fetchHealthDetail();
    } catch (e) {
      setMeiliError(e.response?.data?.detail || 'Test başarısız');
    } finally {
      setMeiliTestingId(null);
    }
  };

  const handleActivateMeiliConfig = async (configId) => {
    if (!isSystemAdmin || !configId) return;
    setMeiliActivatingId(configId);
    setMeiliError('');
    setMeiliNotice('');
    try {
      const res = await axios.post(`${API}/admin/system-settings/meilisearch/${configId}/activate`, {}, { headers: authHeader });
      const ok = Boolean(res.data?.ok);
      const reasonCode = res.data?.result?.reason_code;
      if (ok) {
        setMeiliNotice('Konfig aktif edildi. Search katmanı bu konfig ile çalışacak.');
      } else {
        setMeiliError(`Aktivasyon reddedildi: ${reasonCode || 'test_failed'}`);
      }
      await fetchMeiliActiveConfig();
      await fetchMeiliHistory();
      await fetchHealthDetail();
    } catch (e) {
      setMeiliError(e.response?.data?.detail || 'Aktivasyon başarısız');
    } finally {
      setMeiliActivatingId(null);
    }
  };

  const handleRevokeMeiliConfig = async (configId) => {
    if (!isSystemAdmin || !configId) return;
    setMeiliRevokingId(configId);
    setMeiliError('');
    setMeiliNotice('');
    try {
      await axios.post(`${API}/admin/system-settings/meilisearch/${configId}/revoke`, {}, { headers: authHeader });
      setMeiliNotice('Konfig revoke edildi.');
      await fetchMeiliActiveConfig();
      await fetchMeiliHistory();
      await fetchHealthDetail();
    } catch (e) {
      setMeiliError(e.response?.data?.detail || 'Revoke başarısız');
    } finally {
      setMeiliRevokingId(null);
    }
  };

  const fetchWatermarkSettings = async () => {
    setWatermarkLoading(true);
    setWatermarkError('');
    try {
      const res = await axios.get(`${API}/admin/media/watermark/settings`, { headers: authHeader });
      setWatermarkConfig({
        enabled: Boolean(res.data?.config?.enabled ?? true),
        position: res.data?.config?.position || 'bottom_right',
        opacity: Number(res.data?.config?.opacity ?? 0.35),
        web_max_width: Number(res.data?.config?.web_max_width ?? 1800),
        thumb_max_width: Number(res.data?.config?.thumb_max_width ?? 520),
      });
      setWatermarkLogoUrl(res.data?.logo_url || null);
    } catch (e) {
      setWatermarkError(e.response?.data?.detail || 'Watermark ayarları yüklenemedi');
    } finally {
      setWatermarkLoading(false);
    }
  };

  const fetchWatermarkPreview = async () => {
    try {
      const res = await axios.get(`${API}/admin/media/watermark/preview`, {
        headers: authHeader,
        responseType: 'blob',
      });
      const previewObjectUrl = URL.createObjectURL(res.data);
      setWatermarkPreviewUrl((prev) => {
        if (prev) URL.revokeObjectURL(prev);
        return previewObjectUrl;
      });
    } catch {
      setWatermarkPreviewUrl(null);
    }
  };

  const fetchWatermarkPerf = async () => {
    try {
      const res = await axios.get(`${API}/admin/media/pipeline/performance`, { headers: authHeader });
      setWatermarkPerf(res.data?.summary || null);
    } catch {
      setWatermarkPerf(null);
    }
  };

  const handleSaveWatermarkSettings = async () => {
    setWatermarkSaving(true);
    setWatermarkError('');
    try {
      await axios.patch(`${API}/admin/media/watermark/settings`, watermarkConfig, { headers: authHeader });
      toast({ title: 'Watermark ayarları kaydedildi' });
      await fetchWatermarkSettings();
      await fetchWatermarkPreview();
      await fetchWatermarkPerf();
    } catch (e) {
      setWatermarkError(e.response?.data?.detail || 'Watermark ayarları kaydedilemedi');
    } finally {
      setWatermarkSaving(false);
    }
  };

  const handleSaveCloudflare = async () => {
    if (!encryptionKeyPresent) {
      setCloudflareError('Kaydedilemedi: Güvenlik anahtarı eksik.');
      return;
    }
    if (!cloudflareForm.account_id || !cloudflareForm.zone_id) {
      setCloudflareError('Account ID ve Zone ID zorunludur');
      return;
    }
    setCloudflareSaving(true);
    setCloudflareError('');
    try {
      const res = await axios.post(
        `${API}/admin/system-settings/cloudflare`,
        {
          account_id: cloudflareForm.account_id,
          zone_id: cloudflareForm.zone_id,
        },
        { headers: authHeader }
      );
      toast({
        title: 'Cloudflare IDs Saved',
        description: `Canary: ${res.data?.canary_status || 'UNKNOWN'}`,
      });
      setCloudflareForm({ account_id: '', zone_id: '' });
      fetchCloudflareConfig();
      fetchHealthDetail();
    } catch (e) {
      const detail = e.response?.data?.detail || 'Kaydedilemedi';
      if (detail.includes('CONFIG_ENCRYPTION_KEY')) {
        setCloudflareError('Kaydedilemedi: Güvenlik anahtarı eksik.');
      } else {
        setCloudflareError(detail);
      }
    } finally {
      setCloudflareSaving(false);
    }
  };

  const handleCloudflareCanary = async () => {
    setCanaryLoading(true);
    setCloudflareError('');
    try {
      const res = await axios.post(`${API}/admin/system-settings/cloudflare/canary`, {}, { headers: authHeader });
      const status = res.data?.status || 'UNKNOWN';
      setCloudflareConfig((prev) => ({
        ...prev,
        canary_status: status,
        canary_checked_at: new Date().toISOString(),
      }));
    } catch (e) {
      const detail = e.response?.data?.detail || 'Canary başarısız';
      setCloudflareError(detail);
    } finally {
      setCanaryLoading(false);
    }
  };

  const openCreate = () => {
    setEditing(null);
    setForm({ key: '', value: '', country_code: '', is_readonly: false, description: '' });
    setError(null);
    setModalOpen(true);
  };

  const openEdit = (item) => {
    setEditing(item);
    setForm({
      key: item.key,
      value: formatValue(item.value),
      country_code: item.country_code || '',
      is_readonly: item.is_readonly || false,
      description: item.description || '',
    });
    setError(null);
    setModalOpen(true);
  };

  const submitForm = async () => {
    if (!form.key || form.value === '') {
      setError('Key ve value zorunlu');
      return;
    }
    try {
      if (editing) {
        await axios.patch(
          `${API}/admin/system-settings/${editing.id}`,
          {
            value: parseValue(form.value),
            country_code: form.country_code || null,
            is_readonly: form.is_readonly,
            description: form.description || null,
          },
          { headers: authHeader }
        );
      } else {
        await axios.post(
          `${API}/admin/system-settings`,
          {
            key: form.key,
            value: parseValue(form.value),
            country_code: form.country_code || null,
            is_readonly: form.is_readonly,
            description: form.description || null,
          },
          { headers: authHeader }
        );
      }
      setModalOpen(false);
      fetchSettings();
    } catch (e) {
      setError(e.response?.data?.detail || 'Kaydedilemedi');
    }
  };

  const toggleModerationFreeze = async () => {
    if (!isSuperAdmin || freezeSaving) return;
    const nextValue = !freezeActive;
    const reasonPayload = freezeReason.trim() ? freezeReason.trim() : null;
    setFreezeSaving(true);
    setError('');
    try {
      if (freezeSetting) {
        await axios.patch(
          `${API}/admin/system-settings/${freezeSetting.id}`,
          {
            value: { enabled: nextValue },
            description: freezeSetting.description || 'Moderation freeze flag',
            moderation_freeze_reason: reasonPayload,
          },
          { headers: authHeader }
        );
      } else {
        await axios.post(
          `${API}/admin/system-settings`,
          {
            key: MODERATION_FREEZE_KEY,
            value: { enabled: nextValue },
            country_code: null,
            is_readonly: false,
            description: 'Moderation freeze flag',
            moderation_freeze_reason: reasonPayload,
          },
          { headers: authHeader }
        );
      }
      await fetchSettings();
    } catch (e) {
      setError(e.response?.data?.detail || 'Moderation freeze güncellenemedi');
    } finally {
      setFreezeSaving(false);
    }
  };

  useEffect(() => {
    fetchSettings();
    fetchCloudflareConfig();
    fetchHealthDetail();
    fetchMeiliActiveConfig();
    fetchMeiliHistory();
    fetchWatermarkSettings();
    fetchWatermarkPreview();
    fetchWatermarkPerf();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterCountry]);

  useEffect(() => {
    return () => {
      if (watermarkPreviewUrl) {
        URL.revokeObjectURL(watermarkPreviewUrl);
      }
    };
  }, [watermarkPreviewUrl]);

  useEffect(() => {
    const setting = items.find((item) => item.key === MODERATION_FREEZE_KEY && !item.country_code);
    setFreezeSetting(setting || null);
    setFreezeActive(resolveFreezeValue(setting));
    setFreezeReason(setting?.moderation_freeze_reason || '');
  }, [items]);

  const canaryStatusRaw = cloudflareConfig.canary_status || 'UNKNOWN';
  const canaryReason = useMemo(() => {
    if (canaryStatusRaw === 'CONFIG_MISSING') {
      return configMissingReason || 'config_missing';
    }
    if (canaryStatusRaw === 'SCOPE_ERROR') {
      return 'scope_error';
    }
    if (canaryStatusRaw === 'API_ERROR') {
      return 'api_error';
    }
    return 'none';
  }, [canaryStatusRaw, configMissingReason]);

  const statusInfo = useMemo(() => {
    const technical = `CONFIG_ENCRYPTION_KEY=${encryptionKeyPresent ? 'present' : 'missing'} | cf_metrics_enabled=${cfMetricsEnabled ? 'true' : 'false'} | cf_ids_present=${cloudflareConfig.cf_ids_present ? 'true' : 'false'} | cf_ids_source=${cloudflareConfig.cf_ids_source || 'none'} | canary_status=${canaryStatusRaw} | config_missing_reason=${configMissingReason || 'none'}`;
    if (!encryptionKeyPresent) {
      return {
        tone: 'error',
        title: '🔒 Güvenlik anahtarı tanımlı değil. Bu nedenle Cloudflare bilgileri kaydedilemez. (CONFIG_ENCRYPTION_KEY)',
        subtitle: 'Lütfen sistem yöneticinizden bu anahtarı ortam değişkeni/secret olarak eklemesini isteyin.',
        tooltip: technical,
      };
    }
    if (!cfMetricsEnabled) {
      return {
        tone: 'warning',
        title: 'Cloudflare metrikleri şu an kapalı.',
        subtitle: 'CDN metrikleri görüntülenmeyecek.',
        tooltip: technical,
      };
    }
    if (!cloudflareConfig.cf_ids_present) {
      return {
        tone: 'warning',
        title: 'Cloudflare bilgileri eksik.',
        subtitle: 'Account ve Zone ID girilmelidir.',
        tooltip: technical,
      };
    }
    if (['API_ERROR', 'SCOPE_ERROR'].includes(canaryStatusRaw)) {
      return {
        tone: 'error',
        title: 'Bağlantı testi yapılamadı.',
        subtitle: 'Lütfen canary testini tekrar deneyin.',
        tooltip: technical,
      };
    }
    if (cloudflareError) {
      return {
        tone: 'error',
        title: cloudflareError,
        subtitle: '',
        tooltip: technical,
      };
    }
    return {
      tone: 'success',
      title: 'Cloudflare yapılandırması hazır.',
      subtitle: '',
      tooltip: technical,
    };
  }, [encryptionKeyPresent, cfMetricsEnabled, cloudflareConfig, canaryStatusRaw, configMissingReason, cloudflareError]);

  const canaryUserText = canaryStatusRaw === 'OK' ? 'Başarılı' : 'Bağlantı testi yapılamadı';
  const meiliHealthInfo = healthDetail?.meili || null;
  const meiliConnected = Boolean(meiliHealthInfo?.connected);
  const statusToneClass = {
    error: 'border-rose-200 bg-rose-50 text-rose-700',
    warning: 'border-amber-200 bg-amber-50 text-amber-700',
    success: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    info: 'border-slate-200 bg-slate-50 text-slate-700',
  };

  const filteredItems = items.filter((item) =>
    item.key.toLowerCase().includes(filterKey.toLowerCase())
  );

  const meiliStatusTone = meiliActiveConfig?.status === 'active' ? 'success' : 'warning';
  const meiliLastTest = meiliActiveConfig?.last_test_result;

  return (
    <div className="space-y-6" data-testid="admin-system-settings-page">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold" data-testid="system-settings-title">System Settings</h1>
          <div className="text-xs text-muted-foreground">Key namespace: domain.section.key</div>
        </div>
        <button
          onClick={openCreate}
          className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
          data-testid="system-settings-create-open"
        >
          Yeni Setting
        </button>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-3" data-testid="system-settings-cloudflare-card">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold" data-testid="system-settings-cloudflare-title">Cloudflare (CDN & Analytics)</h2>
            <div className="text-xs text-muted-foreground" data-testid="system-settings-cloudflare-subtitle">
              Account/Zone ID sadece masked olarak görüntülenir.
            </div>
          </div>
          <div className="text-xs text-slate-500" data-testid="system-settings-cloudflare-source">
            Source: {cloudflareConfig.cf_ids_source || 'unknown'} · Present: {cloudflareConfig.cf_ids_present ? 'true' : 'false'}
          </div>
        </div>

        <div
          className={`rounded-md border px-3 py-2 text-xs ${statusToneClass[statusInfo.tone]}`}
          data-testid="system-settings-cloudflare-status"
          title={statusInfo.tooltip}
        >
          <div className="font-semibold" data-testid="system-settings-cloudflare-status-title">Durum: {statusInfo.title}</div>
          {statusInfo.subtitle && (
            <div className="text-[11px]" data-testid="system-settings-cloudflare-status-subtitle">{statusInfo.subtitle}</div>
          )}
        </div>

        {cloudflareLoading ? (
          <div className="text-xs text-muted-foreground" data-testid="system-settings-cloudflare-loading">Yükleniyor…</div>
        ) : (
          <>
            <div className="grid gap-4 md:grid-cols-2" data-testid="system-settings-cloudflare-inputs">
              <div className="space-y-1">
                <label className="text-xs text-slate-600" data-testid="system-settings-cloudflare-account-label">Cloudflare Account ID</label>
                <input
                  type="password"
                  value={cloudflareForm.account_id}
                  onChange={(e) => setCloudflareForm((prev) => ({ ...prev, account_id: e.target.value }))}
                  placeholder={cloudflareConfig.account_id_masked || '••••'}
                  className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                  disabled={!isSuperAdmin || cloudflareSaving}
                  data-testid="system-settings-cloudflare-account-input"
                />
                <div className="text-[11px] text-slate-500" data-testid="system-settings-cloudflare-account-hint">
                  Mevcut: {cloudflareConfig.account_id_masked || '—'}
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-slate-600" data-testid="system-settings-cloudflare-zone-label">Cloudflare Zone ID</label>
                <input
                  type="password"
                  value={cloudflareForm.zone_id}
                  onChange={(e) => setCloudflareForm((prev) => ({ ...prev, zone_id: e.target.value }))}
                  placeholder={cloudflareConfig.zone_id_masked || '••••'}
                  className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                  disabled={!isSuperAdmin || cloudflareSaving}
                  data-testid="system-settings-cloudflare-zone-input"
                />
                <div className="text-[11px] text-slate-500" data-testid="system-settings-cloudflare-zone-hint">
                  Mevcut: {cloudflareConfig.zone_id_masked || '—'}
                </div>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3" data-testid="system-settings-cloudflare-actions">
              <button
                onClick={handleSaveCloudflare}
                className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
                disabled={!isSuperAdmin || cloudflareSaving || !encryptionKeyPresent}
                title={!encryptionKeyPresent ? 'Önce güvenlik anahtarı tanımlanmalı.' : undefined}
                data-testid="system-settings-cloudflare-save"
              >
                {cloudflareSaving ? 'Kaydediliyor…' : 'Kaydet'}
              </button>
              <button
                onClick={handleCloudflareCanary}
                className="h-9 px-3 rounded-md border text-sm"
                disabled={!isSuperAdmin || canaryLoading || !encryptionKeyPresent}
                title={!encryptionKeyPresent ? 'Önce güvenlik anahtarı tanımlanmalı.' : undefined}
                data-testid="system-settings-cloudflare-canary"
              >
                {canaryLoading ? 'Test Ediliyor…' : 'Test Connection (Canary)'}
              </button>
              {!isSuperAdmin && (
                <span className="text-xs text-amber-600" data-testid="system-settings-cloudflare-permission">
                  Sadece super_admin düzenleyebilir.
                </span>
              )}
            </div>

            <div className="text-xs text-slate-600" data-testid="system-settings-cloudflare-canary-status">
              Bağlantı testi: <span className={canaryStatusRaw === 'OK' ? 'text-emerald-600' : 'text-rose-600'}>{canaryUserText}</span>
            </div>
            <details className="text-[11px] text-slate-500" data-testid="system-settings-cloudflare-canary-details">
              <summary className="cursor-pointer">Detaylar</summary>
              <div className="mt-1">canary_status: {canaryStatusRaw}</div>
              <div>reason: {canaryReason}</div>
              <div>cf_ids_source: {cloudflareConfig.cf_ids_source || '-'}</div>
            </details>
          </>
        )}


      </div>

      {isSystemAdmin && (
        <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="system-settings-meili-card">
          <div className="flex items-start justify-between gap-3 flex-wrap">
            <div>
              <h2 className="text-lg font-semibold" data-testid="system-settings-meili-title">Search / Meilisearch</h2>
              <div className="text-xs text-muted-foreground" data-testid="system-settings-meili-subtitle">
                Manuel konfig + versiyonlu geçmiş. Master key hiçbir zaman geri gösterilmez.
              </div>
            </div>
            <div
              className={`rounded-md border px-3 py-2 text-xs ${statusToneClass[meiliStatusTone]}`}
              data-testid="system-settings-meili-active-status"
            >
              Aktif Durum: {meiliActiveConfig?.status || 'inactive'}
            </div>
          </div>

          <div className="text-xs text-slate-600" data-testid="system-settings-meili-health-status">
            Admin Health: <span className={meiliConnected ? 'text-emerald-600' : 'text-rose-600'}>{meiliConnected ? 'connected' : (meiliHealthInfo?.status || 'not_configured')}</span>
          </div>

          {!meiliEncryptionKeyPresent && (
            <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700" data-testid="system-settings-meili-encryption-warning">
              CONFIG_ENCRYPTION_KEY eksik. Konfig kaydetme/aktive etme kapalı.
            </div>
          )}

          <div className="flex gap-2" data-testid="system-settings-meili-tabs">
            <button
              onClick={() => setMeiliTab('active')}
              className={`h-8 px-3 rounded-md text-xs border ${meiliTab === 'active' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-700'}`}
              data-testid="system-settings-meili-tab-active"
            >
              Aktif Konfig
            </button>
            <button
              onClick={() => setMeiliTab('history')}
              className={`h-8 px-3 rounded-md text-xs border ${meiliTab === 'history' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-700'}`}
              data-testid="system-settings-meili-tab-history"
            >
              Geçmiş
            </button>
          </div>

          {meiliLoading ? (
            <div className="text-xs text-muted-foreground" data-testid="system-settings-meili-loading">Yükleniyor…</div>
          ) : meiliTab === 'active' ? (
            <div className="space-y-4" data-testid="system-settings-meili-active-panel">
              <div className="rounded-md border bg-slate-50 px-3 py-3 text-xs space-y-1" data-testid="system-settings-meili-active-summary">
                <div data-testid="system-settings-meili-active-id">Config ID: {meiliActiveConfig?.id || 'Yok'}</div>
                <div data-testid="system-settings-meili-active-url">URL: {meiliActiveConfig?.meili_url || 'Yok'}</div>
                <div data-testid="system-settings-meili-active-index">Index: {meiliActiveConfig?.meili_index_name || DEFAULT_MEILI_INDEX_NAME}</div>
                <div data-testid="system-settings-meili-active-last-test">
                  Son Test: {meiliLastTest?.status || 'N/A'} · {meiliLastTest?.reason_code || 'none'}
                </div>
              </div>

              <div className="grid gap-3 md:grid-cols-3" data-testid="system-settings-meili-form-grid">
                <div className="space-y-1">
                  <label className="text-xs text-slate-600" data-testid="system-settings-meili-url-label">Meili URL</label>
                  <input
                    value={meiliForm.meili_url}
                    onChange={(e) => setMeiliForm((prev) => ({ ...prev, meili_url: e.target.value }))}
                    placeholder="https://your-meili-host"
                    className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                    data-testid="system-settings-meili-url-input"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-600" data-testid="system-settings-meili-index-label">Index Name</label>
                  <input
                    value={meiliForm.meili_index_name}
                    onChange={(e) => setMeiliForm((prev) => ({ ...prev, meili_index_name: e.target.value }))}
                    placeholder={DEFAULT_MEILI_INDEX_NAME}
                    className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                    data-testid="system-settings-meili-index-input"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-slate-600" data-testid="system-settings-meili-key-label">Master Key</label>
                  <input
                    type="password"
                    value={meiliForm.meili_master_key}
                    onChange={(e) => setMeiliForm((prev) => ({ ...prev, meili_master_key: e.target.value }))}
                    placeholder="••••"
                    className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                    data-testid="system-settings-meili-key-input"
                  />
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2" data-testid="system-settings-meili-actions">
                <button
                  onClick={handleSaveMeiliConfig}
                  className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
                  disabled={meiliSaving || !meiliEncryptionKeyPresent}
                  title={!meiliEncryptionKeyPresent ? 'Önce güvenlik anahtarı tanımlanmalı.' : undefined}
                  data-testid="system-settings-meili-save"
                >
                  {meiliSaving ? 'Kaydediliyor…' : 'Kaydet (inactive)'}
                </button>

                <button
                  onClick={() => handleActivateMeiliConfig(meiliLatestConfigId || meiliActiveConfig?.id)}
                  className="h-9 px-3 rounded-md border text-sm"
                  disabled={meiliActivatingId !== null || !(meiliLatestConfigId || meiliActiveConfig?.id) || !meiliEncryptionKeyPresent}
                  title={!meiliEncryptionKeyPresent ? 'Önce güvenlik anahtarı tanımlanmalı.' : undefined}
                  data-testid="system-settings-meili-test-activate"
                >
                  {meiliActivatingId ? 'Test + Aktivasyon…' : 'Test PASS ile Aktif Et'}
                </button>

                {(meiliLatestConfigId || meiliActiveConfig?.id) && (
                  <button
                    onClick={() => handleTestMeiliConfig(meiliLatestConfigId || meiliActiveConfig?.id)}
                    className="h-9 px-3 rounded-md border text-sm"
                    disabled={meiliTestingId !== null}
                    data-testid="system-settings-meili-test-only"
                  >
                    {meiliTestingId ? 'Test Ediliyor…' : 'Sadece Test Et'}
                  </button>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-2" data-testid="system-settings-meili-history-panel">
              {meiliHistory.length === 0 ? (
                <div className="text-xs text-muted-foreground" data-testid="system-settings-meili-history-empty">Geçmiş kayıt yok</div>
              ) : (
                meiliHistory.map((item) => (
                  <div key={item.id} className="rounded-md border p-3 space-y-2" data-testid={`system-settings-meili-history-row-${item.id}`}>
                    <div className="grid gap-2 md:grid-cols-3 text-xs">
                      <div data-testid={`system-settings-meili-history-url-${item.id}`}>URL: {item.meili_url}</div>
                      <div data-testid={`system-settings-meili-history-index-${item.id}`}>Index: {item.meili_index_name}</div>
                      <div data-testid={`system-settings-meili-history-status-${item.id}`}>Status: {item.status}</div>
                      <div data-testid={`system-settings-meili-history-key-${item.id}`}>Key: {item.master_key_masked || '••••'}</div>
                      <div data-testid={`system-settings-meili-history-test-result-${item.id}`}>
                        Test: {item.last_test_result?.status || 'N/A'} ({item.last_test_result?.reason_code || 'none'})
                      </div>
                      <div data-testid={`system-settings-meili-history-created-${item.id}`}>Created: {item.created_at || '-'}</div>
                    </div>
                    <div className="flex flex-wrap items-center gap-2" data-testid={`system-settings-meili-history-actions-${item.id}`}>
                      <button
                        onClick={() => handleActivateMeiliConfig(item.id)}
                        className="h-8 px-2.5 rounded-md border text-xs"
                        disabled={meiliActivatingId !== null || item.status === 'revoked'}
                        data-testid={`system-settings-meili-history-activate-${item.id}`}
                      >
                        Bu konfigi tekrar aktif et
                      </button>
                      <button
                        onClick={() => handleTestMeiliConfig(item.id)}
                        className="h-8 px-2.5 rounded-md border text-xs"
                        disabled={meiliTestingId !== null || item.status === 'revoked'}
                        data-testid={`system-settings-meili-history-test-${item.id}`}
                      >
                        Test
                      </button>
                      <button
                        onClick={() => handleRevokeMeiliConfig(item.id)}
                        className="h-8 px-2.5 rounded-md border text-xs"
                        disabled={meiliRevokingId !== null || item.status === 'revoked'}
                        data-testid={`system-settings-meili-history-revoke-${item.id}`}
                      >
                        {meiliRevokingId === item.id ? 'Revoke…' : 'Revoke'}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {meiliError && (
            <div className="text-xs text-rose-600" data-testid="system-settings-meili-error">{meiliError}</div>
          )}
          {meiliNotice && (
            <div className="text-xs text-emerald-700" data-testid="system-settings-meili-notice">{meiliNotice}</div>
          )}
        </div>
      )}

      <div className="rounded-lg border bg-white p-4 space-y-3" data-testid="system-settings-moderation-freeze-card">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold" data-testid="system-settings-moderation-freeze-title">Moderation Freeze Modu</h2>
            <div className="text-xs text-muted-foreground" data-testid="system-settings-moderation-freeze-subtitle">
              Bu mod aktifken moderasyon işlemleri (onay/red) kilitlenir. Yalnızca görüntüleme yapılabilir.
            </div>
            <div className="text-[11px] text-slate-500 mt-1" data-testid="system-settings-moderation-freeze-note">
              Planlı bakım veya veri dondurma süreçlerinde kullanılır.
            </div>
          </div>
          <div
            className={`text-xs font-semibold px-2 py-1 rounded-full ${freezeActive ? 'bg-amber-100 text-amber-700' : 'bg-emerald-100 text-emerald-700'}`}
            data-testid="system-settings-moderation-freeze-status"
          >
            {freezeActive ? 'Freeze Aktif' : 'Freeze Kapalı'}
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={toggleModerationFreeze}
            disabled={!isSuperAdmin || freezeSaving}
            className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm disabled:opacity-50"
            data-testid="system-settings-moderation-freeze-toggle"
          >
            {freezeSaving ? 'Kaydediliyor…' : freezeActive ? 'Freeze Kapat' : 'Freeze Aç'}
          </button>
          <div className="text-xs text-muted-foreground" data-testid="system-settings-moderation-freeze-key">
            Key: {MODERATION_FREEZE_KEY}
          </div>
          {!isSuperAdmin && (
            <span className="text-xs text-amber-600" data-testid="system-settings-moderation-freeze-permission">
              Sadece super_admin düzenleyebilir.
            </span>
          )}
        </div>

        <div className="space-y-2" data-testid="system-settings-moderation-freeze-reason">
          <label className="text-xs font-medium text-slate-700" data-testid="system-settings-moderation-freeze-reason-label">
            Freeze Reason (opsiyonel)
          </label>
          <input
            value={freezeReason}
            onChange={(e) => setFreezeReason(e.target.value)}
            placeholder="Örn: Planlı bakım / veri doğrulama"
            className="h-9 w-full rounded-md border bg-background px-3 text-sm"
            disabled={!isSuperAdmin || freezeSaving}
            data-testid="system-settings-moderation-freeze-reason-input"
          />
          <div className="text-[11px] text-slate-500" data-testid="system-settings-moderation-freeze-reason-hint">
            Hassas bilgi yazmayın. Kısa ve açıklayıcı bir not yeterlidir.
          </div>
        </div>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="system-settings-watermark-card">
        <div className="flex items-start justify-between gap-3 flex-wrap">
          <div>
            <h2 className="text-lg font-semibold" data-testid="system-settings-watermark-title">Watermark & Image Pipeline</h2>
            <div className="text-xs text-muted-foreground" data-testid="system-settings-watermark-subtitle">
              Key: {WATERMARK_PIPELINE_KEY} · Orijinal private, public türevlerde watermark.
            </div>
          </div>
          <div className={`text-xs font-semibold px-2 py-1 rounded-full ${watermarkConfig.enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-700'}`} data-testid="system-settings-watermark-status">
            {watermarkConfig.enabled ? 'Watermark Açık' : 'Watermark Kapalı'}
          </div>
        </div>

        {watermarkLoading ? (
          <div className="text-xs text-muted-foreground" data-testid="system-settings-watermark-loading">Yükleniyor…</div>
        ) : (
          <>
            <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3" data-testid="system-settings-watermark-form-grid">
              <label className="flex items-center gap-2 text-sm" data-testid="system-settings-watermark-enabled-wrap">
                <input
                  type="checkbox"
                  checked={Boolean(watermarkConfig.enabled)}
                  onChange={(e) => setWatermarkConfig((prev) => ({ ...prev, enabled: e.target.checked }))}
                  data-testid="system-settings-watermark-enabled"
                />
                Watermark aktif
              </label>

              <div className="space-y-1">
                <label className="text-xs text-slate-600" data-testid="system-settings-watermark-position-label">Pozisyon</label>
                <select
                  className="h-9 w-full rounded-md border px-3 text-sm"
                  value={watermarkConfig.position}
                  onChange={(e) => setWatermarkConfig((prev) => ({ ...prev, position: e.target.value }))}
                  data-testid="system-settings-watermark-position"
                >
                  <option value="bottom_right">bottom_right</option>
                  <option value="bottom_left">bottom_left</option>
                  <option value="top_right">top_right</option>
                  <option value="top_left">top_left</option>
                  <option value="center">center</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-xs text-slate-600" data-testid="system-settings-watermark-opacity-label">Opacity: {Number(watermarkConfig.opacity || 0).toFixed(2)}</label>
                <input
                  type="range"
                  min="0.05"
                  max="0.95"
                  step="0.05"
                  value={watermarkConfig.opacity}
                  onChange={(e) => setWatermarkConfig((prev) => ({ ...prev, opacity: Number(e.target.value) }))}
                  className="w-full"
                  data-testid="system-settings-watermark-opacity"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-slate-600" data-testid="system-settings-watermark-web-width-label">Web max width</label>
                <input
                  type="number"
                  min="800"
                  max="3000"
                  value={watermarkConfig.web_max_width}
                  onChange={(e) => setWatermarkConfig((prev) => ({ ...prev, web_max_width: Number(e.target.value) }))}
                  className="h-9 w-full rounded-md border px-3 text-sm"
                  data-testid="system-settings-watermark-web-width"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-slate-600" data-testid="system-settings-watermark-thumb-width-label">Thumbnail width</label>
                <input
                  type="number"
                  min="200"
                  max="1200"
                  value={watermarkConfig.thumb_max_width}
                  onChange={(e) => setWatermarkConfig((prev) => ({ ...prev, thumb_max_width: Number(e.target.value) }))}
                  className="h-9 w-full rounded-md border px-3 text-sm"
                  data-testid="system-settings-watermark-thumb-width"
                />
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2" data-testid="system-settings-watermark-actions">
              <button
                onClick={handleSaveWatermarkSettings}
                disabled={watermarkSaving}
                className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
                data-testid="system-settings-watermark-save"
              >
                {watermarkSaving ? 'Kaydediliyor…' : 'Kaydet'}
              </button>
              <button
                onClick={() => { fetchWatermarkPreview(); fetchWatermarkPerf(); }}
                className="h-9 px-3 rounded-md border text-sm"
                data-testid="system-settings-watermark-refresh-preview"
              >
                Preview Yenile
              </button>
              {watermarkLogoUrl && (
                <a href={watermarkLogoUrl} target="_blank" rel="noreferrer" className="text-xs underline text-primary" data-testid="system-settings-watermark-logo-link">
                  Marka logosunu aç
                </a>
              )}
            </div>

            <div className="grid gap-4 md:grid-cols-2" data-testid="system-settings-watermark-preview-grid">
              <div className="rounded-md border p-3 space-y-2" data-testid="system-settings-watermark-preview-card">
                <div className="text-xs text-muted-foreground" data-testid="system-settings-watermark-preview-title">Preview</div>
                {watermarkPreviewUrl ? (
                  <img src={watermarkPreviewUrl} alt="Watermark preview" className="w-full rounded border object-contain" data-testid="system-settings-watermark-preview-image" />
                ) : (
                  <div className="text-xs text-muted-foreground" data-testid="system-settings-watermark-preview-empty">Preview görseli yok</div>
                )}
              </div>

              <div className="rounded-md border p-3 space-y-2" data-testid="system-settings-watermark-performance-card">
                <div className="text-xs text-muted-foreground" data-testid="system-settings-watermark-performance-title">Performans Özeti</div>
                <div className="text-sm" data-testid="system-settings-watermark-performance-sample">Örnek sayısı: {watermarkPerf?.sample_count ?? 0}</div>
                <div className="text-sm" data-testid="system-settings-watermark-performance-avg-ms">Ortalama işleme: {watermarkPerf?.average_processing_ms ?? 0} ms</div>
                <div className="text-sm" data-testid="system-settings-watermark-performance-ratio">Boyut düşüş oranı: {watermarkPerf?.average_reduction_ratio ?? 0}%</div>
              </div>
            </div>

            {watermarkError && (
              <div className="text-xs text-rose-600" data-testid="system-settings-watermark-error">{watermarkError}</div>
            )}
          </>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3" data-testid="system-settings-filters">
        <input
          value={filterKey}
          onChange={(e) => setFilterKey(e.target.value)}
          placeholder="Key ara"
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="system-settings-filter-key"
        />
        <input
          value={filterCountry}
          onChange={(e) => setFilterCountry(e.target.value)}
          placeholder="Country (opsiyonel)"
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="system-settings-filter-country"
        />
      </div>

      <div className="rounded-md border bg-card overflow-hidden" data-testid="system-settings-table">
        <div className="hidden lg:grid grid-cols-[1.6fr_1.2fr_0.8fr_0.6fr_1.2fr_0.6fr] gap-4 bg-muted px-4 py-3 text-sm font-medium">
          <div>Key</div>
          <div>Value</div>
          <div>Country</div>
          <div>Readonly</div>
          <div>Description</div>
          <div className="text-right">Aksiyon</div>
        </div>
        <div className="divide-y">
          {loading ? (
            <div className="p-6 text-center" data-testid="system-settings-loading">Yükleniyor…</div>
          ) : filteredItems.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground" data-testid="system-settings-empty">Kayıt yok</div>
          ) : (
            filteredItems.map((item) => (
              <div
                key={item.id}
                className="grid grid-cols-1 gap-4 px-4 py-4 lg:grid-cols-[1.6fr_1.2fr_0.8fr_0.6fr_1.2fr_0.6fr]"
                data-testid={`system-setting-row-${item.id}`}
              >
                <div className="font-medium">{item.key}</div>
                <div className="text-xs text-muted-foreground break-all">{formatValue(item.value)}</div>
                <div>{item.country_code || 'global'}</div>
                <div>{item.is_readonly ? 'yes' : 'no'}</div>
                <div className="text-xs text-muted-foreground">{item.description || '—'}</div>
                <div className="flex justify-end">
                  <button
                    onClick={() => openEdit(item)}
                    className="h-8 px-2.5 rounded-md border text-xs"
                    data-testid={`system-setting-edit-${item.id}`}
                  >
                    Düzenle
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {modalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="system-settings-modal">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-xl">
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="text-lg font-semibold" data-testid="system-settings-modal-title">{editing ? 'Setting Güncelle' : 'Setting Oluştur'}</h3>
              <button
                onClick={() => setModalOpen(false)}
                className="h-8 px-2.5 rounded-md border text-xs"
                data-testid="system-settings-modal-close"
              >
                Kapat
              </button>
            </div>
            <div className="p-4 space-y-3">
              <input
                value={form.key}
                onChange={(e) => setForm({ ...form, key: e.target.value })}
                placeholder="Key (domain.section.key)"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                disabled={!!editing}
                data-testid="system-settings-form-key"
              />
              <textarea
                value={form.value}
                onChange={(e) => setForm({ ...form, value: e.target.value })}
                placeholder="Value (string veya JSON)"
                className="w-full min-h-[90px] p-3 rounded-md border bg-background text-sm"
                data-testid="system-settings-form-value"
              />
              <input
                value={form.country_code}
                onChange={(e) => setForm({ ...form, country_code: e.target.value.toUpperCase() })}
                placeholder="Country Code (opsiyonel)"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="system-settings-form-country"
              />
              <input
                value={form.description}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                placeholder="Description"
                className="h-9 px-3 rounded-md border bg-background text-sm w-full"
                data-testid="system-settings-form-description"
              />
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.is_readonly}
                  onChange={(e) => setForm({ ...form, is_readonly: e.target.checked })}
                  data-testid="system-settings-form-readonly"
                />
                Readonly
              </label>
              {error && (
                <div className="text-xs text-destructive" data-testid="system-settings-form-error">{error}</div>
              )}
              <button
                onClick={submitForm}
                className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
                data-testid="system-settings-form-submit"
              >
                {editing ? 'Güncelle' : 'Oluştur'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
