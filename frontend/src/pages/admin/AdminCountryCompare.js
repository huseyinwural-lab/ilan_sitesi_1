import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';
import { ArrowDownUp, BarChart3, Download, Filter, Info } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PERIOD_OPTIONS = [
  { value: 'today', label: 'Bugün' },
  { value: '7d', label: 'Son 7 Gün' },
  { value: '30d', label: 'Son 30 Gün' },
  { value: 'mtd', label: 'MTD' },
  { value: 'custom', label: 'Özel' },
];

const METRIC_OPTIONS = [
  { value: 'total_listings', label: 'Total Listings' },
  { value: 'revenue_eur', label: 'Revenue (EUR)' },
  { value: 'active_dealers', label: 'Active Dealers' },
];

const formatNumber = (value) => {
  if (value === null || value === undefined) return '-';
  return Number(value).toLocaleString('tr-TR');
};

const formatPercent = (value) => {
  if (value === null || value === undefined) return '-';
  const sign = value > 0 ? '+' : '';
  return `${sign}${Number(value).toFixed(2)}%`;
};

const formatRatio = (value) => {
  if (value === null || value === undefined) return '-';
  return `${Number(value).toFixed(2)}%`;
};

const buildCurrencyTooltip = (totals) => {
  if (!totals) return 'Yerel para birimi verisi yok';
  const entries = Object.entries(totals);
  if (entries.length === 0) return 'Yerel para birimi verisi yok';
  return entries.map(([currency, amount]) => `${Number(amount).toLocaleString('tr-TR')} ${currency}`).join(' · ');
};

const cellTestId = (code, key) => `country-compare-${code}-${key}`;

