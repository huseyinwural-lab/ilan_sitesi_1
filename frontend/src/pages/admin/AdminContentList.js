import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useTranslation } from 'react-i18next';
import { toast } from 'sonner';
import { ConfirmModal } from '@/components/ConfirmModal';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PAGE_TYPE_LABEL_MAP = {
  home: 'Ana Sayfa',
  category_l0_l1: 'L0/L1 Kategori Sayfası',
  search_ln: 'Kategori İlan Listesi',
  urgent_listings: 'Acil İlanlar',
  category_showcase: 'Kategori Vitrin',
  listing_detail: 'İlan Detay',
  listing_detail_parameters: 'İlan Detay Parametreleri',
  storefront_profile: 'Mağaza/Kurumsal Profil',
  wizard_step_l0: 'İlan Ver Adım 1 - L0',
  wizard_step_ln: 'İlan Ver Adım 2 - L1>Ln',
  wizard_step_form: 'İlan Ver Adım 3 - Form',
  wizard_preview: 'Ön İzleme',
  wizard_doping_payment: 'Doping ve Ödeme',
  wizard_result: 'Başarı/Sonuç',
  user_dashboard: 'Kullanıcı Paneli',
  search_l1: 'Legacy Search L1',
  search_l2: 'Legacy Search L2',
  listing_create_stepX: 'Legacy İlan Ver',
};

const PAGE_TYPE_OPTIONS = [
  'home',
  'category_l0_l1',
  'search_ln',
  'urgent_listings',
  'category_showcase',
  'listing_detail',
  'listing_detail_parameters',
  'storefront_profile',
  'wizard_step_l0',
  'wizard_step_ln',
  'wizard_step_form',
  'wizard_preview',
  'wizard_doping_payment',
  'wizard_result',
  'user_dashboard',
  'search_l1',
  'search_l2',
  'listing_create_stepX',
].map((value) => ({ value, label: `${PAGE_TYPE_LABEL_MAP[value] || value} (${value})` }));

const CONTENT_LIST_STATUS_FILTER = ['draft', 'published'];

const formatLayoutUpdatedAt = (value) => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  return date.toLocaleString('tr-TR');
};

const resolveLayoutScopeLabel = (item) => {
  if (!item || typeof item !== 'object') return '-';
  if (item.category_id) return `Kategori: ${item.category_id}`;
  return item.scope || `${item.country || '-'} / ${item.module || '-'} / global`;
};

const parseCountriesInput = (value) => (
  String(value || '')
    .split(',')
    .map((token) => token.trim().toUpperCase())
    .filter(Boolean)
);

const normalizeErrorText = (value, fallback = 'Beklenmeyen bir hata oluştu') => {
  if (typeof value === 'string' && value.trim()) return value;
  if (Array.isArray(value)) {
    const merged = value.map((item) => normalizeErrorText(item, '')).filter(Boolean).join(' | ');
    return merged || fallback;
  }
  if (value && typeof value === 'object') {
    if (typeof value.message === 'string' && value.message.trim()) return value.message;
    if (typeof value.detail === 'string' && value.detail.trim()) return value.detail;
    if (typeof value.code === 'string' && value.code.trim()) {
      const blocked = Array.isArray(value.blocked_keys) ? ` blocked_keys=${value.blocked_keys.join(', ')}` : '';
      const keys = Array.isArray(value.keys) ? ` keys=${value.keys.join(', ')}` : '';
      return `${value.code}${blocked}${keys}`.trim();
    }
    try {
      return JSON.stringify(value);
    } catch {
      return fallback;
    }
  }
  return fallback;
};

const extractApiErrorText = (error, fallback) => {
  const responseData = error?.response?.data;
  const detail = responseData?.detail;
  return normalizeErrorText(detail ?? responseData ?? error?.message, fallback);
};

const summarizeFailedCountries = (failedCountries) => {
  if (!Array.isArray(failedCountries) || failedCountries.length === 0) return '';
  return failedCountries
    .map((item) => {
      const country = String(item?.country || '-').toUpperCase();
      const reason = normalizeErrorText(item?.error || item?.detail || 'failed', 'failed');
      return `${country}: ${reason}`;
    })
    .join(' | ');
};

const extractScopeConflictDetail = (error) => {
  const detail = error?.response?.data?.detail;
  if (!detail || typeof detail !== 'object') return null;
  if (detail.code !== 'publish_scope_conflict') return null;
  return {
    scope: detail.scope || '-',
    conflicts: Array.isArray(detail.conflicts) ? detail.conflicts : [],
    message: normalizeErrorText(detail.message, 'Aynı kapsamda aktif bir yayın zaten var.'),
  };
};

const isAxiosTimeoutError = (error) => {
  if (!error) return false;
  return error.code === 'ECONNABORTED' || String(error?.message || '').toLowerCase().includes('timeout');
};

