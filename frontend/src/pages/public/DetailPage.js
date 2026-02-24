import React, { useState, useEffect } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const DetailPage = () => {
  const { id } = useParams(); // Expects :id (uuid) or :id-slug? 
  // Router in App.js is /ilan/:id. 
  // If we use /ilan/UUID-slug, we need to parse.
  const { search } = useLocation();
  const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

  const { token, user } = useAuth();
  
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [phone, setPhone] = useState(null);
  const [reportOpen, setReportOpen] = useState(false);
  const [reportReason, setReportReason] = useState('spam');
  const [reportNote, setReportNote] = useState('');
  const [reportError, setReportError] = useState(null);
  const [reportSuccess, setReportSuccess] = useState(null);
  const [reportSubmitting, setReportSubmitting] = useState(false);
  const [isFavorite, setIsFavorite] = useState(false);

  const reportReasons = [
    { value: 'spam', label: 'spam' },
    { value: 'scam_fraud', label: 'scam_fraud' },
    { value: 'prohibited_item', label: 'prohibited_item' },
    { value: 'wrong_category', label: 'wrong_category' },
    { value: 'harassment', label: 'harassment' },
    { value: 'copyright', label: 'copyright' },
    { value: 'other', label: 'other' },
  ];

  const toTestId = (value) => String(value || 'all')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-');

  const formatPriceLabel = (data) => {
    if (!data) return '-';
    const priceType = String(data.price_type || 'FIXED').toUpperCase();
    const currency = data.currency || 'EUR';
    const amount = priceType === 'HOURLY'
      ? data.hourly_rate
      : (data.price_amount ?? data.price);
    if (amount === null || amount === undefined || amount === '') return '-';
    const formatted = Number(amount).toLocaleString();
    return priceType === 'HOURLY'
      ? `${formatted} ${currency} / saat`
      : `${formatted} ${currency}`;
  };

  const [favoriteLoading, setFavoriteLoading] = useState(false);
  const [favoriteError, setFavoriteError] = useState('');

  const fetchFavoriteState = async (listingId) => {
    if (!user || !listingId) {
      setIsFavorite(false);
      return;
    }
    try {
      const res = await fetch(`${API}/v1/favorites/${listingId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (!res.ok) {
        throw new Error('Favorite state error');
      }
      const data = await res.json();
      setIsFavorite(Boolean(data.is_favorite));
      setFavoriteError('');
    } catch (err) {
      setIsFavorite(false);
      setFavoriteError('Favori durumu alınamadı');
    }
  };

  const handleToggleFavorite = async () => {
    if (!listing) return;
    if (!user) {
      window.location.assign('/login');
      return;
    }
    setFavoriteLoading(true);
    try {
      const res = await fetch(`${API}/v1/favorites/${listing.id}`, {
        method: isFavorite ? 'DELETE' : 'POST',
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (!res.ok) {
        throw new Error('Favorite toggle error');
      }
      const data = await res.json();
      setIsFavorite(Boolean(data.is_favorite));
      setFavoriteError('');
    } catch (err) {
      setFavoriteError('Favori güncellenemedi');
    } finally {
      setFavoriteLoading(false);
    }
  };

  useEffect(() => {
    if (!listing?.id) return;
    fetchFavoriteState(listing.id);
  }, [listing?.id, user]);

  // ID parsing is now handled inside useEffect

  useEffect(() => {
    // Extract UUID id from /ilan/vasita/{id}-{slug} or /ilan/{id}
    const match = id.match(/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/i);
    const realId = match ? match[0] : id;
    const query = new URLSearchParams(search);
    const preview = query.get('preview') === '1';
    const previewParam = preview ? '?preview=1' : '';

    setLoading(true);
    fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/listings/vehicle/${realId}${previewParam}`)
      .then(async (r) => {
        if (!r.ok) throw new Error('not found');
        return r.json();
      })
      .then((data) => {
        if (data) {
          data.contact = data.contact || { phone_protected: false };
          data.seller = data.seller || {};
          data.location = data.location || {};
          data.attributes = data.attributes || {};
          data.media = data.media || [];
        }
        setListing(data);
      })
      .catch(() => {
        setListing(null);
      })
      .finally(() => setLoading(false));
  }, [id, search]);

  const handleRevealPhone = async () => {
    // API Call
    // const res = await fetch(`/api/v1/contact/${realId}/phone`);
    setPhone("+49 170 1234567");
  };

  const submitReport = async () => {
    if (!listing) return;
    const note = reportNote.trim();
    if (reportReason === 'other' && !note) {
      setReportError('Not alanı zorunlu');
      return;
    }
    setReportError(null);
    setReportSubmitting(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/reports`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          listing_id: listing.id,
          reason: reportReason,
          reason_note: note || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        const detail = data?.detail || 'Şikayet oluşturulamadı';
        throw new Error(typeof detail === 'string' ? detail : detail?.code || 'Şikayet oluşturulamadı');
      }
      setReportSuccess('Şikayet alındı. Ekibimiz inceleyecek.');
      setReportOpen(false);
      setReportNote('');
      setReportReason('spam');
    } catch (e) {
      setReportError(e.message || 'Şikayet oluşturulamadı');
    } finally {
      setReportSubmitting(false);
    }
  };

  if (loading) return <div className="p-8 text-center">Loading...</div>;
  if (!listing) return <div className="p-8 text-center">Not Found</div>;

  const seller = listing.seller || {};
  const location = listing.location || {};
  const modules = listing.modules || {};
  const showPhotos = modules.photos?.enabled !== false;
  const showAddress = modules.address?.enabled !== false;
  const showContact = modules.contact?.enabled !== false;
  const phoneEnabled = Boolean(listing.contact_option_phone);
  const messageEnabled = listing.contact_option_message !== false;

  return (
    <>
      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Gallery */}
            {showPhotos && (
              <div className="aspect-video bg-gray-200 rounded-xl overflow-hidden" data-testid="listing-photos-section">
                <img src={listing.media[0].url} alt={listing.title} className="w-full h-full object-cover" />
              </div>
            )}

            {/* Header */}
            <div>
              <h1 className="text-4xl font-extrabold text-gray-900 mb-2" data-testid="listing-title">{listing.title}</h1>
              <div className="text-2xl font-bold text-blue-600" data-testid="listing-price">
                {formatPriceLabel(listing)}
              </div>
              {listing.secondary_price && listing.secondary_currency && (
                <div className="text-sm text-gray-500" data-testid="listing-secondary-price">
                  {listing.secondary_price.toLocaleString()} {listing.secondary_currency}
                </div>
              )}
              {showAddress && (
                <div className="text-gray-500 mt-1" data-testid="listing-address-section">
                  {location.city || ''} {location.country || ''}
                </div>
              )}
            </div>

            {/* Attributes */}
            <div className="bg-white border rounded-xl p-6">
              <h3 className="font-bold text-lg mb-4">Details</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(listing.attributes).map(([key, val]) => (
                  <div key={key}>
                    <span className="text-gray-500 text-sm block capitalize">{key.replace('_', ' ')}</span>
                    <span className="font-medium">{val}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Description */}
            <div className="bg-white border rounded-xl p-6">
              <h3 className="font-bold text-lg mb-4">Description</h3>
              <p className="text-gray-700 whitespace-pre-line">{listing.description || ''}</p>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Seller Card */}
            <div className="bg-white border rounded-xl p-6 shadow-sm">
              <h3 className="font-bold text-lg mb-2" data-testid="listing-seller-title">Seller</h3>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center text-xl">
                  👤
                </div>
                <div>
                  <div className="font-bold" data-testid="listing-seller-name">{seller.name || ''}</div>
                  {seller.is_verified && (
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full" data-testid="listing-seller-verified">Verified</span>
                  )}
                </div>
              </div>

              <div className="space-y-3">
                {showContact && (
                  <div className="space-y-3" data-testid="listing-contact-section">
                    {phoneEnabled ? (
                      !phone ? (
                        <button
                          onClick={handleRevealPhone}
                          className="w-full bg-green-600 text-white py-3 rounded-lg font-bold hover:bg-green-700 transition"
                          data-testid="listing-reveal-phone-button"
                        >
                          Telefonu Göster
                        </button>
                      ) : (
                        <div className="w-full bg-gray-100 py-3 rounded-lg font-bold text-center text-gray-800 border border-green-500" data-testid="listing-phone-number">
                          {phone}
                        </div>
                      )
                    ) : (
                      <div data-testid="listing-phone-hidden">Satıcı telefonunu gizledi</div>
                    )}

                    {messageEnabled ? (
                      <Link 
                        to={`/account/messages?listing=${listing.id}`} 
                        className="w-full bg-blue-600 text-white py-3 rounded-lg font-bold block text-center hover:bg-blue-700 transition"
                        data-testid="listing-send-message-button"
                      >
                        Mesaj Gönder
                      </Link>
                    ) : (
                      <div className="w-full bg-gray-100 py-3 rounded-lg font-bold text-center text-gray-500 border" data-testid="listing-message-disabled">
                        Mesajlaşma kapalı
                      </div>
                    )}
                  </div>
                )}

                <button
                  onClick={handleToggleFavorite}
                  disabled={favoriteLoading}
                  className={`w-full py-3 rounded-lg font-bold transition ${isFavorite ? 'bg-rose-600 text-white' : 'border border-rose-200 text-rose-600 hover:bg-rose-50'} ${favoriteLoading ? 'opacity-60' : ''}`}
                  data-testid="listing-favorite-toggle"
                >
                  {favoriteLoading ? 'Güncelleniyor...' : isFavorite ? 'Favoriden Kaldır' : 'Favoriye Ekle'}
                </button>

                {favoriteError && (
                  <p className="text-xs text-rose-600" data-testid="listing-favorite-error">{favoriteError}</p>
                )}

                <button
                  onClick={() => { setReportOpen(true); setReportError(null); }}
                  className="w-full border border-rose-200 text-rose-600 py-3 rounded-lg font-bold hover:bg-rose-50 transition"
                  data-testid="listing-report-button"
                >
                  Şikayet Et
                </button>
                {reportSuccess && (
                  <div className="text-xs text-green-600" data-testid="listing-report-success">
                    {reportSuccess}
                  </div>
                )}
              </div>
            </div>
          </div>

        </div>
      </div>
      {reportOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="listing-report-modal">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="font-bold text-lg" data-testid="listing-report-title">Şikayet Et</h3>
              <button
                onClick={() => setReportOpen(false)}
                className="text-sm px-2 py-1 border rounded"
                data-testid="listing-report-close"
              >
                Kapat
              </button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="text-sm font-medium">Reason</label>
                <Select value={reportReason} onValueChange={setReportReason}>
                  <SelectTrigger className="h-9 mt-2" data-testid="listing-report-reason-select">
                    <SelectValue placeholder="Reason" />
                  </SelectTrigger>
                  <SelectContent>
                    {reportReasons.map((opt) => (
                      <SelectItem
                        key={opt.value}
                        value={opt.value}
                        data-testid={`listing-report-reason-option-${toTestId(opt.value)}`}
                      >
                        {opt.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium">Note {reportReason === 'other' ? '(zorunlu)' : '(optional)'}</label>
                <textarea
                  value={reportNote}
                  onChange={(e) => setReportNote(e.target.value)}
                  className="mt-2 w-full min-h-[90px] p-3 rounded-md border text-sm"
                  placeholder="Detay paylaşabilirsiniz"
                  data-testid="listing-report-note-input"
                />
              </div>
              {reportError && (
                <div className="text-sm text-red-600" data-testid="listing-report-error">{reportError}</div>
              )}
              <button
                onClick={submitReport}
                className="w-full bg-rose-600 text-white py-3 rounded-lg font-bold hover:bg-rose-700 transition"
                disabled={reportSubmitting}
                data-testid="listing-report-submit"
              >
                {reportSubmitting ? 'Gönderiliyor…' : 'Şikayet Gönder'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DetailPage;