export default function AdminCountryComparePage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [financeVisible, setFinanceVisible] = useState(false);
  const [period, setPeriod] = useState('30d');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');
  const [sortBy, setSortBy] = useState('');
  const [sortDir, setSortDir] = useState('desc');
  const [compareMetric, setCompareMetric] = useState('revenue_eur');
  const [selectedCountries, setSelectedCountries] = useState([]);
  const [selectionInitialized, setSelectionInitialized] = useState(false);
  const [compareError, setCompareError] = useState('');
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState('');
  const [fxInfo, setFxInfo] = useState(null);
  const [periodLabel, setPeriodLabel] = useState('');
  const [periodRange, setPeriodRange] = useState('');
  const [error, setError] = useState('');
  const { user } = useAuth();

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const showRevenue = financeVisible && ['finance', 'super_admin'].includes(user?.role);

  const sortOptions = useMemo(() => {
    const baseOptions = [
      { value: 'total_listings', label: 'Total Listings (desc)' },
      { value: 'growth_total_listings_7d', label: 'Listings Growth 7d (desc)' },
      { value: 'growth_total_listings_30d', label: 'Listings Growth 30d (desc)' },
      { value: 'growth_active_dealers_7d', label: 'Dealers Growth 7d (desc)' },
      { value: 'growth_published_7d', label: 'Published Growth 7d (desc)' },
    ];
    if (showRevenue) {
      baseOptions.unshift(
        { value: 'revenue_eur', label: 'Revenue (EUR) (desc)' },
        { value: 'growth_revenue_7d', label: 'Revenue Growth 7d (desc)' },
        { value: 'growth_revenue_30d', label: 'Revenue Growth 30d (desc)' },
        { value: 'revenue_mtd_growth_pct', label: 'Revenue MTD Growth % (desc)' },
      );
    }
    return baseOptions;
  }, [showRevenue]);

  const fetchCompare = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams();
      params.set('period', period);
      if (period === 'custom') {
        if (customStart) params.set('start_date', customStart);
        if (customEnd) params.set('end_date', customEnd);
      }
      if (sortBy) params.set('sort_by', sortBy);
      if (sortDir) params.set('sort_dir', sortDir);
      const qs = params.toString() ? `?${params.toString()}` : '';
      const res = await axios.get(`${API}/admin/dashboard/country-compare${qs}`, { headers: authHeader });
      setItems(res.data.items || []);
      setFinanceVisible(Boolean(res.data.finance_visible));
      setFxInfo(res.data.fx || null);
      setPeriodLabel(res.data.period_label || '');
      setPeriodRange(`${res.data.period_start || ''} → ${res.data.period_end || ''}`);
      if (!sortBy) {
        setSortBy(res.data.default_sort_by || 'total_listings');
        setSortDir(res.data.default_sort_dir || 'desc');
      }
    } catch (e) {
      console.error('Failed to fetch country compare', e);
      setItems([]);
      setFinanceVisible(false);
      setFxInfo(null);
      setError('Ülke karşılaştırma verileri yüklenemedi.');
    } finally {
      setLoading(false);
      setHasLoaded(true);
    }
  };

  useEffect(() => {
    fetchCompare();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [period, customStart, customEnd, sortBy, sortDir]);

  useEffect(() => {
    if (selectionInitialized || items.length === 0) return;
    const defaults = ['DE', 'CH', 'AT'];
    const available = items.map((item) => item.country_code);
    const initial = defaults.filter((code) => available.includes(code));
    setSelectedCountries(initial.length ? initial : available.slice(0, 3));
    setSelectionInitialized(true);
  }, [items, selectionInitialized]);

  useEffect(() => {
    if (!showRevenue && compareMetric === 'revenue_eur') {
      setCompareMetric('total_listings');
    }
  }, [showRevenue, compareMetric]);

  const handleCountryToggle = (code) => {
    setCompareError('');
    if (selectedCountries.includes(code)) {
      setSelectedCountries(selectedCountries.filter((item) => item !== code));
      return;
    }
    if (selectedCountries.length >= 3) {
      setCompareError('En fazla 3 ülke seçebilirsiniz.');
      return;
    }
    setSelectedCountries([...selectedCountries, code]);
  };

  const handleExportCsv = async () => {
    setExportError('');
    setExporting(true);
    try {
      const params = new URLSearchParams();
      params.set('period', period);
      if (period === 'custom') {
        if (customStart) params.set('start_date', customStart);
        if (customEnd) params.set('end_date', customEnd);
      }
      if (sortBy) params.set('sort_by', sortBy);
      if (sortDir) params.set('sort_dir', sortDir);
      const qs = params.toString() ? `?${params.toString()}` : '';
      const response = await axios.get(`${API}/admin/dashboard/country-compare/export/csv${qs}`, {
        headers: authHeader,
        responseType: 'blob',
      });
      const disposition = response.headers?.['content-disposition'] || '';
      const match = disposition.match(/filename="([^"]+)"/);
      const filename = match?.[1] || `country-compare-${period}.csv`;
      const url = window.URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setExportError('CSV dışa aktarma başarısız.');
    } finally {
      setExporting(false);
    }
  };

  const availableCountries = useMemo(() => items.map((item) => item.country_code), [items]);

  const filteredItems = useMemo(() => {
    if (selectedCountries.length === 0) return items;
    return items.filter((item) => selectedCountries.includes(item.country_code));
  }, [items, selectedCountries]);

  const comparisonCountries = useMemo(() => {
    if (selectedCountries.length > 0) {
      return filteredItems;
    }
    return filteredItems.slice(0, 3);
  }, [filteredItems, selectedCountries]);

  const metricValue = (item) => {
    if (compareMetric === 'revenue_eur') return item.revenue_eur || 0;
    if (compareMetric === 'active_dealers') return item.active_dealers || 0;
    return item.total_listings || 0;
  };

  const comparisonMax = Math.max(...comparisonCountries.map(metricValue), 1);
  const heatmapMax = Math.max(...filteredItems.map(metricValue), 1);

  const gridCols = showRevenue
    ? 'grid-cols-[0.7fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr]'
    : 'grid-cols-[0.7fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr_1fr]';

  return (
    <div className="space-y-6" data-testid="admin-country-compare-page">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold" data-testid="country-compare-title">Ülke Karşılaştırma</h1>
        <div className="text-xs text-muted-foreground" data-testid="country-compare-utc">All metrics in UTC</div>
      </div>

      <div className="bg-card rounded-md border p-4 space-y-4" data-testid="country-compare-controls">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex flex-col gap-2">
            <span className="text-xs text-muted-foreground">Tarih filtresi</span>
            <select
              className="h-9 rounded-md border bg-background px-3 text-sm"
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              data-testid="country-compare-period-select"
            >
              {PERIOD_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          {period === 'custom' && (
            <div className="flex items-end gap-3" data-testid="country-compare-custom-range">
              <div className="flex flex-col gap-2">
                <span className="text-xs text-muted-foreground">Başlangıç</span>
                <input
                  type="date"
                  value={customStart}
                  onChange={(e) => setCustomStart(e.target.value)}
                  className="h-9 rounded-md border bg-background px-3 text-sm"
                  data-testid="country-compare-custom-start"
                />
              </div>
              <div className="flex flex-col gap-2">
                <span className="text-xs text-muted-foreground">Bitiş</span>
                <input
                  type="date"
                  value={customEnd}
                  onChange={(e) => setCustomEnd(e.target.value)}
                  className="h-9 rounded-md border bg-background px-3 text-sm"
                  data-testid="country-compare-custom-end"
                />
              </div>
              <div className="text-xs text-muted-foreground">7-365 gün aralığı</div>
            </div>
          )}
          <div className="flex flex-col gap-2">
            <span className="text-xs text-muted-foreground">Sıralama</span>
            <div className="flex items-center gap-2">
              <select
                className="h-9 rounded-md border bg-background px-3 text-sm"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                data-testid="country-compare-sort-select"
              >
                {sortOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              <button
                type="button"
                className="h-9 w-9 rounded-md border flex items-center justify-center"
                onClick={() => setSortDir(sortDir === 'desc' ? 'asc' : 'desc')}
                data-testid="country-compare-sort-direction"
              >
                <ArrowDownUp size={16} />
              </button>
            </div>
          </div>
          <div className="flex flex-col gap-2">
            <span className="text-xs text-muted-foreground">CSV Export</span>
            <button
              type="button"
              className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium flex items-center gap-2 disabled:opacity-50"
              onClick={handleExportCsv}
              disabled={exporting}
              data-testid="country-compare-export-csv"
            >
              <Download size={16} />
              {exporting ? 'Hazırlanıyor' : 'CSV indir'}
            </button>
          </div>
        </div>
        {exportError && (
          <div className="text-sm text-rose-600" data-testid="country-compare-export-error">{exportError}</div>
        )}
        {fxInfo && (
          <div className="text-xs text-muted-foreground flex flex-wrap items-center gap-2" data-testid="country-compare-fx-info">
            <span>ECB kur kaynağı · Baz: {fxInfo.base}</span>
            <span>Son güncelleme: {fxInfo.as_of || 'unknown'}</span>
            {fxInfo.fallback && (
              <span className="text-amber-600" data-testid="country-compare-fx-fallback">Son başarılı kur kullanılıyor</span>
            )}
            {fxInfo.missing_currencies?.length > 0 && (
              <span data-testid="country-compare-fx-missing">Eksik kur: {fxInfo.missing_currencies.join(', ')}</span>
            )}
          </div>
        )}
        {periodLabel && (
          <div className="text-xs text-muted-foreground" data-testid="country-compare-period-label">
            {periodLabel} · {periodRange}
          </div>
        )}
        {error && (
          <div className="text-sm text-rose-600" data-testid="country-compare-error">{error}</div>
        )}
      </div>

      <div className="bg-card rounded-md border p-4" data-testid="country-compare-selection">
        <div className="flex items-center gap-2 text-sm font-medium">
          <Filter size={16} /> Karşılaştırma Ülkeleri (2-3)
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-3" data-testid="country-compare-country-list">
          {availableCountries.map((code) => (
            <label key={code} className="flex items-center gap-2 text-sm" data-testid={`country-compare-country-${code}`}>
              <input
                type="checkbox"
                checked={selectedCountries.includes(code)}
                onChange={() => handleCountryToggle(code)}
                data-testid={`country-compare-country-toggle-${code}`}
              />
              {code}
            </label>
          ))}
        </div>
        {compareError && (
          <div className="text-xs text-rose-600 mt-2" data-testid="country-compare-selection-error">{compareError}</div>
        )}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="bg-card rounded-md border p-6" data-testid="country-compare-bar-chart">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs text-muted-foreground">Bar Chart Karşılaştırma</div>
              <div className="text-lg font-semibold">Seçili Metriğe Göre</div>
            </div>
            <select
              className="h-9 rounded-md border bg-background px-3 text-sm"
              value={compareMetric}
              onChange={(e) => setCompareMetric(e.target.value)}
              data-testid="country-compare-metric-select"
            >
              {METRIC_OPTIONS.filter((option) => showRevenue || option.value !== 'revenue_eur').map((option) => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
          </div>
          {comparisonCountries.length < 2 ? (
            <div className="text-xs text-muted-foreground mt-6" data-testid="country-compare-bar-empty">
              En az 2 ülke seçerek karşılaştırma grafiğini görüntüleyin.
            </div>
          ) : (
            <div className="mt-6 space-y-4" data-testid="country-compare-bar-list">
              {comparisonCountries.map((item) => {
                const value = metricValue(item);
                const width = Math.max(8, (value / comparisonMax) * 100);
                return (
                  <div key={item.country_code} className="space-y-1" data-testid={`country-compare-bar-row-${item.country_code}`}>
                    <div className="flex items-center justify-between text-sm">
                      <span>{item.country_code}</span>
                      <span data-testid={`country-compare-bar-value-${item.country_code}`}>{formatNumber(value)}</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-primary"
                        style={{ width: `${width}%` }}
                        data-testid={`country-compare-bar-${item.country_code}`}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="bg-card rounded-md border p-6" data-testid="country-compare-heatmap">
          <div className="flex items-center gap-2">
            <BarChart3 size={18} />
            <div>
              <div className="text-xs text-muted-foreground">Heatmap</div>
              <div className="text-lg font-semibold">En Yüksek Performans</div>
            </div>
          </div>
          <div className="mt-6 space-y-3" data-testid="country-compare-heatmap-list">
            {items.slice(0, 5).map((item) => {
              const value = metricValue(item);
              const intensity = Math.max(0.15, value / heatmapMax);
              return (
                <div
                  key={item.country_code}
                  className="flex items-center justify-between text-sm rounded-md px-3 py-2"
                  style={{ backgroundColor: `rgba(37, 99, 235, ${Math.min(intensity, 0.35)})` }}
                  data-testid={`country-compare-heat-${item.country_code}`}
                >
                  <span>{item.country_code}</span>
                  <span data-testid={`country-compare-heat-value-${item.country_code}`}>{formatNumber(value)}</span>
                </div>
              );
            })}
          </div>
          <div className="text-xs text-muted-foreground mt-4" data-testid="country-compare-heatmap-note">
            Heatmap, seçilen metriğe göre ülkeleri öne çıkarır.
          </div>
        </div>
      </div>

      <div className="rounded-md border bg-card overflow-hidden" data-testid="country-compare-table">
        <div className="px-4 py-2 text-xs text-muted-foreground flex items-center gap-2" data-testid="country-compare-table-note">
          <Info size={14} /> Tablo verileri {periodLabel || period} aralığını temsil eder.
        </div>
        <div className="overflow-x-auto" data-testid="country-compare-table-scroll">
          <div className={`min-w-[1400px] grid ${gridCols} gap-4 bg-muted px-4 py-3 text-xs font-semibold uppercase`}>
            <div data-testid="country-compare-header-country">Ülke</div>
            <div data-testid="country-compare-header-total">Total</div>
            <div data-testid="country-compare-header-growth7">Growth 7d</div>
            <div data-testid="country-compare-header-growth30">Growth 30d</div>
            <div data-testid="country-compare-header-published">Published</div>
            <div data-testid="country-compare-header-published-growth7">Pub 7d</div>
            <div data-testid="country-compare-header-published-growth30">Pub 30d</div>
            <div data-testid="country-compare-header-conversion">Conversion %</div>
            <div data-testid="country-compare-header-dealers">Dealers</div>
            <div data-testid="country-compare-header-dealers-growth7">Dealers 7d</div>
            <div data-testid="country-compare-header-dealers-growth30">Dealers 30d</div>
            <div data-testid="country-compare-header-density">Dealer Density</div>
            {showRevenue && <div data-testid="country-compare-header-revenue">Revenue (EUR)</div>}
            {showRevenue && <div data-testid="country-compare-header-rev-growth7">Rev 7d</div>}
            {showRevenue && <div data-testid="country-compare-header-rev-growth30">Rev 30d</div>}
            {showRevenue && <div data-testid="country-compare-header-rev-mtd">Rev MTD %</div>}
            <div data-testid="country-compare-header-sla24">SLA 24h</div>
            <div data-testid="country-compare-header-sla48">SLA 48h</div>
            <div data-testid="country-compare-header-risk-login">Risk Login</div>
            <div data-testid="country-compare-header-risk-payment">Risk Payment</div>
            <div data-testid="country-compare-header-note">Not</div>
          </div>
          <div className="divide-y">
            {loading && !hasLoaded ? (
              <div className="p-6 text-center" data-testid="country-compare-loading">Yükleniyor…</div>
            ) : items.length === 0 ? (
              <div className="p-6 text-center text-muted-foreground" data-testid="country-compare-empty">Kayıt yok</div>
            ) : (
              items.map((item) => {
                const heatIntensity = Math.max(0.05, metricValue(item) / heatmapMax);
                return (
                  <div
                    key={item.country_code}
                    className={`min-w-[1400px] grid ${gridCols} gap-4 px-4 py-3 text-sm`}
                    style={{ backgroundColor: `rgba(37, 99, 235, ${Math.min(heatIntensity, 0.15)})` }}
                    data-testid={`country-compare-row-${item.country_code}`}
                  >
                    <div className="font-medium" data-testid={cellTestId(item.country_code, 'country')}>{item.country_code}</div>
                    <div data-testid={cellTestId(item.country_code, 'total')}>{formatNumber(item.total_listings)}</div>
                    <div data-testid={cellTestId(item.country_code, 'growth7')}>{formatPercent(item.growth_total_listings_7d)}</div>
                    <div data-testid={cellTestId(item.country_code, 'growth30')}>{formatPercent(item.growth_total_listings_30d)}</div>
                    <div data-testid={cellTestId(item.country_code, 'published')}>{formatNumber(item.published_listings)}</div>
                    <div data-testid={cellTestId(item.country_code, 'published-growth7')}>{formatPercent(item.growth_published_7d)}</div>
                    <div data-testid={cellTestId(item.country_code, 'published-growth30')}>{formatPercent(item.growth_published_30d)}</div>
                    <div data-testid={cellTestId(item.country_code, 'conversion')}>{formatRatio(item.conversion_rate)}</div>
                    <div data-testid={cellTestId(item.country_code, 'dealers')}>{formatNumber(item.active_dealers)}</div>
                    <div data-testid={cellTestId(item.country_code, 'dealers-growth7')}>{formatPercent(item.growth_active_dealers_7d)}</div>
                    <div data-testid={cellTestId(item.country_code, 'dealers-growth30')}>{formatPercent(item.growth_active_dealers_30d)}</div>
                    <div data-testid={cellTestId(item.country_code, 'density')}>{formatRatio(item.dealer_density)}</div>
                    {showRevenue && (
                      <div
                        data-testid={cellTestId(item.country_code, 'revenue')}
                        title={buildCurrencyTooltip(item.revenue_local_totals)}
                      >
                        {formatNumber(item.revenue_eur)}
                      </div>
                    )}
                    {showRevenue && (
                      <div data-testid={cellTestId(item.country_code, 'rev-growth7')}>{formatPercent(item.growth_revenue_7d)}</div>
                    )}
                    {showRevenue && (
                      <div data-testid={cellTestId(item.country_code, 'rev-growth30')}>{formatPercent(item.growth_revenue_30d)}</div>
                    )}
                    {showRevenue && (
                      <div data-testid={cellTestId(item.country_code, 'rev-mtd')}>{formatPercent(item.revenue_mtd_growth_pct)}</div>
                    )}
                    <div data-testid={cellTestId(item.country_code, 'sla24')}>{formatNumber(item.sla_pending_24h)}</div>
                    <div data-testid={cellTestId(item.country_code, 'sla48')}>{formatNumber(item.sla_pending_48h)}</div>
                    <div data-testid={cellTestId(item.country_code, 'risk-login')}>{formatNumber(item.risk_multi_login)}</div>
                    <div data-testid={cellTestId(item.country_code, 'risk-payment')}>
                      {showRevenue ? formatNumber(item.risk_pending_payments) : '-'}
                    </div>
                    <div data-testid={cellTestId(item.country_code, 'note')}>
                      {item.note || '-'}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
