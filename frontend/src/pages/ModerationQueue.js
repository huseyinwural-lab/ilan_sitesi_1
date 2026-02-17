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
  suspended: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  expired: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-400',
};

export default function ModerationQueue() {
  const [listings, setListings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [countryFilter, setCountryFilter] = useState('');
  const [moduleFilter, setModuleFilter] = useState('');
  const [selectedListing, setSelectedListing] = useState(null);
  const [pendingCount, setPendingCount] = useState(0);
  const { t, getTranslated, language } = useLanguage();

  useEffect(() => {
    fetchQueue();
    fetchCount();
  }, [countryFilter, moduleFilter]);

  const fetchQueue = async () => {
    try {
      const params = new URLSearchParams();
      params.append('status', 'pending_moderation');
      if (countryFilter) params.append('country', countryFilter);
      if (moduleFilter) params.append('module', moduleFilter);
      
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
      const response = await axios.get(`${API}/admin/moderation/queue/count?status=pending_moderation`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        },
      });
      setPendingCount(response.data.count);
    } catch (error) {
      console.error('Failed to fetch count:', error);
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
      fetchQueue();
      fetchCount();
      setSelectedListing(null);
    } catch (error) {
      console.error('Failed to moderate:', error);
      alert(error.response?.data?.detail || 'Failed to moderate');
    }
  };

  const viewListingDetail = async (listingId) => {
    try {
      const response = await axios.get(`${API}/moderation/listings/${listingId}`);
      setSelectedListing(response.data);
    } catch (error) {
      console.error('Failed to fetch listing:', error);
    }
  };

  return (
    <div className="space-y-6" data-testid="moderation-queue-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Moderation Queue</h1>
          <p className="text-muted-foreground text-sm mt-1">
            <span className="font-semibold text-amber-600">{pendingCount}</span> listings pending review
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select
          value={countryFilter}
          onChange={(e) => { setCountryFilter(e.target.value); setLoading(true); }}
          className="h-9 px-3 rounded-md border bg-background text-sm"
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
        >
          <option value="">All Modules</option>
          <option value="real_estate">Real Estate</option>
          <option value="vehicle">Vehicle</option>
          <option value="machinery">Machinery</option>
          <option value="services">Services</option>
          <option value="jobs">Jobs</option>
        </select>
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
          listings.map((listing) => (
            <div 
              key={listing.id} 
              className="bg-card rounded-md border p-4 hover:shadow-md transition-shadow"
              data-testid={`moderation-item-${listing.id}`}
            >
              <div className="flex items-start gap-4">
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
                    <span className={`px-2 py-0.5 rounded text-xs font-semibold ${statusColors[listing.status]}`}>
                      {listing.status}
                    </span>
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
                      <Clock size={14} />
                      {new Date(listing.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
                
                <div className="flex flex-col gap-1 shrink-0">
                  <button
                    onClick={() => viewListingDetail(listing.id)}
                    className="p-2 rounded-md border hover:bg-muted"
                    title="View Details"
                  >
                    <Eye size={16} />
                  </button>
                  <button
                    onClick={() => handleAction(listing.id, 'approve')}
                    className="p-2 rounded-md border text-emerald-600 hover:bg-emerald-50"
                    title="Approve"
                  >
                    <CheckCircle size={16} />
                  </button>
                  <button
                    onClick={() => {
                      const reason = prompt('Enter reject reason:');
                      if (reason) handleAction(listing.id, 'reject', reason);
                    }}
                    className="p-2 rounded-md border text-rose-600 hover:bg-rose-50"
                    title="Reject"
                  >
                    <XCircle size={16} />
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Listing Detail Modal */}
      {selectedListing && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b sticky top-0 bg-card">
              <h2 className="text-lg font-semibold">Listing Review</h2>
              <button onClick={() => setSelectedListing(null)} className="p-1 rounded hover:bg-muted">×</button>
            </div>
            
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
              
              {selectedListing.status === 'pending' && (
                <div className="flex gap-2 pt-4 border-t">
                  <button
                    onClick={() => handleAction(selectedListing.id, 'approve')}
                    className="flex-1 px-4 py-2 rounded-md bg-emerald-600 text-white font-medium hover:bg-emerald-700 flex items-center justify-center gap-2"
                  >
                    <CheckCircle size={18} />
                    Approve
                  </button>
                  <button
                    onClick={() => {
                      const reason = prompt('Enter reject reason:');
                      if (reason) handleAction(selectedListing.id, 'reject', reason);
                    }}
                    className="flex-1 px-4 py-2 rounded-md bg-rose-600 text-white font-medium hover:bg-rose-700 flex items-center justify-center gap-2"
                  >
                    <XCircle size={18} />
                    Reject
                  </button>
                  <button
                    onClick={() => handleAction(selectedListing.id, 'suspend')}
                    className="px-4 py-2 rounded-md border text-amber-600 hover:bg-amber-50 flex items-center justify-center gap-2"
                  >
                    <AlertTriangle size={18} />
                    Suspend
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
