import { useEffect, useMemo, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdminDealerDetailPage() {
  const { dealerId } = useParams();
  const [searchParams] = useSearchParams();
  const urlCountry = (searchParams.get('country') || '').toUpperCase();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [plans, setPlans] = useState([]);
  const [selectedPlan, setSelectedPlan] = useState('');
  const [riskLevel, setRiskLevel] = useState('low');
  const [riskSaving, setRiskSaving] = useState(false);
  const [riskError, setRiskError] = useState(null);
  const [riskSuccess, setRiskSuccess] = useState(null);
  const [assignError, setAssignError] = useState(null);
  const [assignSuccess, setAssignSuccess] = useState(null);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchDetail = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (urlCountry) params.set('country', urlCountry);
      const res = await axios.get(`${API}/admin/dealers/${dealerId}?${params.toString()}`, {
        headers: authHeader,
      });
      setData(res.data);
      setSelectedPlan(res.data?.dealer?.plan_id || '');
      setRiskLevel(res.data?.dealer?.risk_level || 'low');
    } catch (e) {
      console.error('Failed to fetch dealer detail', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchPlans = async () => {
    if (!urlCountry) return;
    try {
      const res = await axios.get(`${API}/admin/plans?country=${urlCountry}`, {
        headers: authHeader,
      });
      setPlans(res.data.items || []);
    } catch (e) {
      console.error('Failed to fetch plans', e);
    }
  };

  const assignPlan = async () => {
    setAssignError(null);
    setAssignSuccess(null);
    try {
      await axios.post(
        `${API}/admin/dealers/${dealerId}/plan${urlCountry ? `?country=${urlCountry}` : ''}`,
        { plan_id: selectedPlan || null },
        { headers: authHeader }
      );
      setAssignSuccess('Plan güncellendi');
      fetchDetail();
    } catch (e) {
      setAssignError(e.response?.data?.detail || 'Plan atanamadı');
    }
  };

  useEffect(() => {
    fetchDetail();
    fetchPlans();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dealerId, urlCountry]);

  if (loading) {
    return <div className="p-6" data-testid="dealer-detail-loading">Yükleniyor…</div>;
  }

  if (!data) {
    return <div className="p-6" data-testid="dealer-detail-empty">Dealer bulunamadı</div>;
  }

  const { dealer, active_plan: activePlan, last_invoice: lastInvoice, unpaid_count: unpaidCount } = data;

  return (
    <div className="space-y-6" data-testid="dealer-detail-page">
      <div>
        <h1 className="text-2xl font-bold" data-testid="dealer-detail-title">Dealer Detail</h1>
        <div className="text-xs text-muted-foreground" data-testid="dealer-detail-id">{dealer.id}</div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="border rounded-md p-4 space-y-2" data-testid="dealer-detail-card">
          <div className="text-sm font-semibold">Dealer</div>
          <div className="text-xs text-muted-foreground" data-testid="dealer-detail-email">{dealer.email}</div>
          <div className="text-xs text-muted-foreground">Status: {dealer.dealer_status}</div>
          <div className="text-xs text-muted-foreground">Country: {dealer.country_code}</div>
        </div>
        <div className="border rounded-md p-4 space-y-2" data-testid="dealer-plan-card">
          <div className="text-sm font-semibold">Active Plan</div>
          <div className="text-xs text-muted-foreground" data-testid="dealer-plan-name">{activePlan?.name || '—'}</div>
          <div className="text-xs text-muted-foreground">Price: {activePlan ? `${activePlan.price} ${activePlan.currency}` : '—'}</div>
          <div className="text-xs text-muted-foreground">Listing quota: {activePlan?.listing_quota ?? '—'}</div>
        </div>
        <div className="border rounded-md p-4 space-y-2" data-testid="dealer-invoice-card">
          <div className="text-sm font-semibold">Invoice Summary</div>
          <div className="text-xs text-muted-foreground" data-testid="dealer-unpaid-count">Unpaid: {unpaidCount}</div>
          <div className="text-xs text-muted-foreground">Last invoice: {lastInvoice?.id || '—'}</div>
          <div className="text-xs text-muted-foreground">Status: {lastInvoice?.status || '—'}</div>
        </div>
      </div>

      <div className="border rounded-md p-4 space-y-3" data-testid="dealer-plan-assign">
        <div className="text-sm font-semibold">Plan Assignment</div>
        <Select value={selectedPlan || ''} onValueChange={setSelectedPlan}>
          <SelectTrigger className="h-9" data-testid="dealer-plan-select">
            <SelectValue placeholder="Plan seçin" />
          </SelectTrigger>
          <SelectContent>
            {plans.map((plan) => (
              <SelectItem key={plan.id} value={plan.id} data-testid={`dealer-plan-option-${plan.id}`}>
                {plan.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {assignError && (
          <div className="text-xs text-destructive" data-testid="dealer-plan-error">{assignError}</div>
        )}
        {assignSuccess && (
          <div className="text-xs text-green-600" data-testid="dealer-plan-success">{assignSuccess}</div>
        )}
        <button
          onClick={assignPlan}
          className="h-9 px-3 rounded-md bg-primary text-primary-foreground text-sm"
          data-testid="dealer-plan-assign-button"
        >
          Plan Ata
        </button>
      </div>
    </div>
  );
}
