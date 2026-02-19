import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminCountryComparePage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [financeVisible, setFinanceVisible] = useState(false);
  const { user } = useAuth();

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchCompare = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/dashboard/country-compare`, { headers: authHeader });
      setItems(res.data.items || []);
      setFinanceVisible(Boolean(res.data.finance_visible));
    } catch (e) {
      console.error('Failed to fetch country compare', e);
      setItems([]);
      setFinanceVisible(false);
    } finally {
      setLoading(false);
      setHasLoaded(true);
    }
  };

  useEffect(() => {
    fetchCompare();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const showRevenue = financeVisible && ['finance', 'super_admin'].includes(user?.role);
  const gridCols = showRevenue
    ? 'grid-cols-[0.6fr_1fr_1fr_1fr_1fr_1fr]'
    : 'grid-cols-[0.6fr_1fr_1fr_1fr_1fr]';

  return (
    <div className="space-y-6" data-testid="admin-country-compare-page">
      <div>
        <h1 className="text-2xl font-bold" data-testid="country-compare-title">Ülke Karşılaştırma</h1>
      </div>

      <div className="rounded-md border bg-card overflow-hidden" data-testid="country-compare-table">
        <div className={`hidden lg:grid ${gridCols} gap-4 bg-muted px-4 py-3 text-sm font-medium`}>
          <div>Country</div>
          <div>Total</div>
          <div>Published</div>
          <div>Pending</div>
          <div>Active Dealers</div>
          {showRevenue && <div>Revenue MTD</div>}
        </div>
        {!showRevenue && hasLoaded && (
          <div className="px-4 py-2 text-xs text-muted-foreground" data-testid="country-compare-finance-locked">
            Finans metrikleri yalnızca finance ve super_admin rollerine açıktır.
          </div>
        )}
        <div className="divide-y">
          {loading && !hasLoaded ? (
            <div className="p-6 text-center" data-testid="country-compare-loading">Yükleniyor…</div>
          ) : items.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground" data-testid="country-compare-empty">Kayıt yok</div>
          ) : (
            items.map((item) => (
              <div
                key={item.country_code}
                className={`grid grid-cols-1 gap-4 px-4 py-4 lg:${gridCols}`}
                data-testid={`country-compare-row-${item.country_code}`}
              >
                <div className="font-medium">{item.country_code}</div>
                <div>{item.total_listings}</div>
                <div>{item.published_listings}</div>
                <div>{item.pending_moderation}</div>
                <div>{item.active_dealers}</div>
                {showRevenue && (
                  <div data-testid={`country-compare-revenue-${item.country_code}`}>{item.revenue_mtd ?? '-'}</div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
