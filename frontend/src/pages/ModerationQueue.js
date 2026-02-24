import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { 
  CheckCircle, XCircle, AlertTriangle, Eye, 
  Filter, Clock, Image, DollarSign, Building2
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const statusColors = {
  pending: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  active: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
  rejected: 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400',
  needs_revision: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  suspended: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  expired: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
  pending_moderation: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  published: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
};

const REJECT_REASONS_V1 = [
  { value: 'duplicate', label: 'duplicate' },
  { value: 'spam', label: 'spam' },
  { value: 'illegal', label: 'illegal' },
  { value: 'wrong_category', label: 'wrong_category' },
];

const NEEDS_REVISION_REASONS_V1 = [
  { value: 'missing_photos', label: 'missing_photos' },
  { value: 'insufficient_description', label: 'insufficient_description' },
  { value: 'wrong_price', label: 'wrong_price' },
  { value: 'other', label: 'other' },
];

const SLA_WARNING_SECONDS = 12 * 60 * 60;
const SLA_CRITICAL_SECONDS = 24 * 60 * 60;
const FREEZE_TOOLTIP_TEXT = 'Moderation Freeze aktif. İşlem yapılamaz.';


export default function ModerationQueue({
  title = 'Moderation Queue',
  description = 'Review pending listings and apply moderation decisions.',
  dealerOnly = null,
  pageTestId = 'moderation-queue-page',
}) {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [countryFilter, setCountryFilter] = useState('');
  const [moduleFilter, setModuleFilter] = useState('');
  const [selectedListing, setSelectedListing] = useState(null);
  const [pendingCount, setPendingCount] = useState(0);
  const [actionDialog, setActionDialog] = useState(null); // { listingId, actionType }
  const [reason, setReason] = useState('');
  const [reasonNote, setReasonNote] = useState('');
  const [selectedIds, setSelectedIds] = useState([]);
  const [bulkDialog, setBulkDialog] = useState(null); // { actionType }
  const [bulkReason, setBulkReason] = useState('');
  const [bulkReasonNote, setBulkReasonNote] = useState('');
  const [freezeActive, setFreezeActive] = useState(false);
  const [freezeReason, setFreezeReason] = useState('');
  const [freezeLoaded, setFreezeLoaded] = useState(false);
  const { t, getTranslated, language } = useLanguage();

  useEffect(() => {
    fetchQueue();
    fetchCount();
  }, [countryFilter, moduleFilter, dealerOnly]);

  useEffect(() => {
    fetchFreezeStatus();
  }, []);

  useEffect(() => {
    setSelectedIds((prev) => prev.filter((id) => listings.some((listing) => listing.id === id)));
  }, [listings]);

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

  const fetchFreezeStatus = async () => {
    try {
      const response = await axios.get(`${API}/system-settings/effective`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      const setting = (response.data?.items || []).find((item) => item.key === 'moderation.freeze.active');
      setFreezeActive(resolveFreezeValue(setting));
      setFreezeReason(setting?.moderation_freeze_reason || '');
    } catch (error) {
      console.error('Failed to fetch moderation freeze status:', error);
    } finally {
      setFreezeLoaded(true);
    }
  };

  const fetchQueue = async () => {
    try {
      const params = new URLSearchParams();
      params.append('status', 'pending_moderation');
      if (countryFilter) params.append('country', countryFilter);
      if (moduleFilter) params.append('module', moduleFilter);
      if (dealerOnly !== null) params.append('dealer_only', dealerOnly);
      
      const response = await axios.get(`${API}/admin/moderation/queue?${params}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      setListings(response.data);
    } catch (error) {
      console.error('Failed to fetch queue:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchCount = async () => {
    try {
      const params = new URLSearchParams();
      params.append('status', 'pending_moderation');
      if (dealerOnly !== null) params.append('dealer_only', dealerOnly);
      const response = await axios.get(`${API}/admin/moderation/queue/count?${params.toString()}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      setPendingCount(response.data.count);
    } catch (error) {
      console.error('Failed to fetch count:', error);
    }
  };

  const selectedCount = selectedIds.length;
  const allSelected = listings.length > 0 && selectedCount === listings.length;

  const formatDuration = (seconds) => {
    if (seconds === null || seconds === undefined) return '--';
    if (seconds < 60) return `${Math.floor(seconds)}sn`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}dk`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return remainingMinutes ? `${hours}sa ${remainingMinutes}dk` : `${hours}sa`;
  };

  const getSlaMeta = (createdAt) => {
    if (!createdAt) {
      return { label: 'SLA --', badgeClass: 'bg-slate-100 text-slate-600' };
    }
    const seconds = Math.max(0, (Date.now() - new Date(createdAt).getTime()) / 1000);
    if (seconds >= SLA_CRITICAL_SECONDS) {
      return { label: `SLA ${formatDuration(seconds)}`, badgeClass: 'bg-rose-100 text-rose-700' };
    }
    if (seconds >= SLA_WARNING_SECONDS) {
      return { label: `SLA ${formatDuration(seconds)}`, badgeClass: 'bg-amber-100 text-amber-700' };
    }
    return { label: `SLA ${formatDuration(seconds)}`, badgeClass: 'bg-emerald-100 text-emerald-700' };
  };

  const toggleSelectAll = () => {
    if (allSelected) {
      setSelectedIds([]);
      return;
    }
    setSelectedIds(listings.map((listing) => listing.id));
  };

  const toggleSelect = (listingId) => {
    setSelectedIds((prev) => (prev.includes(listingId) ? prev.filter((id) => id !== listingId) : [...prev, listingId]));
  };

  const openBulkDialog = (actionType) => {
    if (!selectedCount) return;
    setBulkDialog({ actionType });
    setBulkReason('');
    setBulkReasonNote('');
  };

  const submitBulkDialog = async () => {
    if (!bulkDialog) return;
    try {
      if (bulkDialog.actionType === 'approve') {
        await axios.post(`${API}/admin/moderation/bulk-approve`, {
          listing_ids: selectedIds,
        }, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
      } else if (bulkDialog.actionType === 'reject') {
        if (!bulkReason) {
          alert('Reason is required');
          return;
        }
        await axios.post(`${API}/admin/moderation/bulk-reject`, {
          listing_ids: selectedIds,
          reason: bulkReason,
          reason_note: bulkReasonNote?.trim() || undefined,
        }, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
      }

      await fetchQueue();
      await fetchCount();
      setSelectedIds([]);
      setBulkDialog(null);
    } catch (error) {
      console.error('Failed to bulk moderate:', error);
      alert(error.response?.data?.detail || 'Failed to bulk moderate');
    }
  };


  const handleAction = async (listingId, actionType, reasonPayload = null) => {
    try {
      if (actionType === 'approve') {
        await axios.post(`${API}/admin/listings/${listingId}/approve`, {}, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
      } else if (actionType === 'reject') {
        await axios.post(`${API}/admin/listings/${listingId}/reject`, reasonPayload, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
      } else if (actionType === 'needs_revision') {
        await axios.post(`${API}/admin/listings/${listingId}/needs_revision`, reasonPayload, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('access_token')}`,
          },
        });
      }

      await fetchQueue();
      await fetchCount();
      setSelectedListing(null);
    } catch (error) {
      console.error('Failed to moderate:', error);
      alert(error.response?.data?.detail || 'Failed to moderate');
    }
  };

  const openActionDialog = (listingId, actionType) => {
    setActionDialog({ listingId, actionType });
    setReason('');
    setReasonNote('');
  };

  const submitActionDialog = async () => {
    if (!actionDialog) return;

    if (actionDialog.actionType === 'reject') {
      if (!reason) {
        alert('Reason is required');
        return;
      }
      await handleAction(actionDialog.listingId, 'reject', { reason });
    }

    if (actionDialog.actionType === 'needs_revision') {
      if (!reason) {
        alert('Reason is required');
        return;
      }
      if (reason === 'other' && !reasonNote.trim()) {
        alert('Reason note is required when reason=other');
        return;
      }
      await handleAction(actionDialog.listingId, 'needs_revision', { reason, reason_note: reason === 'other' ? reasonNote.trim() : undefined });
    }

    setActionDialog(null);
  };

  const viewListingDetail = async (listingId) => {
    try {
      const response = await axios.get(`${API}/admin/moderation/listings/${listingId}`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      setSelectedListing(response.data);
    } catch (error) {
      console.error('Failed to fetch listing:', error);
    }
  };

  const renderFreezeTooltip = (testId) => {
    if (!freezeActive) return null;
    return (
      <span
        className="pointer-events-none absolute -top-9 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-md bg-slate-900 px-2 py-1 text-[11px] text-white opacity-0 shadow transition group-hover:opacity-100"
        data-testid={testId}
      >
        {FREEZE_TOOLTIP_TEXT}
      </span>
    );
  };

  return (
    <div className="space-y-6" data-testid={pageTestId}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight" data-testid="moderation-queue-title">{title}</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {description} · <span className="font-semibold text-amber-600">{pendingCount}</span>
          </p>
        </div>
      </div>

      {freezeActive && (
        <div
          className="sticky top-0 z-20 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm font-medium text-amber-800"
          data-testid="moderation-freeze-banner"
        >
          Moderation Freeze aktif – yalnızca görüntüleme yapılabilir.
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          value={countryFilter}
          onChange={(e) => { setCountryFilter(e.target.value); setLoading(true); }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="moderation-country-filter"
        >
          <option value="">All Countries</option>
          <option value="DE">Germany (DE)</option>
          <option value="CH">Switzerland (CH)</option>
          <option value="FR">France (FR)</option>
          <option value="AT">Austria (AT)</option>
        </select>

        <select
          value={moduleFilter}
          onChange={(e) => { setModuleFilter(e.target.value); setLoading(true); }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
          data-testid="moderation-module-filter"
        >
          <option value="">All Modules</option>
          <option value="real_estate">Real Estate</option>
          <option value="vehicle">Vehicle</option>
          <option value="machinery">Machinery</option>
          <option value="services">Services</option>
          <option value="jobs">Jobs</option>
        </select>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border bg-card p-3" data-testid="moderation-bulk-bar">
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-sm" data-testid="moderation-select-all-label">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={toggleSelectAll}
              className="h-4 w-4"
              data-testid="moderation-select-all"
            />
            Tümünü seç
          </label>
          <span className="text-sm text-muted-foreground" data-testid="moderation-selected-count">Seçilen: {selectedCount}</span>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative group">
            <button
              type="button"
              onClick={() => openBulkDialog('approve')}
              disabled={freezeActive || !selectedCount}
              className="h-9 px-3 rounded-md bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-50"
              data-testid="moderation-bulk-approve"
            >
              Toplu Onayla
            </button>
            {renderFreezeTooltip('moderation-bulk-approve-tooltip')}
          </div>
          <div className="relative group">
            <button
              type="button"
              onClick={() => openBulkDialog('reject')}
              disabled={freezeActive || !selectedCount}
              className="h-9 px-3 rounded-md bg-rose-600 text-white text-sm font-medium hover:bg-rose-700 disabled:opacity-50"
              data-testid="moderation-bulk-reject"
            >
              Toplu Reddet
            </button>
            {renderFreezeTooltip('moderation-bulk-reject-tooltip')}
          </div>
        </div>
      </div>

      {/* Queue List */}
      <div className="space-y-3">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : listings.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground bg-card rounded-md border">
            <CheckCircle size={48} className="mx-auto mb-4 text-emerald-500" />
            <p className="font-medium">All caught up!</p>
            <p className="text-sm">No listings pending moderation</p>
          </div>
        ) : (
          listings.map((listing) => {
            const slaMeta = getSlaMeta(listing.moderation_created_at || listing.created_at);
            const isSelected = selectedIds.includes(listing.id);
            return (
              <div 
                key={listing.id} 
                className="bg-card rounded-md border p-4 hover:shadow-md transition-shadow"
                data-testid={`moderation-item-${listing.id}`}
              >
                <div className="flex items-start gap-4">
                  <div className="pt-1">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => toggleSelect(listing.id)}
                      className="h-4 w-4"
                      data-testid={`moderation-select-${listing.id}`}
                    />
                  </div>
                  {/* Thumbnail placeholder */}
                  <div className="w-24 h-24 rounded-md bg-muted flex items-center justify-center shrink-0">
                    {listing.image_count > 0 ? (
                      <Image size={24} className="text-muted-foreground" />
                    ) : (
                      <AlertTriangle size={24} className="text-amber-500" />
                    )}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <h3 className="font-medium truncate">{listing.title}</h3>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs px-1.5 py-0.5 rounded bg-muted capitalize">{listing.module.replace('_', ' ')}</span>
                          <span className="text-xs px-1.5 py-0.5 rounded bg-muted">{listing.country}</span>
                          {listing.city && <span className="text-xs text-muted-foreground">{listing.city}</span>}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${statusColors[listing.status]}`}>
                          {listing.status}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-xs font-semibold ${slaMeta.badgeClass}`}
                          data-testid={`moderation-sla-${listing.id}`}
                        >
                          {slaMeta.label}
                        </span>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 mt-3 text-sm">
                      {listing.price && (
                        <span className="flex items-center gap-1">
                          <DollarSign size={14} className="text-muted-foreground" />
                          {listing.price.toLocaleString()} {listing.currency}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Image size={14} className="text-muted-foreground" />
                        {listing.image_count} images
                      </span>
                      {listing.is_dealer_listing && (
                        <span className="flex items-center gap-1 text-blue-600">
                          <Building2 size={14} />
                          Dealer
                        </span>
                      )}
                      {listing.is_premium && (
                        <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 text-xs font-medium">
                          Premium
                        </span>
                      )}
                      <span className="flex items-center gap-1 text-muted-foreground">
                        <Clock size={14} className="text-muted-foreground" />
                        {new Date(listing.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex flex-col gap-1 shrink-0">
                    <button
                      onClick={() => viewListingDetail(listing.id)}
                      className="p-2 rounded-md border hover:bg-muted"
                      title="View Details"
                      data-testid={`moderation-view-${listing.id}`}
                    >
                      <Eye size={16} />
                    </button>
                    <div className="relative group">
                      <button
                        onClick={() => handleAction(listing.id, 'approve')}
                        disabled={freezeActive}
                        className="p-2 rounded-md border text-emerald-600 hover:bg-emerald-50 disabled:opacity-50"
                        title="Approve"
                        data-testid={`moderation-approve-${listing.id}`}
                      >
                        <CheckCircle size={16} />
                      </button>
                      {renderFreezeTooltip(`moderation-approve-tooltip-${listing.id}`)}
                    </div>
                    <div className="relative group">
                      <button
                        onClick={() => openActionDialog(listing.id, 'reject')}
                        disabled={freezeActive}
                        className="p-2 rounded-md border text-rose-600 hover:bg-rose-50 disabled:opacity-50"
                        title="Reject"
                        data-testid={`moderation-reject-${listing.id}`}
                      >
                        <XCircle size={16} />
                      </button>
                      {renderFreezeTooltip(`moderation-reject-tooltip-${listing.id}`)}
                    </div>
                    <div className="relative group">
                      <button
                        onClick={() => openActionDialog(listing.id, 'needs_revision')}
                        disabled={freezeActive}
                        className="p-2 rounded-md border text-amber-600 hover:bg-amber-50 disabled:opacity-50"
                        title="Needs Revision"
                        data-testid={`moderation-needs-revision-${listing.id}`}
                      >
                        <AlertTriangle size={16} />
                      </button>
                      {renderFreezeTooltip(`moderation-needs-revision-tooltip-${listing.id}`)}
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Listing Detail Modal */}
      {selectedListing && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b sticky top-0 bg-card">
              <h2 className="text-lg font-semibold">Listing Review</h2>
              <button onClick={() => setSelectedListing(null)} className="p-1 rounded hover:bg-muted" data-testid="moderation-detail-close">×</button>
            </div>
            {freezeActive && (
              <div
                className="mx-4 mt-4 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800"
                data-testid="moderation-freeze-detail-banner"
              >
                Moderation Freeze aktif – yalnızca görüntüleme yapılabilir.
              </div>
            )}

            <div className="p-4 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-xl font-semibold">{selectedListing.title}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs px-1.5 py-0.5 rounded bg-muted capitalize">{selectedListing.module.replace('_', ' ')}</span>
                    <span className="text-xs px-1.5 py-0.5 rounded bg-muted">{selectedListing.country}</span>
                  </div>
                </div>
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${statusColors[selectedListing.status]}`}>
                  {selectedListing.status}
                </span>
              </div>
              
              {selectedListing.description && (
                <div>
                  <h4 className="font-medium mb-1">Description</h4>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">{selectedListing.description}</p>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-medium mb-1">Price</h4>
                  <p className="text-lg font-semibold">{selectedListing.price?.toLocaleString()} {selectedListing.currency}</p>
                </div>
                <div>
                  <h4 className="font-medium mb-1">Location</h4>
                  <p>{selectedListing.city || selectedListing.country}</p>
                </div>
              </div>
              
              {selectedListing.images && selectedListing.images.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Images ({selectedListing.images.length})</h4>
                  <div className="flex gap-2 flex-wrap">
                    {selectedListing.images.map((img, idx) => (
                      <div key={idx} className="w-20 h-20 rounded bg-muted flex items-center justify-center">
                        <Image size={24} className="text-muted-foreground" />
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {selectedListing.attributes && Object.keys(selectedListing.attributes).length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Attributes</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    {Object.entries(selectedListing.attributes).map(([key, value]) => (
                      <div key={key} className="flex justify-between p-2 bg-muted/50 rounded">
                        <span className="text-muted-foreground capitalize">{key.replace('_', ' ')}</span>
                        <span className="font-medium">{String(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>


              )}
              
              {selectedListing.moderation_history && selectedListing.moderation_history.length > 0 && (
                <div>
                  <h4 className="font-medium mb-2">Moderation History</h4>
                  <div className="space-y-2">
                    {selectedListing.moderation_history.map((action) => (
                      <div key={action.id} className="text-sm p-2 bg-muted/50 rounded">
                        <div className="flex items-center gap-2">
                          <span className={`px-1.5 py-0.5 rounded text-xs font-medium capitalize ${
                            action.action_type === 'approve' ? 'bg-emerald-100 text-emerald-800' :
                            action.action_type === 'reject' ? 'bg-rose-100 text-rose-800' :
                            'bg-amber-100 text-amber-800'
                          }`}>
                            {action.action_type}
                          </span>
                          <span className="text-muted-foreground">{action.actor_email}</span>
                          <span className="text-muted-foreground">{new Date(action.created_at).toLocaleString()}</span>
                        </div>
                        {action.reason && <p className="mt-1 text-muted-foreground">{action.reason}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {selectedListing.status === 'pending_moderation' && (
                <div className="flex flex-wrap gap-2 pt-4 border-t">
                  <div className="relative group flex-1 min-w-[160px]">
                    <button
                      onClick={() => handleAction(selectedListing.id, 'approve')}
                      disabled={freezeActive}
                      className="w-full px-4 py-2 rounded-md bg-emerald-600 text-white font-medium hover:bg-emerald-700 disabled:opacity-50 flex items-center justify-center gap-2"
                      data-testid="moderation-detail-approve"
                    >
                      <CheckCircle size={18} />
                      Approve
                    </button>
                    {renderFreezeTooltip('moderation-detail-approve-tooltip')}
                  </div>
                  <div className="relative group flex-1 min-w-[160px]">
                    <button
                      onClick={() => openActionDialog(selectedListing.id, 'reject')}
                      disabled={freezeActive}
                      className="w-full px-4 py-2 rounded-md bg-rose-600 text-white font-medium hover:bg-rose-700 disabled:opacity-50 flex items-center justify-center gap-2"
                      data-testid="moderation-detail-reject"
                    >
                      <XCircle size={18} />
                      Reject
                    </button>
                    {renderFreezeTooltip('moderation-detail-reject-tooltip')}
                  </div>
                  <div className="relative group flex-1 min-w-[160px]">
                    <button
                      onClick={() => openActionDialog(selectedListing.id, 'needs_revision')}
                      disabled={freezeActive}
                      className="w-full px-4 py-2 rounded-md border text-amber-700 hover:bg-amber-50 disabled:opacity-50 flex items-center justify-center gap-2"
                      data-testid="moderation-detail-needs-revision"
                    >
                      <AlertTriangle size={18} />
                      Needs Revision
                    </button>
                    {renderFreezeTooltip('moderation-detail-needs-revision-tooltip')}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}


      {/* Action Dialog */}
      {actionDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="moderation-action-dialog">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-md">
            <div className="p-4 border-b">
              <h3 className="text-lg font-semibold">
                {actionDialog.actionType === 'reject' ? 'Reject Listing' : 'Needs Revision'}
              </h3>
              <p className="text-sm text-muted-foreground mt-1">
                Please select a reason
              </p>
            </div>

            {freezeActive && (
              <div
                className="mx-4 mt-4 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800"
                data-testid="moderation-freeze-action-banner"
              >
                Moderation Freeze aktif – işlem yapılamaz.
              </div>
            )}

            <div className="p-4 space-y-4">
              <div>
                <label className="text-sm font-medium">Reason</label>
                <select
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="mt-1 w-full h-9 px-3 rounded-md border bg-background text-sm"
                  data-testid="moderation-action-reason"
                >
                  <option value="">Select…</option>
                  {(actionDialog.actionType === 'reject' ? REJECT_REASONS_V1 : NEEDS_REVISION_REASONS_V1).map((r) => (
                    <option key={r.value} value={r.value}>{r.label}</option>
                  ))}
                </select>
              </div>

              {actionDialog.actionType === 'needs_revision' && reason === 'other' && (
                <div>
                  <label className="text-sm font-medium">Reason note (required for other)</label>
                  <textarea
                    value={reasonNote}
                    onChange={(e) => setReasonNote(e.target.value)}
                    className="mt-1 w-full min-h-[90px] p-3 rounded-md border bg-background text-sm"
                    placeholder="Explain what needs to be changed…"
                    data-testid="moderation-action-reason-note"
                  />
                </div>
              )}
            </div>

            <div className="p-4 border-t flex items-center justify-end gap-2">
              <button
                onClick={() => setActionDialog(null)}
                className="h-9 px-3 rounded-md border hover:bg-muted text-sm"
                data-testid="moderation-action-cancel"
              >
                Cancel
              </button>
              <div className="relative group">
                <button
                  onClick={submitActionDialog}
                  disabled={freezeActive}
                  className="h-9 px-3 rounded-md bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50 text-sm"
                  data-testid="moderation-action-submit"
                >
                  Submit
                </button>
                {renderFreezeTooltip('moderation-action-submit-tooltip')}
              </div>
            </div>
          </div>
        </div>
      )}

      {bulkDialog && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="moderation-bulk-dialog">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-md">
            <div className="p-4 border-b">
              <h3 className="text-lg font-semibold">
                {bulkDialog.actionType === 'approve' ? 'Toplu Onayla' : 'Toplu Reddet'}
              </h3>
              <p className="text-sm text-muted-foreground mt-1" data-testid="moderation-bulk-summary">
                Seçili {selectedCount} ilan için bu işlemi onaylayın.
              </p>
            </div>

            {freezeActive && (
              <div
                className="mx-4 mt-4 rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-medium text-amber-800"
                data-testid="moderation-freeze-bulk-banner"
              >
                Moderation Freeze aktif – işlem yapılamaz.
              </div>
            )}

            {bulkDialog.actionType === 'reject' && (
              <div className="p-4 space-y-4">
                <div>
                  <label className="text-sm font-medium">Reason</label>
                  <select
                    value={bulkReason}
                    onChange={(e) => setBulkReason(e.target.value)}
                    className="mt-1 w-full h-9 px-3 rounded-md border bg-background text-sm"
                    data-testid="moderation-bulk-reason"
                  >
                    <option value="">Select…</option>
                    {REJECT_REASONS_V1.map((r) => (
                      <option key={r.value} value={r.value}>{r.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium">Not (opsiyonel)</label>
                  <textarea
                    value={bulkReasonNote}
                    onChange={(e) => setBulkReasonNote(e.target.value)}
                    className="mt-1 w-full min-h-[90px] p-3 rounded-md border bg-background text-sm"
                    placeholder="Ek açıklama..."
                    data-testid="moderation-bulk-reason-note"
                  />
                </div>
              </div>
            )}

            <div className="p-4 border-t flex items-center justify-end gap-2">
              <button
                onClick={() => setBulkDialog(null)}
                className="h-9 px-3 rounded-md border hover:bg-muted text-sm"
                data-testid="moderation-bulk-cancel"
              >
                Cancel
              </button>
              <div className="relative group">
                <button
                  onClick={submitBulkDialog}
                  disabled={freezeActive}
                  className={`h-9 px-3 rounded-md text-white text-sm disabled:opacity-50 ${
                    bulkDialog.actionType === 'approve'
                      ? 'bg-emerald-600 hover:bg-emerald-700'
                      : 'bg-rose-600 hover:bg-rose-700'
                  }`}
                  data-testid="moderation-bulk-submit"
                >
                  Onayla
                </button>
                {renderFreezeTooltip('moderation-bulk-submit-tooltip')}
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
