import React from 'react';
import { BarChart3, Lock } from 'lucide-react';

const formatNumber = (value) => {
  if (value === null || value === undefined) return '-';
  return Number(value).toLocaleString('tr-TR');
};

const formatCurrencyTotals = (totals) => {
  if (!totals || Object.keys(totals).length === 0) return '-';
  return Object.entries(totals)
    .map(([currency, amount]) => `${Number(amount).toLocaleString('tr-TR')} ${currency}`)
    .join(' · ');
};

const MiniLineChart = ({ data, valueKey, testId }) => {
  if (!data || data.length === 0) {
    return (
      <div className="text-xs text-muted-foreground text-center py-8" data-testid={`${testId}-empty`}>
        Veri yok
      </div>
    );
  }

  const width = 300;
  const height = 120;
  const padding = 12;
  const values = data.map((item) => Number(item[valueKey] || 0));
  const max = Math.max(...values, 1);
  const min = Math.min(...values, 0);
  const range = max - min || 1;

  const points = values
    .map((value, index) => {
      const x = padding + (index / (values.length - 1 || 1)) * (width - padding * 2);
      const y = height - padding - ((value - min) / range) * (height - padding * 2);
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full h-28"
      preserveAspectRatio="none"
      data-testid={testId}
    >
      <polyline
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinejoin="round"
        strokeLinecap="round"
        className="text-primary"
        points={points}
      />
    </svg>
  );
};

const TrendCard = ({ title, subtitle, data, valueKey, totalLabel, footer, testId }) => (
  <div className="bg-card rounded-md border p-6" data-testid={testId}>
    <div className="flex items-start justify-between mb-4">
      <div>
        <p className="text-xs text-muted-foreground" data-testid={`${testId}-subtitle`}>{subtitle}</p>
        <h3 className="text-lg font-semibold" data-testid={`${testId}-title`}>{title}</h3>
      </div>
      <div className="text-right">
        <div className="text-xs text-muted-foreground">Toplam</div>
        <div className="text-lg font-semibold" data-testid={`${testId}-total`}>{totalLabel}</div>
      </div>
    </div>
    <MiniLineChart data={data} valueKey={valueKey} testId={`${testId}-chart`} />
    <div className="flex justify-between text-xs text-muted-foreground mt-3">
      <span data-testid={`${testId}-start-date`}>{data?.[0]?.date || '-'}</span>
      <span data-testid={`${testId}-end-date`}>{data?.[data.length - 1]?.date || '-'}</span>
    </div>
    {footer && (
      <div className="text-xs text-muted-foreground mt-2" data-testid={`${testId}-footer`}>{footer}</div>
    )}
  </div>
);

export default function TrendsSection({ trends, canViewFinance }) {
  const listings = trends?.listings || [];
  const revenue = trends?.revenue || [];
  const windowDays = trends?.window_days || 0;

  const listingsTotal = listings.reduce((sum, item) => sum + Number(item.count || 0), 0);
  const revenueTotals = revenue.reduce((acc, item) => {
    const totals = item.currency_totals || {};
    Object.entries(totals).forEach(([currency, amount]) => {
      acc[currency] = (acc[currency] || 0) + Number(amount || 0);
    });
    return acc;
  }, {});
  const revenueTotalAmount = revenue.reduce((sum, item) => sum + Number(item.amount || 0), 0);

  return (
    <div className="grid gap-6 lg:grid-cols-2" data-testid="dashboard-trends-section">
      <TrendCard
        title="İlan Trendi"
        subtitle={`${windowDays || listings.length} günlük görünüm`}
        data={listings}
        valueKey="count"
        totalLabel={formatNumber(listingsTotal)}
        testId="dashboard-trend-listings"
      />
      {canViewFinance ? (
        <TrendCard
          title="Gelir Trendi"
          subtitle={`${windowDays || revenue.length} günlük görünüm`}
          data={revenue}
          valueKey="amount"
          totalLabel={formatNumber(revenueTotalAmount)}
          footer={formatCurrencyTotals(revenueTotals)}
          testId="dashboard-trend-revenue"
        />
      ) : (
        <div className="bg-card rounded-md border p-6 flex flex-col justify-between" data-testid="dashboard-trend-revenue-locked">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-muted-foreground">Gelir Trendi</p>
              <h3 className="text-lg font-semibold">Yetki gerekiyor</h3>
            </div>
            <div className="p-2 rounded-md bg-muted">
              <Lock size={18} className="text-muted-foreground" />
            </div>
          </div>
          <div className="text-xs text-muted-foreground mt-6" data-testid="dashboard-trend-revenue-locked-note">
            Finans metriklerini görmek için finance / super_admin rolü gerekli.
          </div>
          <div className="mt-6 flex items-center gap-2 text-sm text-muted-foreground" data-testid="dashboard-trend-revenue-locked-icon">
            <BarChart3 size={18} /> Trend grafiği gizli
          </div>
        </div>
      )}
    </div>
  );
}
