import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { useToast } from '@/components/ui/toaster';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const MODERATION_FREEZE_KEY = 'moderation.freeze.active';

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
      setEncryptionKeyPresent(Boolean(res.data?.encryption_key_present));
      setCfMetricsEnabled(Boolean(res.data?.cf_metrics_enabled));
      setConfigMissingReason(res.data?.config_missing_reason || '');
    } catch (e) {
      setEncryptionKeyPresent(false);
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterCountry]);

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
  const statusToneClass = {
    error: 'border-rose-200 bg-rose-50 text-rose-700',
    warning: 'border-amber-200 bg-amber-50 text-amber-700',
    success: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    info: 'border-slate-200 bg-slate-50 text-slate-700',
  };

  const filteredItems = items.filter((item) =>
    item.key.toLowerCase().includes(filterKey.toLowerCase())
  );

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
