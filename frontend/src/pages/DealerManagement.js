import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { 
  Building2, Plus, Check, X, Clock, Eye, FileText,
  ChevronDown, MapPin, Mail, Phone, Globe
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const statusColors = {
  pending: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  approved: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
  rejected: 'bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400',
};

const dealerTypeLabels = {
  auto_dealer: 'Auto Dealer',
  real_estate_agency: 'Real Estate Agency',
  machinery_dealer: 'Machinery Dealer',
  general: 'General',
};

export default function DealerManagement() {
  const [tab, setTab] = useState('applications');
  const [applications, setApplications] = useState([]);
  const [dealers, setDealers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedApp, setSelectedApp] = useState(null);
  const [statusFilter, setStatusFilter] = useState('pending');
  const { t, getTranslated } = useLanguage();

  useEffect(() => {
    if (tab === 'applications') {
      fetchApplications();
    } else {
      fetchDealers();
    }
  }, [tab, statusFilter]);

  const fetchApplications = async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      const response = await axios.get(`${API}/dealer-applications?${params}`);
      setApplications(response.data);
    } catch (error) {
      console.error('Failed to fetch applications:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDealers = async () => {
    try {
      const response = await axios.get(`${API}/dealers`);
      setDealers(response.data);
    } catch (error) {
      console.error('Failed to fetch dealers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleReview = async (appId, action, rejectReason = null) => {
    try {
      await axios.post(`${API}/dealer-applications/${appId}/review`, {
        action,
        reject_reason: rejectReason
      });
      fetchApplications();
      setSelectedApp(null);
    } catch (error) {
      console.error('Failed to review application:', error);
      alert(error.response?.data?.detail || 'Failed to review');
    }
  };

  const handleToggleDealer = async (dealerId, field, value) => {
    try {
      await axios.patch(`${API}/dealers/${dealerId}`, { [field]: value });
      fetchDealers();
    } catch (error) {
      console.error('Failed to update dealer:', error);
    }
  };

  return (
    <div className="space-y-6" data-testid="dealer-management-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Dealer Management</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage dealer applications and accounts
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b">
        <button
          onClick={() => { setTab('applications'); setLoading(true); }}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            tab === 'applications' 
              ? 'border-primary text-primary' 
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          Applications
        </button>
        <button
          onClick={() => { setTab('dealers'); setLoading(true); }}
          className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
            tab === 'dealers' 
              ? 'border-primary text-primary' 
              : 'border-transparent text-muted-foreground hover:text-foreground'
          }`}
        >
          Active Dealers
        </button>
      </div>

      {tab === 'applications' && (
        <>
          {/* Status Filter */}
          <div className="flex gap-2">
            {['pending', 'approved', 'rejected', ''].map(status => (
              <button
                key={status || 'all'}
                onClick={() => { setStatusFilter(status); setLoading(true); }}
                className={`px-3 py-1.5 rounded-md text-sm font-medium capitalize transition-colors ${
                  statusFilter === status ? 'bg-primary text-primary-foreground' : 'bg-muted hover:bg-muted/80'
                }`}
              >
                {status || 'All'}
              </button>
            ))}
          </div>

          {/* Applications List */}
          <div className="rounded-md border bg-card overflow-hidden">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Company</th>
                  <th>Type</th>
                  <th>Country</th>
                  <th>Contact</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8">
                      <div className="flex items-center justify-center">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
                      </div>
                    </td>
                  </tr>
                ) : applications.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-8 text-muted-foreground">
                      No applications found
                    </td>
                  </tr>
                ) : (
                  applications.map((app) => (
                    <tr key={app.id} data-testid={`application-row-${app.id}`}>
                      <td>
                        <div className="font-medium">{app.company_name}</div>
                      </td>
                      <td>
                        <span className="text-sm">{dealerTypeLabels[app.dealer_type] || app.dealer_type}</span>
                      </td>
                      <td>
                        <span className="text-xs px-1.5 py-0.5 rounded bg-muted">{app.country}</span>
                      </td>
                      <td>
                        <div className="text-sm">{app.contact_name}</div>
                        <div className="text-xs text-muted-foreground">{app.contact_email}</div>
                      </td>
                      <td>
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold capitalize ${statusColors[app.status]}`}>
                          {app.status}
                        </span>
                      </td>
                      <td className="text-sm text-muted-foreground">
                        {new Date(app.created_at).toLocaleDateString()}
                      </td>
                      <td className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => setSelectedApp(app)}
                            className="p-1.5 rounded hover:bg-muted"
                            title="View Details"
                          >
                            <Eye size={16} />
                          </button>
                          {app.status === 'pending' && (
                            <>
                              <button
                                onClick={() => handleReview(app.id, 'approve')}
                                className="p-1.5 rounded hover:bg-emerald-100 text-emerald-600"
                                title="Approve"
                              >
                                <Check size={16} />
                              </button>
                              <button
                                onClick={() => {
                                  const reason = prompt('Enter reject reason:');
                                  if (reason) handleReview(app.id, 'reject', reason);
                                }}
                                className="p-1.5 rounded hover:bg-rose-100 text-rose-600"
                                title="Reject"
                              >
                                <X size={16} />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}

      {tab === 'dealers' && (
        <div className="grid gap-4 md:grid-cols-2">
          {loading ? (
            <div className="col-span-2 flex items-center justify-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
            </div>
          ) : dealers.length === 0 ? (
            <div className="col-span-2 text-center py-12 text-muted-foreground bg-card rounded-md border">
              <Building2 size={48} className="mx-auto mb-4 opacity-50" />
              <p>No active dealers</p>
            </div>
          ) : (
            dealers.map((dealer) => (
              <div key={dealer.id} className="bg-card rounded-md border p-4" data-testid={`dealer-card-${dealer.id}`}>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold">{dealer.company_name}</h3>
                    <p className="text-sm text-muted-foreground">{dealerTypeLabels[dealer.dealer_type]}</p>
                  </div>
                  <span className="text-xs px-1.5 py-0.5 rounded bg-muted">{dealer.country}</span>
                </div>
                
                <div className="grid grid-cols-2 gap-3 text-sm mb-4">
                  <div>
                    <p className="text-muted-foreground">Listings</p>
                    <p className="font-medium">{dealer.active_listing_count} / {dealer.listing_limit}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Status</p>
                    <p className={`font-medium ${dealer.is_active ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {dealer.is_active ? 'Active' : 'Inactive'}
                    </p>
                  </div>
                </div>
                
                <div className="flex gap-2">
                  <button
                    onClick={() => handleToggleDealer(dealer.id, 'is_active', !dealer.is_active)}
                    className={`flex-1 px-3 py-1.5 text-sm rounded-md border transition-colors ${
                      dealer.is_active 
                        ? 'text-rose-600 hover:bg-rose-50' 
                        : 'text-emerald-600 hover:bg-emerald-50'
                    }`}
                  >
                    {dealer.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                  <button
                    onClick={() => handleToggleDealer(dealer.id, 'can_publish', !dealer.can_publish)}
                    className={`flex-1 px-3 py-1.5 text-sm rounded-md border transition-colors ${
                      dealer.can_publish 
                        ? 'text-amber-600 hover:bg-amber-50' 
                        : 'text-emerald-600 hover:bg-emerald-50'
                    }`}
                  >
                    {dealer.can_publish ? 'Block Publishing' : 'Allow Publishing'}
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Application Detail Modal */}
      {selectedApp && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">Application Details</h2>
              <button onClick={() => setSelectedApp(null)} className="p-1 rounded hover:bg-muted">
                <X size={20} />
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div className="flex items-center justify-between">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold capitalize ${statusColors[selectedApp.status]}`}>
                  {selectedApp.status}
                </span>
                <span className="text-sm text-muted-foreground">
                  {new Date(selectedApp.created_at).toLocaleString()}
                </span>
              </div>
              
              <div>
                <h3 className="font-semibold text-lg">{selectedApp.company_name}</h3>
                <p className="text-muted-foreground">{dealerTypeLabels[selectedApp.dealer_type]}</p>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <MapPin size={14} className="text-muted-foreground" />
                  <span>{selectedApp.country}</span>
                </div>
                {selectedApp.website && (
                  <div className="flex items-center gap-2">
                    <Globe size={14} className="text-muted-foreground" />
                    <a href={selectedApp.website} target="_blank" rel="noreferrer" className="text-primary hover:underline truncate">
                      {selectedApp.website}
                    </a>
                  </div>
                )}
              </div>
              
              <div className="border-t pt-4">
                <h4 className="font-medium mb-2">Contact</h4>
                <div className="space-y-1 text-sm">
                  <p>{selectedApp.contact_name}</p>
                  <p className="flex items-center gap-2">
                    <Mail size={14} className="text-muted-foreground" />
                    {selectedApp.contact_email}
                  </p>
                  {selectedApp.contact_phone && (
                    <p className="flex items-center gap-2">
                      <Phone size={14} className="text-muted-foreground" />
                      {selectedApp.contact_phone}
                    </p>
                  )}
                </div>
              </div>
              
              {selectedApp.reject_reason && (
                <div className="border-t pt-4">
                  <h4 className="font-medium mb-2 text-rose-600">Reject Reason</h4>
                  <p className="text-sm">{selectedApp.reject_reason}</p>
                </div>
              )}
              
              {selectedApp.status === 'pending' && (
                <div className="flex gap-2 pt-4 border-t">
                  <button
                    onClick={() => handleReview(selectedApp.id, 'approve')}
                    className="flex-1 px-4 py-2 rounded-md bg-emerald-600 text-white font-medium hover:bg-emerald-700"
                  >
                    Approve
                  </button>
                  <button
                    onClick={() => {
                      const reason = prompt('Enter reject reason:');
                      if (reason) handleReview(selectedApp.id, 'reject', reason);
                    }}
                    className="flex-1 px-4 py-2 rounded-md bg-rose-600 text-white font-medium hover:bg-rose-700"
                  >
                    Reject
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
