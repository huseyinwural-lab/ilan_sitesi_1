import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Heart,
  Info,
  Mail,
  Pencil,
  PlusCircle,
  ShieldAlert,
} from 'lucide-react';
import { LoadingState, ErrorState, EmptyState } from '@/components/account/AccountStates';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const buildMetric = (value = 0, ready = false) => ({ value, ready });

const resolveStatus = (status) => {
  const normalized = (status || '').toLowerCase();
  if (['published', 'active'].includes(normalized)) return 'approved';
  if (['pending_moderation', 'pending'].includes(normalized)) return 'pending';
  if (['rejected', 'needs_revision'].includes(normalized)) return 'rejected';
  return 'draft';
};

const statusMeta = {
  draft: { label: 'Taslak', tone: 'bg-slate-100 text-slate-600' },
  pending: { label: 'Beklemede', tone: 'bg-amber-100 text-amber-700' },
  approved: { label: 'Onaylandı', tone: 'bg-emerald-100 text-emerald-700' },
  rejected: { label: 'Reddedildi', tone: 'bg-rose-100 text-rose-700' },
};

export default function AccountDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [metrics, setMetrics] = useState({
    active: buildMetric(),
    pending: buildMetric(),
    favorites: buildMetric(),
    messages: buildMetric(),
    savedSearches: buildMetric(),
  });
  const [listings, setListings] = useState([]);
  const [listingsReady, setListingsReady] = useState(false);
  const [statusChecks, setStatusChecks] = useState({ emailVerified: true, twoFactorEnabled: true });
  const [quotaInfo, setQuotaInfo] = useState({ remaining: 0, limit: null, ready: false });

  useEffect(() => {
    let active = true;

    const fetchDashboard = async () => {
      setLoading(true);
      const headers = { Authorization: `Bearer ${localStorage.getItem('access_token')}` };

      const requests = [
        fetch(`${API}/v1/listings/my?status=active&limit=1`, { headers }),
        fetch(`${API}/v1/listings/my?status=pending_moderation&limit=1`, { headers }),
        fetch(`${API}/v1/favorites/count`, { headers }),
        fetch(`${API}/v1/messages/unread-count`, { headers }),
        fetch(`${API}/v1/listings/my?limit=5`, { headers }),
        fetch(`${API}/auth/me`, { headers }),
        fetch(`${API}/v1/users/me/2fa/status`, { headers }),
      ];

      const results = await Promise.allSettled(requests);
      const nextMetrics = { ...metrics };
      let successCount = 0;

      const [activeRes, pendingRes, favRes, msgRes, listingsRes, meRes, twoFaRes] = results;

      if (activeRes.status === 'fulfilled' && activeRes.value.ok) {
        const data = await activeRes.value.json();
        nextMetrics.active = buildMetric(data.pagination?.total || 0, true);
        successCount += 1;
      } else {
        nextMetrics.active = buildMetric(0, false);
      }

      if (pendingRes.status === 'fulfilled' && pendingRes.value.ok) {
        const data = await pendingRes.value.json();
        nextMetrics.pending = buildMetric(data.pagination?.total || 0, true);
        successCount += 1;
      } else {
        nextMetrics.pending = buildMetric(0, false);
      }

      if (favRes.status === 'fulfilled' && favRes.value.ok) {
        const data = await favRes.value.json();
        nextMetrics.favorites = buildMetric(data.count || 0, true);
        successCount += 1;
      } else {
        nextMetrics.favorites = buildMetric(0, false);
      }

      if (msgRes.status === 'fulfilled' && msgRes.value.ok) {
        const data = await msgRes.value.json();
        nextMetrics.messages = buildMetric(data.count || 0, true);
        successCount += 1;
      } else {
        nextMetrics.messages = buildMetric(0, false);
      }

      if (listingsRes.status === 'fulfilled' && listingsRes.value.ok) {
        const data = await listingsRes.value.json();
        setListings(data.items || []);
        setListingsReady(true);
        successCount += 1;
      } else {
        setListings([]);
        setListingsReady(false);
      }

      if (meRes.status === 'fulfilled' && meRes.value.ok) {
        const data = await meRes.value.json();
        setStatusChecks((prev) => ({
          ...prev,
          emailVerified: Boolean(data.is_verified),
        }));
      }

      if (twoFaRes.status === 'fulfilled' && twoFaRes.value.ok) {
        const data = await twoFaRes.value.json();
        setStatusChecks((prev) => ({
          ...prev,
          twoFactorEnabled: Boolean(data.enabled),
        }));
      }

      setMetrics(nextMetrics);

      if (successCount === 0) {
        setError('Dashboard verileri alınamadı');
      } else {
        setError('');
      }

      if (active) {
        setLoading(false);
      }
    };

    fetchDashboard();

    return () => {
      active = false;
    };
  }, []);

  const shouldDisableCTA = quotaInfo.ready && quotaInfo.remaining <= 0;
  const quotaLabel = quotaInfo.ready ? `${quotaInfo.remaining}` : '0';

  const statusItems = useMemo(() => {
    const items = [];
    const hasEmailIssue = !statusChecks.emailVerified;
    const hasTwoFaIssue = !statusChecks.twoFactorEnabled;

    if (hasEmailIssue) {
      items.push({
        key: 'email',
        icon: Mail,
        text: 'E-posta doğrulanmadı',
        testId: 'account-status-email',
      });
    }
    if (hasTwoFaIssue) {
      items.push({
        key: '2fa',
        icon: ShieldAlert,
        text: '2FA aktif değil',
        testId: 'account-status-2fa',
      });
    }

    const showQuotaWarning = quotaInfo.ready ? quotaInfo.remaining <= 1 : false;
    const includeQuota = hasEmailIssue || hasTwoFaIssue || showQuotaWarning;
    if (includeQuota) {
      items.push({
        key: 'quota',
        icon: AlertTriangle,
        text: `Kalan ücretsiz ilan: ${quotaLabel}${quotaInfo.ready ? '' : ' (Veri hazırlanıyor)'}`,
        testId: 'account-status-quota',
      });
    }

    return items;
  }, [quotaInfo.ready, quotaInfo.remaining, quotaLabel, statusChecks.emailVerified, statusChecks.twoFactorEnabled]);

  const kpiCards = useMemo(
    () => [
      {
        key: 'active',
        label: 'Yayında İlan',
        icon: CheckCircle,
        metric: metrics.active,
        testId: 'account-kpi-active',
      },
      {
        key: 'pending',
        label: 'Bekleyen İlan',
        icon: Clock,
        metric: metrics.pending,
        testId: 'account-kpi-pending',
      },
      {
        key: 'favorites',
        label: 'Favoriye Eklenen',
        icon: Heart,
        metric: metrics.favorites,
        testId: 'account-kpi-favorites',
      },
      {
        key: 'messages',
        label: 'Gelen Mesaj (30g)',
        icon: Mail,
        metric: metrics.messages,
        testId: 'account-kpi-messages',
      },
    ],
    [metrics]
  );

  if (loading) {
    return <LoadingState label="Dashboard yükleniyor..." />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  return (
    <div className="space-y-8" data-testid="account-dashboard">
      <div className="flex flex-wrap items-center justify-between gap-4" data-testid="account-dashboard-header">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]" data-testid="account-dashboard-title">
            Hoş geldiniz
          </h1>
          <p className="text-sm text-[var(--text-secondary)]" data-testid="account-dashboard-subtitle">
            Bugün hangi işlemi yapmak istersiniz?
          </p>
        </div>
      </div>

      {statusItems.length > 0 && (
        <div
          className="rounded-2xl border border-[var(--border-warm)] bg-[var(--bg-soft)] px-4 py-3"
          data-testid="account-status-banner"
        >
          <div className="text-xs font-semibold text-[var(--text-primary)]" data-testid="account-status-title">
            Hesap Durumu
          </div>
          <div className="mt-2 flex flex-wrap gap-3" data-testid="account-status-items">
            {statusItems.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.key}
                  className="flex items-center gap-2 rounded-full bg-white px-3 py-1 text-xs text-[var(--text-secondary)]"
                  data-testid={item.testId}
                >
                  <Icon size={14} />
                  {item.text}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4" data-testid="account-kpi-row">
        {kpiCards.map((card) => {
          const Icon = card.icon;
          const isPassive = card.metric.value === 0;
          return (
            <div
              key={card.key}
              className="rounded-2xl border bg-white p-4 shadow-sm"
              data-testid={card.testId}
            >
              <div className="flex items-center justify-between" data-testid={`${card.testId}-header`}>
                <div className="text-xs uppercase tracking-[0.2em] text-[var(--text-secondary)]" data-testid={`${card.testId}-label`}>
                  {card.label}
                </div>
                <Icon size={18} className="text-[var(--text-secondary)]" data-testid={`${card.testId}-icon`} />
              </div>
              <div
                className={`mt-3 text-3xl font-semibold ${isPassive ? 'text-slate-300' : 'text-[var(--text-primary)]'}`}
                data-testid={`${card.testId}-value`}
              >
                {card.metric.value}
              </div>
              {!card.metric.ready && (
                <div className="mt-1 text-[11px] text-slate-400" data-testid={`${card.testId}-pending`}>
                  Veri hazırlanıyor
                </div>
              )}
            </div>
          );
        })}
      </div>

      <div className="rounded-2xl border bg-white p-6 shadow-sm" data-testid="account-primary-cta">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <div className="text-xl font-semibold text-[var(--text-primary)]" data-testid="account-cta-title">
              Hemen İlan Ver
            </div>
            <p className="mt-2 text-sm text-[var(--text-secondary)]" data-testid="account-cta-description">
              İlan oluşturma sihirbazıyla birkaç dakikada yayına çıkın.
            </p>
            <div className="mt-3 text-xs text-[var(--text-secondary)]" data-testid="account-cta-quota">
              Kalan ücretsiz ilan hakkı: {quotaLabel}
              {!quotaInfo.ready && <span data-testid="account-cta-quota-loading"> • Veri hazırlanıyor</span>}
            </div>
            {shouldDisableCTA && (
              <div className="mt-1 text-xs text-rose-600" data-testid="account-cta-disabled-reason">
                Ücretsiz ilan hakkınız doldu. Paketinizi yükseltin.
              </div>
            )}
          </div>
          <Link
            to="/ilan-ver/kategori-secimi"
            className={`inline-flex items-center justify-center gap-2 rounded-full px-6 py-3 text-sm font-semibold text-white ${
              shouldDisableCTA ? 'bg-slate-300 pointer-events-none' : 'bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)]'
            }`}
            data-testid="account-cta-button"
            aria-disabled={shouldDisableCTA}
          >
            <PlusCircle size={18} /> Hemen İlan Ver
          </Link>
        </div>
      </div>

      <div className="rounded-2xl border bg-white p-6 shadow-sm" data-testid="account-listing-snapshot">
        <div className="flex flex-wrap items-center justify-between gap-3" data-testid="account-listing-snapshot-header">
          <div>
            <div className="text-lg font-semibold text-[var(--text-primary)]" data-testid="account-listing-snapshot-title">
              Son İlanlarım
            </div>
            <p className="text-xs text-[var(--text-secondary)]" data-testid="account-listing-snapshot-subtitle">
              Son 5 ilanınızın durumunu hızlıca görüntüleyin.
            </p>
          </div>
          <Link
            to="/account/listings"
            className="text-xs font-semibold text-[#F57C00]"
            data-testid="account-listing-snapshot-viewall"
          >
            Tümünü gör
          </Link>
        </div>

        <div className="mt-4 space-y-3" data-testid="account-listing-snapshot-list">
          {!listingsReady ? (
            <div className="text-xs text-slate-400" data-testid="account-listing-snapshot-loading">
              Veri hazırlanıyor
            </div>
          ) : listings.length === 0 ? (
            <EmptyState
              title="Henüz ilan yok"
              description="İlk ilanınızı oluşturmak için hemen başlayın."
              actionLabel="İlan Ver"
              onAction={() => (window.location.href = '/ilan-ver/kategori-secimi')}
              testId="account-listing-snapshot-empty"
            />
          ) : (
            listings.map((listing) => {
              const statusKey = resolveStatus(listing.status);
              const meta = statusMeta[statusKey];
              const reasonText = listing.moderation_reason || 'N/A';
              return (
                <div
                  key={listing.id}
                  className="flex flex-wrap items-center justify-between gap-3 rounded-xl border px-4 py-3"
                  data-testid={`account-listing-row-${listing.id}`}
                >
                  <div data-testid={`account-listing-title-${listing.id}`}>
                    <div className="text-sm font-semibold text-[var(--text-primary)]">
                      {listing.title || 'Başlıksız ilan'}
                    </div>
                    <div className="text-xs text-[var(--text-secondary)]" data-testid={`account-listing-status-${listing.id}`}>
                      Durum: {meta.label}
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-3" data-testid={`account-listing-actions-${listing.id}`}>
                    <span
                      className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${meta.tone}`}
                      data-testid={`account-listing-badge-${listing.id}`}
                    >
                      {meta.label}
                    </span>
                    <div
                      className="relative group inline-flex items-center gap-1 text-xs text-[var(--text-secondary)]"
                      data-testid={`account-listing-reason-${listing.id}`}
                    >
                      <Info size={14} data-testid={`account-listing-reason-icon-${listing.id}`} />
                      <span>Neden</span>
                      <span
                        className="pointer-events-none absolute -top-10 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-900 px-2 py-1 text-[11px] text-white opacity-0 shadow transition group-hover:opacity-100"
                        data-testid={`account-listing-reason-tooltip-${listing.id}`}
                      >
                        Moderation nedeni: {reasonText}
                      </span>
                    </div>
                    <Link
                      to={`/account/create/vehicle-wizard?edit=${listing.id}`}
                      className="inline-flex items-center gap-1 rounded-full border px-3 py-1 text-xs font-semibold text-[var(--text-primary)]"
                      data-testid={`account-listing-edit-${listing.id}`}
                    >
                      <Pencil size={14} /> Hızlı Düzenle
                    </Link>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2" data-testid="account-favorites-saved-searches">
        <div className="rounded-2xl border bg-white p-5 shadow-sm" data-testid="account-favorites-card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-[0.2em] text-[var(--text-secondary)]" data-testid="account-favorites-label">
                Favoriler
              </div>
              <div
                className={`mt-2 text-3xl font-semibold ${metrics.favorites.value === 0 ? 'text-slate-300' : 'text-[var(--text-primary)]'}`}
                data-testid="account-favorites-count"
              >
                {metrics.favorites.value}
              </div>
              {!metrics.favorites.ready && (
                <div className="mt-1 text-[11px] text-slate-400" data-testid="account-favorites-loading">
                  Veri hazırlanıyor
                </div>
              )}
            </div>
            <Link
              to="/account/favorites"
              className="text-xs font-semibold text-[#F57C00]"
              data-testid="account-favorites-viewall"
            >
              Tümünü gör
            </Link>
          </div>
        </div>

        <div className="rounded-2xl border bg-white p-5 shadow-sm" data-testid="account-saved-searches-card">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs uppercase tracking-[0.2em] text-[var(--text-secondary)]" data-testid="account-saved-searches-label">
                Kayıtlı Aramalar
              </div>
              <div
                className={`mt-2 text-3xl font-semibold ${metrics.savedSearches.value === 0 ? 'text-slate-300' : 'text-[var(--text-primary)]'}`}
                data-testid="account-saved-searches-count"
              >
                {metrics.savedSearches.value}
              </div>
              {!metrics.savedSearches.ready && (
                <div className="mt-1 text-[11px] text-slate-400" data-testid="account-saved-searches-loading">
                  Veri hazırlanıyor
                </div>
              )}
            </div>
            <button
              type="button"
              className="text-xs font-semibold text-slate-400"
              data-testid="account-saved-searches-viewall"
              disabled
            >
              Tümünü gör
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
