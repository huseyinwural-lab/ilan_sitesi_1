import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useLanguage } from '@/contexts/LanguageContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const sectionTabs = [
  { key: 'hourly_visit_report', labelKey: 'dealer.reports.sections.hourly_visit_report', fallback: 'Saatlik Ziyaret Sayısı' },
  { key: 'listing_report', labelKey: 'dealer.reports.sections.listing_report', fallback: 'Yayındaki İlan Raporu' },
  { key: 'views_report', labelKey: 'dealer.reports.sections.views_report', fallback: 'Görüntülenme Raporu' },
  { key: 'favorites_report', labelKey: 'dealer.reports.sections.favorites_report', fallback: 'Favoriye Alınma Raporu' },
  { key: 'messages_report', labelKey: 'dealer.reports.sections.messages_report', fallback: 'Gelen Mesaj Raporu' },
  { key: 'mobile_calls_report', labelKey: 'dealer.reports.sections.mobile_calls_report', fallback: 'Gelen Arama Raporu (Mobil)' },
  { key: 'package_reports', labelKey: 'dealer.reports.sections.package_reports', fallback: 'Paket Raporları' },
  { key: 'doping_usage', labelKey: 'dealer.reports.sections.doping_usage', fallback: 'Doping Kullanım Raporu' },
];

const formatDate = (value, language = 'tr') => {
  if (!value) return '-';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';
  const localeMap = { tr: 'tr-TR', de: 'de-DE', fr: 'fr-FR' };
  return date.toLocaleDateString(localeMap[language] || 'tr-TR');
};

