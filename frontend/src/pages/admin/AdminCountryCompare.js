import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminCountryComparePage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchCompare = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/admin/dashboard/country-compare`, { headers: authHeader });
      setItems(res.data.items || []);
    } catch (e) {
      console.error('Failed to fetch country compare', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCompare();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="space-y-6" data-testid="admin-country-compare-page">
      <div>
        <h1 className="text-2xl font-bold" data-testid="country-compare-title">Ülke Karşılaştırma</h1>
      </div>

      <div className="rounded-md border bg-card overflow-hidden" data-testid="country-compare-table">
        <div className="hidden lg:grid grid-cols-[0.6fr_1fr_1fr_1fr_1fr_1fr] gap-4 bg-muted px-4 py-3 text-sm font-medium">
          <div>Country</div>
          <div>Total</div>
          <div>Published</div>
          <div>Pending</div>
          <div>Active Dealers</div>
          <div>Revenue MTD</div>
        </div>
        <div className="divide-y">
          {loading ? (
            <div className="p-6 text-center" data-testid="country-compare-loading">Yükleniyor…</div>
          ) : items.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground" data-testid="country-compare-empty">Kayıt yok</div>
          ) : (
            items.map((item) => (
              <div
                key={item.country_code}
                className="grid grid-cols-1 gap-4 px-4 py-4 lg:grid-cols-[0.6fr_1fr_1fr_1fr_1fr_1fr]"
                data-testid={`country-compare-row-${item.country_code}`}
              >
                <div className="font-medium">{item.country_code}</div>
                <div>{item.total_listings}</div>
                <div>{item.published_listings}</div>
                <div>{item.pending_moderation}</div>
                <div>{item.active_dealers}</div>
                <div>{item.revenue_mtd}</div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
