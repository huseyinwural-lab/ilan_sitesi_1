import { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import { useAuth } from '../../contexts/AuthContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminLedgerPage() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [referenceType, setReferenceType] = useState('');
  const [referenceId, setReferenceId] = useState('');

  const authHeader = useMemo(() => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` }), []);

  const loadLedger = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (referenceType.trim()) params.set('reference_type', referenceType.trim());
      if (referenceId.trim()) params.set('reference_id', referenceId.trim());
      const res = await axios.get(`${API}/admin/finance/ledger?${params.toString()}`, { headers: authHeader });
      setItems(res.data.items || []);
      setError('');
    } catch {
      setError('Ledger kayıtları yüklenemedi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLedger();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="p-6 space-y-4" data-testid="admin-ledger-page">
      <div className="flex items-center justify-between gap-3 flex-wrap" data-testid="admin-ledger-header">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="admin-ledger-title">Ledger Entries</h1>
          <p className="text-sm text-muted-foreground" data-testid="admin-ledger-subtitle">Immutable çift taraflı kayıt görünümü</p>
          <p className="text-xs text-muted-foreground" data-testid="admin-ledger-scope-badge">
            Scope: {user?.role === 'country_admin' ? (user?.country_code || 'COUNTRY') : 'Global'}
          </p>
        </div>
      </div>

      {error ? <div className="border border-red-200 bg-red-50 text-red-700 rounded-md p-3" data-testid="admin-ledger-error">{error}</div> : null}

      <div className="grid md:grid-cols-3 gap-3" data-testid="admin-ledger-filters">
        <input value={referenceType} onChange={(e) => setReferenceType(e.target.value)} className="h-9 px-3 rounded-md border bg-background text-sm" placeholder="reference_type" data-testid="admin-ledger-filter-reference-type" />
        <input value={referenceId} onChange={(e) => setReferenceId(e.target.value)} className="h-9 px-3 rounded-md border bg-background text-sm" placeholder="reference_id" data-testid="admin-ledger-filter-reference-id" />
        <button onClick={loadLedger} className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm" data-testid="admin-ledger-filter-apply">Uygula</button>
      </div>

      <div className="border rounded-lg overflow-hidden" data-testid="admin-ledger-table">
        <table className="w-full text-sm">
          <thead className="bg-muted">
            <tr>
              <th className="text-left px-3 py-2">group</th>
              <th className="text-left px-3 py-2">account</th>
              <th className="text-left px-3 py-2">debit</th>
              <th className="text-left px-3 py-2">credit</th>
              <th className="text-left px-3 py-2">reference</th>
              <th className="text-left px-3 py-2">created</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan="6" className="px-3 py-4" data-testid="admin-ledger-loading">Yükleniyor...</td></tr>
            ) : items.length === 0 ? (
              <tr><td colSpan="6" className="px-3 py-4" data-testid="admin-ledger-empty">Kayıt yok</td></tr>
            ) : items.map((item) => (
              <tr key={item.id} className="border-t" data-testid={`admin-ledger-row-${item.id}`}>
                <td className="px-3 py-2 font-mono text-xs" data-testid={`admin-ledger-group-${item.id}`}>{item.entry_group_id}</td>
                <td className="px-3 py-2" data-testid={`admin-ledger-account-${item.id}`}>{item.account_code || item.account_id}</td>
                <td className="px-3 py-2" data-testid={`admin-ledger-debit-${item.id}`}>{item.debit_display}</td>
                <td className="px-3 py-2" data-testid={`admin-ledger-credit-${item.id}`}>{item.credit_display}</td>
                <td className="px-3 py-2" data-testid={`admin-ledger-reference-${item.id}`}>{item.reference_type} / {item.reference_id}</td>
                <td className="px-3 py-2 text-xs" data-testid={`admin-ledger-created-${item.id}`}>{item.created_at || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