export default function DealerReports() {
  const { t, language } = useLanguage();
  const [searchParams, setSearchParams] = useSearchParams();
  const [windowDays, setWindowDays] = useState(30);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [kpis, setKpis] = useState({ views_7d: 0, contact_clicks_7d: 0 });
  const [reportSections, setReportSections] = useState({});
  const [packageReports, setPackageReports] = useState({ usage_rows: [] });
  const [dopingUsage, setDopingUsage] = useState({ total_used: 0, total_views: 0, series_used: [], series_views: [] });

  const activeSection = useMemo(() => {
    const requested = searchParams.get('section');
    if (sectionTabs.some((item) => item.key === requested)) return requested;
    return 'listing_report';
  }, [searchParams]);

  const activeReport = useMemo(() => {
    if (activeSection === 'package_reports' || activeSection === 'doping_usage') return null;
    if (activeSection === 'hourly_visit_report') return reportSections?.views_report || null;
    return reportSections?.[activeSection] || null;
  }, [activeSection, reportSections]);

  const lineSeries = useMemo(() => {
    if (!activeReport?.series?.length) return [];
    return activeReport.series.map((item, index) => ({
      x: index,
      label: item.label || item.date,
      value: Number(item.value || 0),
    }));
  }, [activeReport]);

  const lineSvgPath = useMemo(() => {
    if (!lineSeries.length) return '';
    const width = 720;
    const height = 180;
    const maxVal = Math.max(...lineSeries.map((item) => item.value), 1);
    return lineSeries.map((item, index) => {
      const x = (index / Math.max(lineSeries.length - 1, 1)) * width;
      const y = height - (item.value / maxVal) * (height - 20);
      return `${index === 0 ? 'M' : 'L'}${x},${y}`;
    }).join(' ');
  }, [lineSeries]);

  const fetchData = async (days = windowDays) => {
    setLoading(true);
    setError('');
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(`${API}/dealer/reports?window_days=${days}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const payload = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(payload?.detail || t('dealer.reports.errors.fetch_failed', 'Rapor verisi alınamadı'));
      setKpis(payload?.kpis || { views_7d: 0, contact_clicks_7d: 0 });
      setReportSections(payload?.report_sections || {});
      setPackageReports(payload?.package_reports || { usage_rows: [] });
      setDopingUsage(payload?.doping_usage_report || { total_used: 0, total_views: 0, series_used: [], series_views: [] });
    } catch (err) {
      setError(err?.message || t('dealer.reports.errors.fetch_failed', 'Rapor verisi alınamadı'));
      setKpis({ views_7d: 0, contact_clicks_7d: 0 });
      setReportSections({});
      setPackageReports({ usage_rows: [] });
      setDopingUsage({ total_used: 0, total_views: 0, series_used: [], series_views: [] });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSectionClick = (sectionKey) => {
    setSearchParams({ section: sectionKey });
  };

  const handleWindowChange = (days) => {
    setWindowDays(days);
    fetchData(days);
  };

  return (
    <div className="space-y-4" data-testid="dealer-reports-page">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="dealer-reports-header">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900" data-testid="dealer-reports-title">{t('dealer.reports.title', 'Raporlar')}</h1>
          <p className="text-sm font-medium text-slate-700" data-testid="dealer-reports-subtitle">{t('dealer.reports.subtitle', 'Performans, paket ve doping raporlarını tek ekrandan takip edin.')}</p>
        </div>
        <button
          type="button"
          onClick={() => fetchData(windowDays)}
          className="h-9 rounded-md border border-slate-300 px-3 text-sm font-semibold text-slate-900"
          data-testid="dealer-reports-refresh-button"
        >
          {t('dealer.reports.refresh', 'Yenile')}
        </button>
      </div>

      {error ? <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700" data-testid="dealer-reports-error">{error}</div> : null}

      <div className="grid gap-4 md:grid-cols-2" data-testid="dealer-reports-kpi-grid">
        <div className="rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-reports-views-card">
          <div className="text-xs uppercase tracking-[0.2em] font-semibold text-slate-700" data-testid="dealer-reports-views-label">{t('dealer.reports.kpi.views_7d', 'Son 7 Gün Görüntülenme')}</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900" data-testid="dealer-reports-views-value">{kpis.views_7d || 0}</div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-reports-contact-card">
          <div className="text-xs uppercase tracking-[0.2em] font-semibold text-slate-700" data-testid="dealer-reports-contact-label">{t('dealer.reports.kpi.contact_clicks', 'Lead/İletişim Tıklaması')}</div>
          <div className="mt-2 text-3xl font-semibold text-slate-900" data-testid="dealer-reports-contact-value">{kpis.contact_clicks_7d || 0}</div>
        </div>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-4" data-testid="dealer-reports-toolbar">
        <div className="flex flex-wrap items-center gap-2" data-testid="dealer-reports-window-filter">
          {[7, 14, 30, 90].map((days) => (
            <button
              key={days}
              type="button"
              onClick={() => handleWindowChange(days)}
              className={`rounded-full border px-3 py-1.5 text-xs font-semibold ${windowDays === days ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
              data-testid={`dealer-reports-window-${days}`}
            >
              {t('dealer.reports.days', '{{days}} Gün', { days })}
            </button>
          ))}
        </div>
        <div className="mt-3 flex flex-wrap items-center gap-2" data-testid="dealer-reports-section-tabs">
          {sectionTabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              onClick={() => handleSectionClick(tab.key)}
              className={`rounded-md border px-3 py-1.5 text-xs font-semibold ${activeSection === tab.key ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
              data-testid={`dealer-reports-section-tab-${tab.key}`}
            >
              {t(tab.labelKey, tab.fallback)}
            </button>
          ))}
        </div>
      </div>

      {loading ? <div className="rounded-md border p-4 text-sm text-slate-500" data-testid="dealer-reports-loading">{t('dealer.reports.loading', 'Yükleniyor...')}</div> : null}

      {!loading && activeReport ? (
        <div className="space-y-4" data-testid="dealer-reports-section-default">
          <div className="rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-reports-current-card">
            <div className="text-sm font-semibold text-slate-900" data-testid="dealer-reports-current-title">{t(`dealer.reports.sections.${activeSection}`, activeReport.title)}</div>
            <div className="mt-3 grid gap-3 md:grid-cols-4" data-testid="dealer-reports-current-metrics-grid">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="dealer-reports-current-value-card">
                <div className="text-xs font-semibold text-slate-700">{t('dealer.reports.metrics.current_period', 'Mevcut Dönem')}</div>
                <div className="text-2xl font-semibold text-slate-900" data-testid="dealer-reports-current-value">{activeReport.current_value || 0}</div>
              </div>
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="dealer-reports-previous-value-card">
                <div className="text-xs font-semibold text-slate-700">{t('dealer.reports.metrics.previous_period', 'Önceki Dönem')}</div>
                <div className="text-2xl font-semibold text-slate-900" data-testid="dealer-reports-previous-value">{activeReport.previous_value || 0}</div>
              </div>
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="dealer-reports-change-card">
                <div className="text-xs font-semibold text-slate-700">{t('dealer.reports.metrics.change', 'Değişim')}</div>
                <div className={`text-2xl font-semibold ${(activeReport.change_pct || 0) >= 0 ? 'text-emerald-700' : 'text-rose-700'}`} data-testid="dealer-reports-change-value">{activeReport.change_pct || 0}%</div>
              </div>
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="dealer-reports-total-card">
                <div className="text-xs font-semibold text-slate-700">{t('dealer.reports.metrics.total', 'Toplam')}</div>
                <div className="text-2xl font-semibold text-slate-900" data-testid="dealer-reports-total-value">{activeReport.total || 0}</div>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-reports-series-card">
            <div className="text-sm font-semibold text-slate-900" data-testid="dealer-reports-series-title">{t('dealer.reports.series.title', 'Günlük Seri')}</div>
            {activeSection === 'hourly_visit_report' ? (
              <div className="mt-3 overflow-x-auto" data-testid="dealer-reports-hourly-line-chart-wrap">
                <svg viewBox="0 0 720 180" className="h-44 w-full min-w-[640px]" data-testid="dealer-reports-hourly-line-chart">
                  <path d={lineSvgPath} fill="none" stroke="#0f172a" strokeWidth="2" />
                </svg>
              </div>
            ) : null}
            <div className="mt-3 overflow-x-auto" data-testid="dealer-reports-series-table-wrap">
              <table className="w-full text-sm" data-testid="dealer-reports-series-table">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-3 py-2 text-left text-slate-800">{t('dealer.reports.table.date', 'Tarih')}</th>
                    <th className="px-3 py-2 text-left text-slate-800">{t('dealer.reports.table.value', 'Değer')}</th>
                  </tr>
                </thead>
                <tbody>
                  {(activeReport.series || []).map((row) => (
                    <tr key={row.date} className="border-t" data-testid={`dealer-reports-series-row-${row.date}`}>
                      <td className="px-3 py-2">{row.label || row.date}</td>
                      <td className="px-3 py-2 font-semibold">{row.value || 0}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}

      {!loading && activeSection === 'package_reports' ? (
        <div className="rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-reports-package-section">
          <div className="text-sm font-semibold text-slate-900" data-testid="dealer-reports-package-title">{packageReports.package_name || t('dealer.reports.package.title', 'Paket Raporu')}</div>
          <div className="mt-1 text-xs text-slate-600" data-testid="dealer-reports-package-period">{formatDate(packageReports?.period?.start, language)} - {formatDate(packageReports?.period?.end, language)}</div>
          <div className="mt-3 grid gap-3 md:grid-cols-3" data-testid="dealer-reports-package-metrics-grid">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="dealer-reports-package-used-card"><div className="text-xs font-semibold text-slate-700">{t('dealer.reports.package.used', 'Kullanılan')}</div><div className="text-2xl font-semibold text-slate-900">{packageReports.used || 0}</div></div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="dealer-reports-package-remaining-card"><div className="text-xs font-semibold text-slate-700">{t('dealer.reports.package.remaining', 'Kalan')}</div><div className="text-2xl font-semibold text-slate-900">{packageReports.remaining || 0}</div></div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="dealer-reports-package-quota-card"><div className="text-xs font-semibold text-slate-700">{t('dealer.reports.package.limit', 'Limit')}</div><div className="text-2xl font-semibold text-slate-900">{packageReports.quota_limit || 0}</div></div>
          </div>
          <div className="mt-3 overflow-x-auto" data-testid="dealer-reports-package-table-wrap">
            <table className="w-full text-sm" data-testid="dealer-reports-package-table">
              <thead className="bg-slate-50"><tr><th className="px-3 py-2 text-left text-slate-800">{t('dealer.reports.package.table.listing', 'İlan')}</th><th className="px-3 py-2 text-left text-slate-800">{t('dealer.reports.package.table.usage_type', 'Kullanım Tipi')}</th><th className="px-3 py-2 text-left text-slate-800">{t('dealer.reports.table.date', 'Tarih')}</th></tr></thead>
              <tbody>
                {(packageReports.usage_rows || []).length === 0 ? (
                  <tr><td className="px-3 py-4 text-slate-600" colSpan={3} data-testid="dealer-reports-package-empty">{t('dealer.reports.empty', 'Kayıt yok')}</td></tr>
                ) : (packageReports.usage_rows || []).map((row) => (
                  <tr key={row.listing_id} className="border-t" data-testid={`dealer-reports-package-row-${row.listing_id}`}>
                    <td className="px-3 py-2 font-medium text-slate-900">{row.listing_title || '-'}</td>
                    <td className="px-3 py-2">{row.usage_type || '-'}</td>
                    <td className="px-3 py-2">{formatDate(row.date, language)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}

      {!loading && activeSection === 'doping_usage' ? (
        <div className="rounded-xl border border-slate-200 bg-white p-4" data-testid="dealer-reports-doping-section">
          <div className="text-sm font-semibold text-slate-900" data-testid="dealer-reports-doping-title">{t('dealer.reports.sections.doping_usage', 'Doping Kullanım Raporu')}</div>
          <div className="mt-3 grid gap-3 md:grid-cols-2" data-testid="dealer-reports-doping-metrics-grid">
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="dealer-reports-doping-total-used-card"><div className="text-xs font-semibold text-slate-700">{t('dealer.reports.doping.total_doping', 'Toplam Doping')}</div><div className="text-2xl font-semibold text-slate-900">{dopingUsage.total_used || 0}</div></div>
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3" data-testid="dealer-reports-doping-total-views-card"><div className="text-xs font-semibold text-slate-700">{t('dealer.reports.doping.total_views', 'Toplam Görüntülenme')}</div><div className="text-2xl font-semibold text-slate-900">{dopingUsage.total_views || 0}</div></div>
          </div>
          <div className="mt-3 overflow-x-auto" data-testid="dealer-reports-doping-table-wrap">
            <table className="w-full text-sm" data-testid="dealer-reports-doping-table">
              <thead className="bg-slate-50"><tr><th className="px-3 py-2 text-left text-slate-800">{t('dealer.reports.table.date', 'Tarih')}</th><th className="px-3 py-2 text-left text-slate-800">{t('dealer.reports.doping.doping', 'Doping')}</th><th className="px-3 py-2 text-left text-slate-800">{t('dealer.reports.table.views', 'Görüntülenme')}</th></tr></thead>
              <tbody>
                {(dopingUsage.series_views || []).map((row, idx) => {
                  const used = dopingUsage.series_used?.[idx]?.value || 0;
                  return (
                    <tr key={row.date} className="border-t" data-testid={`dealer-reports-doping-row-${row.date}`}>
                      <td className="px-3 py-2">{row.label || row.date}</td>
                      <td className="px-3 py-2 font-semibold">{used}</td>
                      <td className="px-3 py-2 font-semibold">{row.value || 0}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  );
}