export default function AdminContentList() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const resolveRequestLocale = () => {
    const pathLocale = String(window.location.pathname || '').split('/').filter(Boolean)[0]?.toLowerCase();
    if (['tr', 'de', 'fr'].includes(pathLocale)) return pathLocale;
    const stored = String(localStorage.getItem('language') || '').toLowerCase();
    if (['tr', 'de', 'fr'].includes(stored)) return stored;
    return 'tr';
  };

  const authHeaders = useMemo(
    () => {
      const locale = resolveRequestLocale();
      const pathLocale = String(window.location.pathname || '').split('/').filter(Boolean)[0]?.toLowerCase();
      return {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        'Accept-Language': locale,
        'X-URL-Locale': ['tr', 'de', 'fr'].includes(pathLocale) ? pathLocale : locale,
      };
    },
    [],
  );

  const [contentListRows, setContentListRows] = useState([]);
  const [contentListLoading, setContentListLoading] = useState(false);
  const [contentListError, setContentListError] = useState('');
  const [statusMessage, setStatusMessage] = useState('');
  const [contentListView, setContentListView] = useState('active');
  const [selectedPassiveRevisionIds, setSelectedPassiveRevisionIds] = useState([]);
  const [permanentDeleteLoading, setPermanentDeleteLoading] = useState(false);

  const [copyTargetPageType, setCopyTargetPageType] = useState('home');
  const [copyTargetCountry, setCopyTargetCountry] = useState('DE');
  const [copyTargetModule, setCopyTargetModule] = useState('global');
  const [copyTargetCategoryId, setCopyTargetCategoryId] = useState('');
  const [copyPublishAfterCopy, setCopyPublishAfterCopy] = useState(false);
  const [copyConflictModalOpen, setCopyConflictModalOpen] = useState(false);
  const [copyConflictLoading, setCopyConflictLoading] = useState(false);
  const [pendingCopyConflict, setPendingCopyConflict] = useState(null);

  const [presetCountriesInput, setPresetCountriesInput] = useState('TR,DE,FR');
  const [presetModule, setPresetModule] = useState('global');
  const [presetPersona, setPresetPersona] = useState('individual');
  const [presetVariant, setPresetVariant] = useState('A');
  const [presetOverwriteDraft, setPresetOverwriteDraft] = useState(true);
  const [presetPublishAfterSeed, setPresetPublishAfterSeed] = useState(true);
  const [presetIncludeExtendedTemplates, setPresetIncludeExtendedTemplates] = useState(false);
  const [presetFailFast, setPresetFailFast] = useState(true);
  const [presetLoading, setPresetLoading] = useState(false);
  const [presetError, setPresetError] = useState('');
  const [presetStatus, setPresetStatus] = useState('');
  const [presetInstallResult, setPresetInstallResult] = useState(null);
  const [presetVerifyResult, setPresetVerifyResult] = useState(null);

  const presetInstallFailedCountries = useMemo(
    () => (Array.isArray(presetInstallResult?.failed_countries) ? presetInstallResult.failed_countries : []),
    [presetInstallResult],
  );
  const presetInstallCountryResults = useMemo(
    () => (Array.isArray(presetInstallResult?.results) ? presetInstallResult.results : []),
    [presetInstallResult],
  );
  const presetVerifyCountrySummaries = useMemo(
    () => (Array.isArray(presetVerifyResult?.country_summaries) ? presetVerifyResult.country_summaries : []),
    [presetVerifyResult],
  );
  const presetVerifyNotReadyItems = useMemo(() => {
    const rows = Array.isArray(presetVerifyResult?.items) ? presetVerifyResult.items : [];
    return rows.filter((item) => !Boolean(item?.is_ready));
  }, [presetVerifyResult]);

  const fetchContentList = useCallback(async ({ silent = false } = {}) => {
    setContentListLoading(true);
    if (!silent) setContentListError('');
    try {
      const response = await axios.get(`${API}/admin/layouts`, {
        headers: authHeaders,
        params: {
          include_deleted: true,
          statuses: CONTENT_LIST_STATUS_FILTER.join(','),
          page: 1,
          limit: 200,
        },
      });
      const items = Array.isArray(response.data?.items) ? response.data.items : [];
      setContentListRows(items);
      setContentListError('');
    } catch (err) {
      setContentListRows([]);
      const message = extractApiErrorText(err, 'Content list yüklenemedi');
      setContentListError(message);
      if (!silent) toast.error(message);
    } finally {
      setContentListLoading(false);
    }
  }, [authHeaders]);

  useEffect(() => {
    fetchContentList({ silent: true });
  }, [fetchContentList]);

  const activeRows = useMemo(
    () => contentListRows.filter((item) => !item?.is_deleted && Boolean(item?.is_active)),
    [contentListRows],
  );
  const passiveRows = useMemo(
    () => contentListRows.filter((item) => Boolean(item?.is_deleted) || !Boolean(item?.is_active)),
    [contentListRows],
  );
  const visibleRows = contentListView === 'passive' ? passiveRows : activeRows;
  const passiveRevisionIds = useMemo(
    () => passiveRows.map((item) => item?.revision_id || item?.id).filter(Boolean),
    [passiveRows],
  );
  const selectedPassiveCount = useMemo(
    () => selectedPassiveRevisionIds.filter((revisionId) => passiveRevisionIds.includes(revisionId)).length,
    [passiveRevisionIds, selectedPassiveRevisionIds],
  );
  const allPassiveSelected = passiveRevisionIds.length > 0 && selectedPassiveCount === passiveRevisionIds.length;

  useEffect(() => {
    setSelectedPassiveRevisionIds((previous) => previous.filter((revisionId) => passiveRevisionIds.includes(revisionId)));
  }, [passiveRevisionIds]);

  useEffect(() => {
    if (contentListView !== 'passive') {
      setSelectedPassiveRevisionIds([]);
    }
  }, [contentListView]);

  const togglePassiveSelection = (revisionId) => {
    if (!revisionId) return;
    setSelectedPassiveRevisionIds((previous) => {
      if (previous.includes(revisionId)) {
        return previous.filter((value) => value !== revisionId);
      }
      return [...previous, revisionId];
    });
  };

  const toggleSelectAllPassiveRows = () => {
    if (allPassiveSelected) {
      setSelectedPassiveRevisionIds([]);
      return;
    }
    setSelectedPassiveRevisionIds(passiveRevisionIds);
  };

  const handleContentListEdit = (item) => {
    if (!item?.layout_page_id || item.is_deleted) return;
    const params = new URLSearchParams();
    params.set('autoload_page_id', item.layout_page_id);
    params.set('page_type', item.page_type || 'home');
    params.set('country', String(item.country || 'DE').toUpperCase());
    params.set('module', String(item.module || 'global'));
    if (item.category_id) {
      params.set('category_id', item.category_id);
    }
    navigate(`/admin/site-design/content-builder?${params.toString()}`);
  };

  const handleContentListDelete = async (item) => {
    if (!item?.revision_id || item.is_deleted) return;
    const confirmed = window.confirm('Bu revision soft-delete edilsin mi?');
    if (!confirmed) return;

    setStatusMessage('');
    setContentListError('');
    try {
      await axios.delete(`${API}/admin/layouts/${item.revision_id}`, {
        headers: authHeaders,
      });
      setStatusMessage('Revision soft-delete edildi.');
      toast.success('Revision soft-delete edildi.');
      await fetchContentList({ silent: true });
    } catch (err) {
      const message = extractApiErrorText(err, 'Soft-delete başarısız');
      setContentListError(message);
      toast.error(message);
    }
  };

  const handleCopySuccess = async ({ response, normalizedCountry, normalizedModule, fallbackPageType }) => {
    const targetPage = response?.data?.target_page;
    const targetPageId = targetPage?.id;

    await fetchContentList({ silent: true });
    setStatusMessage('Sayfa bire bir kopyalandı. Hedef sayfa Content Builder’da açılıyor.');
    toast.success('Bire bir kopyalama tamamlandı.');

    if (targetPageId) {
      const params = new URLSearchParams();
      params.set('autoload_page_id', targetPageId);
      params.set('page_type', targetPage?.page_type || fallbackPageType || 'home');
      params.set('country', String(targetPage?.country || normalizedCountry || 'DE').toUpperCase());
      params.set('module', String(targetPage?.module || normalizedModule || 'global'));
      if (targetPage?.category_id) {
        params.set('category_id', targetPage.category_id);
      }
      navigate(`/admin/site-design/content-builder?${params.toString()}`);
    }
  };

  const handleCopyConflictCancel = () => {
    setCopyConflictModalOpen(false);
    setPendingCopyConflict(null);
    setStatusMessage('Kopyalama iptal edildi: conflict çözümü onaylanmadı.');
    toast.info('Kopyalama iptal edildi.');
  };

  const handleCopyConflictProceed = async () => {
    if (!pendingCopyConflict?.sourceRevisionId || !pendingCopyConflict?.requestPayload) return;

    setCopyConflictLoading(true);
    setContentListError('');
    try {
      const response = await axios.post(
        `${API}/admin/layouts/${pendingCopyConflict.sourceRevisionId}/copy`,
        pendingCopyConflict.requestPayload,
        {
          headers: authHeaders,
          params: { force: true },
        },
      );
      setCopyConflictModalOpen(false);
      setPendingCopyConflict(null);
      await handleCopySuccess({
        response,
        normalizedCountry: pendingCopyConflict.normalizedCountry,
        normalizedModule: pendingCopyConflict.normalizedModule,
        fallbackPageType: pendingCopyConflict.fallbackPageType,
      });
    } catch (err) {
      const message = extractApiErrorText(err, 'Kopyalama başarısız');
      setContentListError(message);
      toast.error(message);
    } finally {
      setCopyConflictLoading(false);
    }
  };

  const handleContentListCopy = async (item) => {
    if (!item?.revision_id) {
      const sourceErrorMessage = t('copy_page.invalid_source', { defaultValue: 'Kopya kaynağı geçersiz.' });
      setContentListError(sourceErrorMessage);
      toast.error(sourceErrorMessage);
      return;
    }
    const normalizedModule = String(copyTargetModule || '').trim();
    const normalizedCountry = String(copyTargetCountry || '').trim().toUpperCase();

    if (!normalizedCountry || !normalizedModule) {
      const targetErrorMessage = t('copy_page.invalid_target', { defaultValue: 'Kopya hedefi için ülke ve module zorunludur.' });
      toast.error(targetErrorMessage);
      return;
    }

    setStatusMessage('');
    setContentListError('');
    try {
      const requestPayload = {
        target_page_type: copyTargetPageType,
        country: normalizedCountry,
        module: normalizedModule,
        category_id: String(copyTargetCategoryId || '').trim() || null,
        publish_after_copy: copyPublishAfterCopy,
      };

      let response;
      try {
        response = await axios.post(
          `${API}/admin/layouts/${item.revision_id}/copy`,
          requestPayload,
          { headers: authHeaders },
        );
      } catch (copyError) {
        const conflictDetail = extractScopeConflictDetail(copyError);
        if (!conflictDetail || !copyPublishAfterCopy) {
          throw copyError;
        }

        const hasMissingRevisionId = (conflictDetail.conflicts || []).some((conflictItem) => !String(conflictItem?.revision_id || '').trim());
        if (hasMissingRevisionId) {
          const revisionMissingMessage = t('copy_page.revision_id_required', { defaultValue: 'Çakışma listesinde revision_id zorunludur.' });
          setContentListError(revisionMissingMessage);
          toast.error(revisionMissingMessage);
          return;
        }

        setPendingCopyConflict({
          sourceRevisionId: item.revision_id,
          requestPayload,
          normalizedCountry,
          normalizedModule,
          fallbackPageType: copyTargetPageType,
          conflictDetail,
        });
        setCopyConflictModalOpen(true);
        setStatusMessage(t('copy_page.conflict_warning', { defaultValue: 'Kopyalama çakışması tespit edildi. Onay bekleniyor.' }));
        return;
      }

      await handleCopySuccess({
        response,
        normalizedCountry,
        normalizedModule,
        fallbackPageType: copyTargetPageType,
      });
    } catch (err) {
      const message = extractApiErrorText(err, 'Kopyalama başarısız');
      setContentListError(message);
      toast.error(message);
    }
  };

  const handleSetRevisionActive = async (item, nextActive) => {
    if (!item?.revision_id || item.is_deleted) return;

    setStatusMessage('');
    setContentListError('');
    try {
      await axios.patch(
        `${API}/admin/layouts/${item.revision_id}/active`,
        { is_active: nextActive },
        { headers: authHeaders },
      );
      setStatusMessage(`Revision ${nextActive ? 'aktif' : 'pasif'} olarak güncellendi.`);
      toast.success(`Revision ${nextActive ? 'aktif' : 'pasif'} olarak güncellendi.`);
      await fetchContentList({ silent: true });
    } catch (err) {
      const message = extractApiErrorText(err, 'Aktif/pasif güncellemesi başarısız');
      setContentListError(message);
      toast.error(message);
    }
  };

  const handleRestoreFromPassive = async (item) => {
    if (!item?.revision_id) return;

    setStatusMessage('');
    setContentListError('');
    try {
      if (item.is_deleted) {
        await axios.post(`${API}/admin/layouts/${item.revision_id}/restore`, {}, { headers: authHeaders });
      } else {
        await axios.patch(
          `${API}/admin/layouts/${item.revision_id}/active`,
          { is_active: true },
          { headers: authHeaders },
        );
      }

      setStatusMessage('Revision tekrar aktif listeye alındı.');
      toast.success('Revision aktif edildi.');
      await fetchContentList({ silent: true });
      setContentListView('active');
    } catch (err) {
      const message = extractApiErrorText(err, 'Revision geri yükleme başarısız');
      setContentListError(message);
      toast.error(message);
    }
  };

  const handlePermanentDelete = async ({ revisionIds, mode }) => {
    const normalizedRevisionIds = Array.isArray(revisionIds)
      ? revisionIds.map((value) => String(value || '').trim()).filter(Boolean)
      : [];
    if (!normalizedRevisionIds.length) {
      toast.error('Kalıcı silme için en az bir kayıt seçin.');
      return;
    }

    const confirmText = mode === 'bulk'
      ? `${normalizedRevisionIds.length} adet pasif/arsiv revision kalıcı olarak silinsin mi?`
      : 'Bu pasif/arsiv revision kalıcı olarak silinsin mi?';
    const confirmed = window.confirm(confirmText);
    if (!confirmed) return;

    setPermanentDeleteLoading(true);
    setStatusMessage('');
    setContentListError('');

    try {
      const response = await axios.delete(`${API}/admin/layouts/permanent`, {
        headers: authHeaders,
        data: { revision_ids: normalizedRevisionIds },
      });
      const deletedCount = Number(response.data?.deleted_count || normalizedRevisionIds.length || 0);
      setStatusMessage(`${deletedCount} kayıt kalıcı olarak silindi.`);
      toast.success(`${deletedCount} kayıt kalıcı olarak silindi.`);
      setSelectedPassiveRevisionIds([]);
      await fetchContentList({ silent: true });
    } catch (err) {
      const message = extractApiErrorText(err, 'Kalıcı silme başarısız');
      setContentListError(message);
      toast.error(message);
    } finally {
      setPermanentDeleteLoading(false);
    }
  };

  const handlePermanentDeleteSingle = async (item) => {
    const revisionId = item?.revision_id || item?.id;
    if (!revisionId) return;
    await handlePermanentDelete({ revisionIds: [revisionId], mode: 'single' });
  };

  const handlePermanentDeleteBulk = async () => {
    await handlePermanentDelete({ revisionIds: selectedPassiveRevisionIds, mode: 'bulk' });
  };

  const handleResetAndSeedHomeWireframe = async () => {
    const confirmed = window.confirm('Tüm listeleri pasifleştirip (A: tüm scope), TR/DE/FR için yeni wireframe ana sayfa oluşturulsun mu?');
    if (!confirmed) return;

    setPresetLoading(true);
    setPresetError('');
    setPresetStatus('');
    setStatusMessage('');
    setContentListError('');
    try {
      const response = await axios.post(
        `${API}/admin/layouts/workflows/reset-and-seed-home-wireframe`,
        {
          countries: ['TR', 'DE', 'FR'],
          module: 'global',
          passivate_all: true,
          hard_delete_demo_pages: true,
        },
        { headers: authHeaders },
      );

      const payload = response.data || {};
      setPresetInstallResult(payload);

      if (payload.ok === false) {
        const failedSummary = summarizeFailedCountries(payload.failed_countries);
        const message = normalizeErrorText(payload.detail, 'Toplu pasifleştirme/wireframe işlemi tamamlanamadı');
        const fullMessage = failedSummary ? `${message} | ${failedSummary}` : message;
        setPresetError(fullMessage);
        toast.error(fullMessage);
        return;
      }

      setPresetStatus('Tüm sayfalar pasife alındı ve yeni ana sayfa wireframe’i TR/DE/FR için oluşturuldu.');
      setStatusMessage('Toplu pasifleştirme + yeni ana sayfa oluşturma tamamlandı.');
      toast.success('Yeni ana sayfa wireframe operasyonu tamamlandı.');
      await fetchContentList({ silent: true });
      setContentListView('active');
    } catch (err) {
      const message = extractApiErrorText(err, 'Toplu pasifleştirme/wireframe işlemi başarısız');
      setPresetError(message);
      toast.error(message);
    } finally {
      setPresetLoading(false);
    }
  };

  const handleInstallStandardPack = async () => {
    const countries = parseCountriesInput(presetCountriesInput);
    if (!countries.length) {
      setPresetError('En az bir ülke giriniz. Örn: TR,DE,FR');
      return;
    }
    const normalizedModule = String(presetModule || '').trim();
    if (!normalizedModule) {
      setPresetError('Module zorunludur.');
      return;
    }

    setPresetLoading(true);
    setPresetError('');
    setPresetStatus('');
    setPresetInstallResult(null);
    try {
      const response = await axios.post(
        `${API}/admin/site/content-layout/preset/install-standard-pack`,
        {
          countries,
          module: normalizedModule,
          persona: presetPersona,
          variant: presetVariant,
          overwrite_existing_draft: presetOverwriteDraft,
          publish_after_seed: presetPublishAfterSeed,
          include_extended_templates: presetIncludeExtendedTemplates,
          fail_fast: presetFailFast,
        },
        { headers: authHeaders, timeout: 20000 },
      );
      const payload = response.data || {};
      setPresetInstallResult(payload);

      if (payload.ok === false) {
        const failedSummary = summarizeFailedCountries(payload.failed_countries);
        const message = normalizeErrorText(payload.detail, 'Template pack kurulumu hızlı-fail ile durdu');
        const stoppedEarlyMessage = payload.stopped_early ? 'İşlem fail-fast nedeniyle ilk hatada durduruldu.' : '';
        const fullMessage = [message, stoppedEarlyMessage, failedSummary].filter(Boolean).join(' | ');
        setPresetError(fullMessage);
        toast.error(fullMessage);
        return;
      }

      setPresetStatus('Standart template pack kurulumu tamamlandı.');
      toast.success('Standart template pack kuruldu.');
      await fetchContentList({ silent: true });
    } catch (err) {
      const message = isAxiosTimeoutError(err)
        ? 'Template pack kurulumu timeout nedeniyle hızlıca durduruldu. Ülke sonuçlarını kontrol edin.'
        : extractApiErrorText(err, 'Template pack kurulumu başarısız');
      setPresetError(message);
      toast.error(message);
    } finally {
      setPresetLoading(false);
    }
  };

  const handleVerifyStandardPack = async () => {
    const countries = parseCountriesInput(presetCountriesInput);
    if (!countries.length) {
      setPresetError('En az bir ülke giriniz. Örn: TR,DE,FR');
      return;
    }
    const normalizedModule = String(presetModule || '').trim();
    if (!normalizedModule) {
      setPresetError('Module zorunludur.');
      return;
    }

    setPresetLoading(true);
    setPresetError('');
    setPresetVerifyResult(null);
    try {
      const response = await axios.get(`${API}/admin/site/content-layout/preset/verify-standard-pack`, {
        headers: authHeaders,
        timeout: 15000,
        params: {
          countries: countries.join(','),
          module: normalizedModule,
          include_extended_templates: presetIncludeExtendedTemplates,
          fail_fast: presetFailFast,
        },
      });
      const payload = response.data || {};
      setPresetVerifyResult(payload);

      if (payload.ok === false) {
        const failedSummary = summarizeFailedCountries(payload.failed_countries);
        const message = normalizeErrorText(payload.detail, 'Template pack doğrulaması fail-fast nedeniyle durdu');
        const fullMessage = [message, failedSummary].filter(Boolean).join(' | ');
        setPresetError(fullMessage);
        toast.error(fullMessage);
        return;
      }

      const ratio = payload?.summary?.ready_ratio;
      const missingRows = Number(payload?.summary?.missing_rows || 0);
      setPresetStatus(`TR/DE/FR publish doğrulaması güncellendi. Hazır oran: ${ratio ?? 0}% • Eksik: ${missingRows}`);
      toast.success('Standart pack doğrulaması tamamlandı.');
    } catch (err) {
      const message = isAxiosTimeoutError(err)
        ? 'Template pack doğrulaması timeout nedeniyle hızlıca durduruldu. Lütfen tekrar deneyin.'
        : extractApiErrorText(err, 'Template pack doğrulaması başarısız');
      setPresetError(message);
      toast.error(message);
    } finally {
      setPresetLoading(false);
    }
  };

  return (
    <div className="space-y-5" data-testid="admin-content-list-page">
      <section className="rounded-xl border bg-white p-4" data-testid="admin-content-list-panel">
        <div className="flex flex-wrap items-center justify-between gap-2" data-testid="admin-content-list-header">
          <div>
            <h1 className="text-sm font-semibold" data-testid="admin-content-list-title">Content List</h1>
            <p className="text-xs text-slate-500" data-testid="admin-content-list-subtitle">
              Filtre: draft + published • Silinen kayıtlar kırmızı gösterilir • Aktif/Pasif durumları yönetilebilir.
            </p>
          </div>
          <div className="flex items-center gap-2 text-xs" data-testid="admin-content-list-header-actions">
            <button
              type="button"
              className="h-9 rounded border px-3"
              onClick={() => fetchContentList()}
              disabled={contentListLoading}
              data-testid="admin-content-list-refresh-button"
            >
              Yenile
            </button>
            {contentListView === 'passive' ? (
              <button
                type="button"
                className="h-9 rounded border border-rose-300 px-3 text-rose-700 disabled:cursor-not-allowed disabled:opacity-60"
                onClick={handlePermanentDeleteBulk}
                disabled={permanentDeleteLoading || selectedPassiveCount === 0}
                data-testid="admin-content-list-bulk-permanent-delete-button"
              >
                Toplu Kalıcı Sil ({selectedPassiveCount})
              </button>
            ) : null}
            <div className="inline-flex rounded border p-1" data-testid="admin-content-list-view-switch">
              <button
                type="button"
                className={`h-8 rounded px-3 ${contentListView === 'active' ? 'bg-emerald-600 text-white' : 'text-slate-700'}`}
                onClick={() => setContentListView('active')}
                data-testid="admin-content-list-view-active-button"
              >
                Aktif List ({activeRows.length})
              </button>
              <button
                type="button"
                className={`h-8 rounded px-3 ${contentListView === 'passive' ? 'bg-rose-600 text-white' : 'text-slate-700'}`}
                onClick={() => setContentListView('passive')}
                data-testid="admin-content-list-view-passive-button"
              >
                Pasif/Arşiv List ({passiveRows.length})
              </button>
            </div>
          </div>
        </div>

        <div className="mt-3 rounded-lg border bg-slate-50 p-3" data-testid="admin-content-list-copy-target-panel">
          <div className="text-xs font-semibold" data-testid="admin-content-list-copy-target-title">Bire bir kopya hedefi</div>
          <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-5" data-testid="admin-content-list-copy-target-grid">
            <label className="text-xs" data-testid="admin-content-list-copy-target-page-type-wrap">
              Page Type
              <select
                className="mt-1 h-9 w-full rounded border px-2"
                value={copyTargetPageType}
                onChange={(event) => setCopyTargetPageType(event.target.value)}
                data-testid="admin-content-list-copy-target-page-type-select"
              >
                {PAGE_TYPE_OPTIONS.map((item) => <option key={`content-list-copy-target-${item.value}`} value={item.value}>{item.label}</option>)}
              </select>
            </label>

            <label className="text-xs" data-testid="admin-content-list-copy-target-country-wrap">
              Country
              <input
                className="mt-1 h-9 w-full rounded border px-2"
                value={copyTargetCountry}
                onChange={(event) => setCopyTargetCountry(event.target.value.toUpperCase())}
                data-testid="admin-content-list-copy-target-country-input"
              />
            </label>

            <label className="text-xs" data-testid="admin-content-list-copy-target-module-wrap">
              Module
              <input
                className="mt-1 h-9 w-full rounded border px-2"
                value={copyTargetModule}
                onChange={(event) => setCopyTargetModule(event.target.value)}
                data-testid="admin-content-list-copy-target-module-input"
              />
            </label>

            <label className="text-xs" data-testid="admin-content-list-copy-target-category-wrap">
              Category ID (opsiyonel)
              <input
                className="mt-1 h-9 w-full rounded border px-2"
                value={copyTargetCategoryId}
                onChange={(event) => setCopyTargetCategoryId(event.target.value)}
                data-testid="admin-content-list-copy-target-category-input"
              />
            </label>

            <label className="mt-6 inline-flex items-center gap-2 text-xs" data-testid="admin-content-list-copy-target-publish-wrap">
              <input
                type="checkbox"
                checked={copyPublishAfterCopy}
                onChange={(event) => setCopyPublishAfterCopy(event.target.checked)}
                data-testid="admin-content-list-copy-target-publish-input"
              />
              Kopya sonrası publish et
            </label>
          </div>
        </div>

        <div className="mt-3 rounded-lg border bg-white p-3" data-testid="admin-content-list-template-pack-panel">
          <div className="flex flex-wrap items-center justify-between gap-2" data-testid="admin-content-list-template-pack-header">
            <div>
              <h2 className="text-xs font-semibold" data-testid="admin-content-list-template-pack-title">#612 + P1 Başlangıç: Standart Template Pack</h2>
              <p className="text-xs text-slate-500" data-testid="admin-content-list-template-pack-subtitle">TR/DE/FR için (varsayılan: core 4 şablon) publish doğrulama, tek tık preset kurulum ve wireframe reset akışı</p>
            </div>
            <div className="flex gap-2" data-testid="admin-content-list-template-pack-header-actions">
              <button
                type="button"
                className="h-8 rounded border border-amber-300 px-3 text-xs text-amber-700"
                onClick={handleResetAndSeedHomeWireframe}
                disabled={presetLoading}
                data-testid="admin-content-list-template-pack-reset-wireframe-button"
              >
                Tümünü Pasifleştir + Yeni Home Oluştur
              </button>
              <button
                type="button"
                className="h-8 rounded border px-3 text-xs"
                onClick={handleVerifyStandardPack}
                disabled={presetLoading}
                data-testid="admin-content-list-template-pack-verify-button"
              >
                Publish Doğrula
              </button>
              <button
                type="button"
                className="h-8 rounded border border-blue-300 px-3 text-xs text-blue-700"
                onClick={handleInstallStandardPack}
                disabled={presetLoading}
                data-testid="admin-content-list-template-pack-install-button"
              >
                Tek Tık Kurulum Başlat
              </button>
            </div>
          </div>

          <div className="mt-2 grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-6" data-testid="admin-content-list-template-pack-form-grid">
            <label className="text-xs" data-testid="admin-content-list-template-pack-countries-wrap">
              Countries (CSV)
              <input
                className="mt-1 h-8 w-full rounded border px-2"
                value={presetCountriesInput}
                onChange={(event) => setPresetCountriesInput(event.target.value.toUpperCase())}
                placeholder="TR,DE,FR"
                data-testid="admin-content-list-template-pack-countries-input"
              />
            </label>

            <label className="text-xs" data-testid="admin-content-list-template-pack-module-wrap">
              Module
              <input
                className="mt-1 h-8 w-full rounded border px-2"
                value={presetModule}
                onChange={(event) => setPresetModule(event.target.value)}
                data-testid="admin-content-list-template-pack-module-input"
              />
            </label>

            <label className="text-xs" data-testid="admin-content-list-template-pack-persona-wrap">
              Persona
              <select
                className="mt-1 h-8 w-full rounded border px-2"
                value={presetPersona}
                onChange={(event) => setPresetPersona(event.target.value)}
                data-testid="admin-content-list-template-pack-persona-select"
              >
                <option value="individual">individual</option>
                <option value="corporate">corporate</option>
              </select>
            </label>

            <label className="text-xs" data-testid="admin-content-list-template-pack-variant-wrap">
              Variant
              <select
                className="mt-1 h-8 w-full rounded border px-2"
                value={presetVariant}
                onChange={(event) => setPresetVariant(event.target.value)}
                data-testid="admin-content-list-template-pack-variant-select"
              >
                <option value="A">A</option>
                <option value="B">B</option>
              </select>
            </label>

            <label className="mt-6 inline-flex items-center gap-2 text-xs" data-testid="admin-content-list-template-pack-overwrite-wrap">
              <input
                type="checkbox"
                checked={presetOverwriteDraft}
                onChange={(event) => setPresetOverwriteDraft(event.target.checked)}
                data-testid="admin-content-list-template-pack-overwrite-input"
              />
              Draft üzerine yaz
            </label>

            <label className="mt-6 inline-flex items-center gap-2 text-xs" data-testid="admin-content-list-template-pack-publish-wrap">
              <input
                type="checkbox"
                checked={presetPublishAfterSeed}
                onChange={(event) => setPresetPublishAfterSeed(event.target.checked)}
                data-testid="admin-content-list-template-pack-publish-input"
              />
              Seed sonrası publish
            </label>

            <label className="mt-6 inline-flex items-center gap-2 text-xs" data-testid="admin-content-list-template-pack-extended-wrap">
              <input
                type="checkbox"
                checked={presetIncludeExtendedTemplates}
                onChange={(event) => setPresetIncludeExtendedTemplates(event.target.checked)}
                data-testid="admin-content-list-template-pack-extended-input"
              />
              Genişletilmiş şablonlar (core dışı)
            </label>

            <label className="mt-6 inline-flex items-center gap-2 text-xs" data-testid="admin-content-list-template-pack-fail-fast-wrap">
              <input
                type="checkbox"
                checked={presetFailFast}
                onChange={(event) => setPresetFailFast(event.target.checked)}
                data-testid="admin-content-list-template-pack-fail-fast-input"
              />
              Hızlı fail (ilk hatada durdur)
            </label>
          </div>

          {presetStatus ? (
            <p className="mt-2 text-xs text-emerald-700" data-testid="admin-content-list-template-pack-status-message">{presetStatus}</p>
          ) : null}
          {presetError ? (
            <p className="mt-2 text-xs text-rose-700" data-testid="admin-content-list-template-pack-error-message">{presetError}</p>
          ) : null}

          {presetInstallResult?.summary ? (
            <div className="mt-2 rounded border bg-slate-50 p-2 text-xs" data-testid="admin-content-list-template-pack-install-summary">
              <span data-testid="admin-content-list-template-pack-install-scope">scope: {presetInstallResult.template_scope || 'core'}</span>
              {' · '}
              <span data-testid="admin-content-list-template-pack-install-created-pages">created_pages: {presetInstallResult.summary.created_pages ?? 0}</span>
              {' · '}
              <span data-testid="admin-content-list-template-pack-install-updated-drafts">updated_drafts: {presetInstallResult.summary.updated_drafts ?? 0}</span>
              {' · '}
              <span data-testid="admin-content-list-template-pack-install-published">published_revisions: {presetInstallResult.summary.published_revisions ?? 0}</span>
              {' · '}
              <span data-testid="admin-content-list-template-pack-install-failed-countries">failed_countries: {presetInstallResult.summary.failed_countries ?? 0}</span>
            </div>
          ) : null}

          {presetInstallCountryResults.length ? (
            <div className="mt-2 overflow-x-auto" data-testid="admin-content-list-template-pack-install-results-wrap">
              <table className="min-w-full text-left text-xs" data-testid="admin-content-list-template-pack-install-results-table">
                <thead>
                  <tr className="border-b bg-slate-50" data-testid="admin-content-list-template-pack-install-results-head">
                    <th className="px-2 py-1">country</th>
                    <th className="px-2 py-1">ok</th>
                    <th className="px-2 py-1">created_pages</th>
                    <th className="px-2 py-1">updated_drafts</th>
                    <th className="px-2 py-1">published</th>
                    <th className="px-2 py-1">error</th>
                  </tr>
                </thead>
                <tbody data-testid="admin-content-list-template-pack-install-results-body">
                  {presetInstallCountryResults.map((row, index) => (
                    <tr key={`preset-install-result-${row?.country || index}`} className="border-b" data-testid={`admin-content-list-template-pack-install-result-row-${index}`}>
                      <td className="px-2 py-1" data-testid={`admin-content-list-template-pack-install-result-country-${index}`}>{row?.country || '-'}</td>
                      <td className="px-2 py-1" data-testid={`admin-content-list-template-pack-install-result-ok-${index}`}>{row?.ok === false ? 'hayır' : 'evet'}</td>
                      <td className="px-2 py-1" data-testid={`admin-content-list-template-pack-install-result-created-${index}`}>{row?.summary?.created_pages ?? 0}</td>
                      <td className="px-2 py-1" data-testid={`admin-content-list-template-pack-install-result-updated-${index}`}>{row?.summary?.updated_drafts ?? 0}</td>
                      <td className="px-2 py-1" data-testid={`admin-content-list-template-pack-install-result-published-${index}`}>{row?.summary?.published_revisions ?? 0}</td>
                      <td className="px-2 py-1 text-rose-700" data-testid={`admin-content-list-template-pack-install-result-error-${index}`}>{row?.error || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}

          {presetInstallFailedCountries.length ? (
            <div className="mt-2 rounded border border-rose-200 bg-rose-50 p-2 text-xs text-rose-700" data-testid="admin-content-list-template-pack-install-failed-list">
              {presetInstallFailedCountries.map((item, index) => (
                <p key={`preset-install-failed-${item?.country || index}`} data-testid={`admin-content-list-template-pack-install-failed-item-${index}`}>
                  {String(item?.country || '-').toUpperCase()} • {normalizeErrorText(item?.error || item?.detail || 'failed', 'failed')}
                </p>
              ))}
            </div>
          ) : null}

          {presetVerifyResult?.summary ? (
            <div className="mt-2 rounded border bg-slate-50 p-2 text-xs" data-testid="admin-content-list-template-pack-verify-summary">
              <span data-testid="admin-content-list-template-pack-verify-scope">scope: {presetVerifyResult.template_scope || 'core'}</span>
              {' · '}
              <span data-testid="admin-content-list-template-pack-verify-ready-rows">ready_rows: {presetVerifyResult.summary.ready_rows ?? 0}</span>
              {' / '}
              <span data-testid="admin-content-list-template-pack-verify-total-rows">total_rows: {presetVerifyResult.summary.total_rows ?? 0}</span>
              {' · '}
              <span data-testid="admin-content-list-template-pack-verify-ratio">ready_ratio: {presetVerifyResult.summary.ready_ratio ?? 0}%</span>
              {' · '}
              <span data-testid="admin-content-list-template-pack-verify-missing-rows">missing_rows: {presetVerifyResult.summary.missing_rows ?? 0}</span>
            </div>
          ) : null}

          {presetVerifyCountrySummaries.length ? (
            <div className="mt-2 overflow-x-auto" data-testid="admin-content-list-template-pack-verify-country-wrap">
              <table className="min-w-full text-left text-xs" data-testid="admin-content-list-template-pack-verify-country-table">
                <thead>
                  <tr className="border-b bg-slate-50" data-testid="admin-content-list-template-pack-verify-country-head">
                    <th className="px-2 py-1">country</th>
                    <th className="px-2 py-1">ok</th>
                    <th className="px-2 py-1">ready_rows</th>
                    <th className="px-2 py-1">total_rows</th>
                    <th className="px-2 py-1">ratio</th>
                    <th className="px-2 py-1">error</th>
                  </tr>
                </thead>
                <tbody data-testid="admin-content-list-template-pack-verify-country-body">
                  {presetVerifyCountrySummaries.map((row, index) => (
                    <tr key={`preset-verify-country-${row?.country || index}`} className="border-b" data-testid={`admin-content-list-template-pack-verify-country-row-${index}`}>
                      <td className="px-2 py-1" data-testid={`admin-content-list-template-pack-verify-country-${index}`}>{row?.country || '-'}</td>
                      <td className="px-2 py-1" data-testid={`admin-content-list-template-pack-verify-country-ok-${index}`}>{row?.ok === false ? 'hayır' : 'evet'}</td>
                      <td className="px-2 py-1" data-testid={`admin-content-list-template-pack-verify-country-ready-${index}`}>{row?.ready_rows ?? 0}</td>
                      <td className="px-2 py-1" data-testid={`admin-content-list-template-pack-verify-country-total-${index}`}>{row?.total_rows ?? 0}</td>
                      <td className="px-2 py-1" data-testid={`admin-content-list-template-pack-verify-country-ratio-${index}`}>{row?.ready_ratio ?? 0}%</td>
                      <td className="px-2 py-1 text-rose-700" data-testid={`admin-content-list-template-pack-verify-country-error-${index}`}>{row?.error || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}

          {presetVerifyNotReadyItems.length ? (
            <div className="mt-2 rounded border border-amber-200 bg-amber-50 p-2 text-xs" data-testid="admin-content-list-template-pack-verify-not-ready-wrap">
              <p className="font-semibold text-amber-700" data-testid="admin-content-list-template-pack-verify-not-ready-title">
                Hazır olmayan satırlar ({presetVerifyNotReadyItems.length})
              </p>
              <div className="mt-1 flex flex-wrap gap-2" data-testid="admin-content-list-template-pack-verify-not-ready-list">
                {presetVerifyNotReadyItems.slice(0, 30).map((item, index) => (
                  <span
                    key={`preset-verify-not-ready-${item?.country || 'x'}-${item?.page_type || index}`}
                    className="rounded border border-amber-300 bg-white px-2 py-1"
                    data-testid={`admin-content-list-template-pack-verify-not-ready-item-${index}`}
                  >
                    {String(item?.country || '-').toUpperCase()} • {item?.page_type || '-'}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </div>

        <div className="mt-3 overflow-x-auto" data-testid="admin-content-list-table-wrap">
          <div className="mb-2 text-xs font-semibold text-slate-700" data-testid="admin-content-list-current-view-label">
            {contentListView === 'active' ? 'Aktif List' : 'Pasif / Arşiv List'}
          </div>
          <table className="min-w-full text-left text-xs" data-testid="admin-content-list-table">
            <thead>
              <tr className="border-b bg-slate-50" data-testid="admin-content-list-head-row">
                <th className="px-2 py-2" data-testid="admin-content-list-select-head">
                  {contentListView === 'passive' ? (
                    <label className="inline-flex items-center gap-1" data-testid="admin-content-list-select-all-wrap">
                      <input
                        type="checkbox"
                        checked={allPassiveSelected}
                        onChange={toggleSelectAllPassiveRows}
                        disabled={passiveRevisionIds.length === 0}
                        data-testid="admin-content-list-select-all-checkbox"
                      />
                      <span>seç</span>
                    </label>
                  ) : null}
                </th>
                <th className="px-2 py-2">page_type</th>
                <th className="px-2 py-2">country</th>
                <th className="px-2 py-2">module</th>
                <th className="px-2 py-2">category / scope</th>
                <th className="px-2 py-2">status</th>
                <th className="px-2 py-2">active_state</th>
                <th className="px-2 py-2">version</th>
                <th className="px-2 py-2">updated_at</th>
                <th className="px-2 py-2">actions</th>
              </tr>
            </thead>
            <tbody data-testid="admin-content-list-table-body">
              {contentListLoading ? (
                <tr data-testid="admin-content-list-loading-row">
                  <td className="px-2 py-3 text-slate-500" colSpan={10} data-testid="admin-content-list-loading-cell">İçerik listesi yükleniyor...</td>
                </tr>
              ) : visibleRows.length === 0 ? (
                <tr data-testid="admin-content-list-empty-row">
                  <td className="px-2 py-3 text-slate-500" colSpan={10} data-testid="admin-content-list-empty-cell">{contentListView === 'active' ? 'Aktif listede kayıt bulunamadı.' : 'Pasif/Arşiv listesinde kayıt bulunamadı.'}</td>
                </tr>
              ) : (
                visibleRows.map((item) => {
                  const rowKey = item.revision_id || item.id;
                  const deleted = Boolean(item.is_deleted);
                  const active = !deleted && Boolean(item.is_active);
                  const isSelected = selectedPassiveRevisionIds.includes(rowKey);
                  return (
                    <tr
                      key={rowKey}
                      className={`border-b ${deleted ? 'bg-rose-50 text-rose-700' : 'text-slate-700'}`}
                      data-testid={`admin-content-list-row-${rowKey}`}
                    >
                      <td className="px-2 py-2" data-testid={`admin-content-list-select-cell-${rowKey}`}>
                        {contentListView === 'passive' ? (
                          <input
                            type="checkbox"
                            checked={isSelected}
                            onChange={() => togglePassiveSelection(rowKey)}
                            data-testid={`admin-content-list-select-checkbox-${rowKey}`}
                          />
                        ) : null}
                      </td>
                      <td className="px-2 py-2 font-medium" data-testid={`admin-content-list-page-type-${rowKey}`}>
                        {PAGE_TYPE_LABEL_MAP[item.page_type] || item.page_type}
                      </td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-country-${rowKey}`}>{item.country || '-'}</td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-module-${rowKey}`}>{item.module || '-'}</td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-scope-${rowKey}`}>{resolveLayoutScopeLabel(item)}</td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-status-${rowKey}`}>
                        <span className={`inline-flex rounded border px-2 py-1 text-[11px] ${deleted ? 'border-rose-300 bg-rose-100 text-rose-700' : 'border-slate-200 bg-slate-100 text-slate-700'}`}>
                          {deleted ? 'deleted' : item.status}
                        </span>
                      </td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-active-state-${rowKey}`}>
                        <span className="inline-flex items-center gap-1">
                          <span
                            className={`h-2.5 w-2.5 rounded-full ${active ? 'bg-emerald-500' : 'bg-rose-500'}`}
                            data-testid={`admin-content-list-active-dot-${rowKey}`}
                          />
                          <span data-testid={`admin-content-list-active-label-${rowKey}`}>{active ? 'aktif' : 'pasif'}</span>
                        </span>
                      </td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-version-${rowKey}`}>{item.version ?? '-'}</td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-updated-at-${rowKey}`}>{formatLayoutUpdatedAt(item.updated_at)}</td>
                      <td className="px-2 py-2" data-testid={`admin-content-list-actions-${rowKey}`}>
                        <div className="flex flex-wrap gap-1">
                          {contentListView === 'active' ? (
                            <>
                              <button
                                type="button"
                                className="h-8 rounded border px-2 text-[11px]"
                                onClick={() => handleContentListEdit(item)}
                                disabled={deleted}
                                data-testid={`admin-content-list-edit-button-${rowKey}`}
                              >
                                Edit
                              </button>
                              <button
                                type="button"
                                className="h-8 rounded border border-rose-300 px-2 text-[11px] text-rose-700"
                                onClick={() => handleContentListDelete(item)}
                                disabled={deleted}
                                data-testid={`admin-content-list-delete-button-${rowKey}`}
                              >
                                Delete
                              </button>
                              <button
                                type="button"
                                className="h-8 rounded border border-blue-300 px-2 text-[11px] text-blue-700"
                                onClick={() => handleContentListCopy(item)}
                                disabled={deleted}
                                data-testid={`admin-content-list-copy-button-${rowKey}`}
                              >
                                Kopyala
                              </button>
                              <button
                                type="button"
                                className="h-8 rounded border border-rose-300 px-2 text-[11px] text-rose-700"
                                onClick={() => handleSetRevisionActive(item, false)}
                                disabled={deleted || !active}
                                data-testid={`admin-content-list-deactivate-button-${rowKey}`}
                              >
                                Pasif Et
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                type="button"
                                className="h-8 rounded border border-emerald-300 px-2 text-[11px] text-emerald-700"
                                onClick={() => handleRestoreFromPassive(item)}
                                data-testid={`admin-content-list-restore-button-${rowKey}`}
                              >
                                {deleted ? 'Geri Yükle + Aktif Et' : 'Aktif Et'}
                              </button>
                              <button
                                type="button"
                                className="h-8 rounded border border-blue-300 px-2 text-[11px] text-blue-700"
                                onClick={() => handleContentListCopy(item)}
                                disabled={permanentDeleteLoading}
                                data-testid={`admin-content-list-copy-button-passive-${rowKey}`}
                              >
                                Kopyala
                              </button>
                              <button
                                type="button"
                                className="h-8 rounded border border-rose-300 px-2 text-[11px] text-rose-700"
                                onClick={() => handlePermanentDeleteSingle(item)}
                                disabled={permanentDeleteLoading}
                                data-testid={`admin-content-list-permanent-delete-button-${rowKey}`}
                              >
                                Kalıcı Sil
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        <ConfirmModal
          open={copyConflictModalOpen}
          onOpenChange={(nextOpen) => {
            setCopyConflictModalOpen(nextOpen);
            if (!nextOpen && !copyConflictLoading) {
              setPendingCopyConflict(null);
            }
          }}
          title={t('copy_page.conflict_warning', { defaultValue: 'Kopyalama Çakışması' })}
          description={pendingCopyConflict?.conflictDetail?.message || t('copy_page.conflict_warning', { defaultValue: 'Aynı kapsamda aktif bir yayın zaten var.' })}
          warningText={t('copy_page.force_publish_effect', { defaultValue: 'Devam ederseniz eski aktif yayın pasifleştirilir ve yeni kopya publish edilir.' })}
          cancelLabel={t('cancel', { defaultValue: 'İptal' })}
          proceedLabel={t('copy_page.proceed', { defaultValue: 'Devam Et' })}
          openRevisionLabel={t('copy_page.open_revision', { defaultValue: 'Revizyonu Aç' })}
          onCancel={handleCopyConflictCancel}
          onProceed={handleCopyConflictProceed}
          conflictItems={pendingCopyConflict?.conflictDetail?.conflicts || []}
          loading={copyConflictLoading}
          testIdPrefix="admin-content-list-copy-conflict-modal"
        />

        {statusMessage ? (
          <p className="mt-2 text-xs text-emerald-700" data-testid="admin-content-list-status-message">{statusMessage}</p>
        ) : null}
        {contentListError ? (
          <p className="mt-2 text-xs text-rose-700" data-testid="admin-content-list-error-message">{contentListError}</p>
        ) : null}
      </section>
    </div>
  );
}
