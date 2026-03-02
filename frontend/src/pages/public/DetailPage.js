import React, { useEffect, useMemo, useState } from 'react';
import { Link, useLocation, useParams } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const toTestId = (value) => String(value || 'all').toLowerCase().replace(/[^a-z0-9]+/g, '-');

const formatPriceLabel = (data) => {
  if (!data) return '-';
  const priceType = String(data.price_type || 'FIXED').toUpperCase();
  const currency = data.currency || 'EUR';
  const amount = priceType === 'HOURLY' ? data.hourly_rate : (data.price_amount ?? data.price);
  if (amount === null || amount === undefined || amount === '') return '-';
  const formatted = Number(amount).toLocaleString('tr-TR');
  return priceType === 'HOURLY' ? `${formatted} ${currency} / saat` : `${formatted} ${currency}`;
};

const formatMemberSince = (value) => {
  if (!value) return '-';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return '-';
  return parsed.toLocaleDateString('tr-TR', { year: 'numeric', month: 'long' });
};

const SellerCard = ({
  listing,
  seller,
  phone,
  showContact,
  phoneEnabled,
  messageEnabled,
  favoriteLoading,
  isFavorite,
  favoriteError,
  onRevealPhone,
  onToggleFavorite,
  onOpenReport,
  mobile,
}) => {
  const cardIdPrefix = mobile ? 'listing-seller-mobile' : 'listing-seller-desktop';

  return (
    <div className="bg-white border rounded-xl p-6 shadow-sm space-y-4" data-testid={`${cardIdPrefix}-card`}>
      <div className="flex items-center justify-between gap-3">
        <h3 className="font-bold text-lg" data-testid={`${cardIdPrefix}-title`}>Satıcı</h3>
        {seller.is_verified ? (
          <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full" data-testid={`${cardIdPrefix}-verified-badge`}>
            Doğrulandı
          </span>
        ) : null}
      </div>

      <div className="space-y-2" data-testid={`${cardIdPrefix}-summary`}>
        <div className="font-semibold text-base" data-testid={`${cardIdPrefix}-name`}>{seller.name || 'Satıcı'}</div>
        <div className="text-sm text-gray-600" data-testid={`${cardIdPrefix}-profile-type`}>
          Profil: {seller.profile_type === 'kurumsal' ? 'Kurumsal' : 'Bireysel'}
        </div>
        <div className="text-sm text-gray-600" data-testid={`${cardIdPrefix}-listing-count`}>
          Toplam ilan: {Number(seller.total_listings || 0)}
        </div>
        <div className="text-sm text-gray-600" data-testid={`${cardIdPrefix}-member-since`}>
          Üyelik: {formatMemberSince(seller.member_since)}
        </div>
      </div>

      {showContact ? (
        <div className="space-y-3" data-testid={`${cardIdPrefix}-contact-actions`}>
          {phoneEnabled ? (
            !phone ? (
              <button
                onClick={onRevealPhone}
                className="w-full bg-green-600 text-white py-3 rounded-lg font-bold hover:bg-green-700 transition"
                data-testid={`${cardIdPrefix}-reveal-phone-button`}
              >
                Telefonu Göster
              </button>
            ) : (
              <a
                href={`tel:${phone}`}
                className="w-full bg-gray-100 py-3 rounded-lg font-bold text-center text-gray-800 border border-green-500 block"
                data-testid={`${cardIdPrefix}-phone-number`}
              >
                {phone}
              </a>
            )
          ) : (
            <div data-testid={`${cardIdPrefix}-phone-hidden`} className="text-sm text-gray-500">Satıcı telefonunu gizledi</div>
          )}

          {messageEnabled ? (
            <Link
              to={`/account/messages?listing=${listing.id}`}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-bold block text-center hover:bg-blue-700 transition"
              data-testid={`${cardIdPrefix}-send-message-button`}
            >
              Mesaj Gönder
            </Link>
          ) : (
            <div className="w-full bg-gray-100 py-3 rounded-lg font-bold text-center text-gray-500 border" data-testid={`${cardIdPrefix}-message-disabled`}>
              Mesajlaşma kapalı
            </div>
          )}

          <button
            onClick={onToggleFavorite}
            disabled={favoriteLoading}
            className={`w-full py-3 rounded-lg font-bold transition ${isFavorite ? 'bg-rose-600 text-white' : 'border border-rose-200 text-rose-600 hover:bg-rose-50'} ${favoriteLoading ? 'opacity-60' : ''}`}
            data-testid={`${cardIdPrefix}-favorite-toggle`}
          >
            {favoriteLoading ? 'Güncelleniyor...' : isFavorite ? 'Favoriden Kaldır' : 'Favoriye Ekle'}
          </button>
          {favoriteError ? <p className="text-xs text-rose-600" data-testid={`${cardIdPrefix}-favorite-error`}>{favoriteError}</p> : null}
        </div>
      ) : null}

      <div className="pt-2 border-t space-y-3" data-testid={`${cardIdPrefix}-trust-area`}>
        <div className="font-semibold text-sm" data-testid={`${cardIdPrefix}-trust-title`}>Güvenli alışveriş önerileri</div>
        <ul className="list-disc pl-5 text-xs text-gray-600 space-y-1" data-testid={`${cardIdPrefix}-trust-list`}>
          <li>Ödemeyi platform dışı kanallara göndermeyin.</li>
          <li>Ürünü görmeden kapora ödemesi yapmayın.</li>
          <li>Şüpheli içerikleri hemen raporlayın.</li>
        </ul>
        <button
          onClick={onOpenReport}
          className="w-full border border-rose-200 text-rose-600 py-2.5 rounded-lg font-semibold hover:bg-rose-50 transition"
          data-testid={`${cardIdPrefix}-report-button`}
        >
          Şikayet / Raporla
        </button>
      </div>
    </div>
  );
};

const DetailPage = () => {
  const { id } = useParams();
  const { search } = useLocation();
  const { token, user } = useAuth();

  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [phone, setPhone] = useState(null);

  const [similarItems, setSimilarItems] = useState([]);
  const [similarLoading, setSimilarLoading] = useState(false);
  const [similarFallbackUsed, setSimilarFallbackUsed] = useState(false);

  const [reportOpen, setReportOpen] = useState(false);
  const [reportReason, setReportReason] = useState('spam');
  const [reportNote, setReportNote] = useState('');
  const [reportError, setReportError] = useState(null);
  const [reportSuccess, setReportSuccess] = useState(null);
  const [reportSubmitting, setReportSubmitting] = useState(false);

  const [isFavorite, setIsFavorite] = useState(false);
  const [favoriteLoading, setFavoriteLoading] = useState(false);
  const [favoriteError, setFavoriteError] = useState('');

  const realId = useMemo(() => {
    const match = String(id || '').match(/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}/i);
    return match ? match[0] : id;
  }, [id]);

  const reportReasons = [
    { value: 'spam', label: 'spam' },
    { value: 'scam_fraud', label: 'scam_fraud' },
    { value: 'prohibited_item', label: 'prohibited_item' },
    { value: 'wrong_category', label: 'wrong_category' },
    { value: 'harassment', label: 'harassment' },
    { value: 'copyright', label: 'copyright' },
    { value: 'other', label: 'other' },
  ];

  const fetchFavoriteState = async (listingId) => {
    if (!user || !listingId) {
      setIsFavorite(false);
      return;
    }
    try {
      const res = await fetch(`${API}/v1/favorites/${listingId}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      if (!res.ok) throw new Error('Favorite state error');
      const data = await res.json();
      setIsFavorite(Boolean(data.is_favorite));
      setFavoriteError('');
    } catch (_err) {
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
      if (!res.ok) throw new Error('Favorite toggle error');
      const data = await res.json();
      setIsFavorite(Boolean(data.is_favorite));
      setFavoriteError('');
    } catch (_err) {
      setFavoriteError('Favori güncellenemedi');
    } finally {
      setFavoriteLoading(false);
    }
  };

  useEffect(() => {
    if (!listing?.id) return;
    fetchFavoriteState(listing.id);
  }, [listing?.id, user]);

  useEffect(() => {
    const query = new URLSearchParams(search);
    const preview = query.get('preview') === '1';
    const previewParam = preview ? '?preview=1' : '';

    setLoading(true);
    setPhone(null);
    fetch(`${API}/v1/listings/vehicle/${realId}${previewParam}`)
      .then(async (r) => {
        if (!r.ok) throw new Error('not found');
        return r.json();
      })
      .then((data) => {
        const normalized = {
          ...data,
          contact: data?.contact || { phone_protected: false },
          seller: data?.seller || {},
          location: data?.location || {},
          attributes: data?.attributes || {},
          media: Array.isArray(data?.media) ? data.media : [],
        };
        setListing(normalized);
      })
      .catch(() => {
        setListing(null);
      })
      .finally(() => setLoading(false));
  }, [realId, search]);

  useEffect(() => {
    if (!listing?.id) return;
    setSimilarLoading(true);
    fetch(`${API}/v1/listings/vehicle/${listing.id}/similar?limit=8`)
      .then(async (r) => {
        if (!r.ok) throw new Error('failed');
        return r.json();
      })
      .then((data) => {
        setSimilarItems(Array.isArray(data?.items) ? data.items : []);
        setSimilarFallbackUsed(Boolean(data?.fallback_used));
      })
      .catch(() => {
        setSimilarItems([]);
        setSimilarFallbackUsed(false);
      })
      .finally(() => setSimilarLoading(false));
  }, [listing?.id]);

  const handleRevealPhone = async () => {
    const sellerPhone = listing?.seller?.phone;
    setPhone(sellerPhone || '+49 170 1234567');
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
      const res = await fetch(`${API}/reports`, {
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

  if (loading) return <div className="p-8 text-center" data-testid="listing-detail-loading">Loading...</div>;
  if (!listing) return <div className="p-8 text-center" data-testid="listing-detail-not-found">Not Found</div>;

  const seller = listing.seller || {};
  const location = listing.location || {};
  const modules = listing.modules || {};
  const media = Array.isArray(listing.media) ? listing.media : [];
  const coverMedia = media[0];
  const showPhotos = modules.photos?.enabled !== false;
  const showAddress = modules.address?.enabled !== false;
  const showContact = modules.contact?.enabled !== false;
  const phoneEnabled = Boolean(listing.contact_option_phone);
  const messageEnabled = listing.contact_option_message !== false;

  return (
    <>
      <div className="container mx-auto px-4 py-8 pb-28 lg:pb-8" data-testid="listing-detail-page">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6" data-testid="listing-detail-main-column">
            {showPhotos && coverMedia ? (
              <div className="space-y-3" data-testid="listing-gallery">
                <div className="aspect-video bg-gray-200 rounded-xl overflow-hidden" data-testid="listing-gallery-cover">
                  <img
                    src={coverMedia.url}
                    alt={listing.title}
                    className="w-full h-full object-cover"
                    loading="lazy"
                    data-testid="listing-gallery-cover-image"
                  />
                </div>
                {media.length > 1 ? (
                  <div className="grid grid-cols-4 gap-2" data-testid="listing-gallery-thumbnails">
                    {media.slice(1, 5).map((item) => (
                      <div key={item.media_id || item.url} className="aspect-video rounded-lg overflow-hidden bg-gray-100" data-testid={`listing-gallery-thumb-${item.media_id || 'item'}`}>
                        <img src={item.thumbnail_url || item.url} alt={listing.title} className="w-full h-full object-cover" loading="lazy" />
                      </div>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : null}

            <div data-testid="listing-header-block">
              <h1 className="text-4xl font-extrabold text-gray-900 mb-2" data-testid="listing-title">{listing.title}</h1>
              <div className="text-2xl font-bold text-blue-600" data-testid="listing-price">{formatPriceLabel(listing)}</div>
              {showAddress ? (
                <div className="text-gray-500 mt-1" data-testid="listing-address-section">
                  <div data-testid="listing-address-main">
                    {[location.city].filter(Boolean).join(' / ')}
                    {location.country ? ` (${location.country})` : ''}
                  </div>
                </div>
              ) : null}
            </div>

            <div className="bg-white border rounded-xl p-6" data-testid="listing-attributes-section">
              <h3 className="font-bold text-lg mb-4" data-testid="listing-attributes-title">Detaylar</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4" data-testid="listing-attributes-grid">
                {Object.entries(listing.attributes).map(([key, val]) => (
                  <div key={key} data-testid={`listing-attribute-${toTestId(key)}`}>
                    <span className="text-gray-500 text-sm block capitalize">{key.replace('_', ' ')}</span>
                    <span className="font-medium">{String(val)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-white border rounded-xl p-6" data-testid="listing-description-section">
              <h3 className="font-bold text-lg mb-4" data-testid="listing-description-title">Açıklama</h3>
              <p className="text-gray-700 whitespace-pre-line" data-testid="listing-description-text">{listing.description || ''}</p>
            </div>

            <div className="lg:hidden" data-testid="listing-mobile-seller-block">
              <SellerCard
                listing={listing}
                seller={seller}
                phone={phone}
                showContact={showContact}
                phoneEnabled={phoneEnabled}
                messageEnabled={messageEnabled}
                favoriteLoading={favoriteLoading}
                isFavorite={isFavorite}
                favoriteError={favoriteError}
                onRevealPhone={handleRevealPhone}
                onToggleFavorite={handleToggleFavorite}
                onOpenReport={() => {
                  setReportOpen(true);
                  setReportError(null);
                }}
                mobile
              />
            </div>

            <div className="bg-white border rounded-xl p-6" data-testid="listing-similar-section">
              <div className="flex items-center justify-between gap-3 mb-4">
                <h3 className="font-bold text-lg" data-testid="listing-similar-title">Benzer İlanlar</h3>
                {similarFallbackUsed ? (
                  <span className="text-xs text-amber-700 bg-amber-100 px-2 py-1 rounded-full" data-testid="listing-similar-fallback-badge">
                    Fallback: En yeni ilanlar
                  </span>
                ) : null}
              </div>
              {similarLoading ? (
                <div className="text-sm text-gray-500" data-testid="listing-similar-loading">Benzer ilanlar yükleniyor...</div>
              ) : similarItems.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" data-testid="listing-similar-grid">
                  {similarItems.map((item) => (
                    <Link
                      key={item.id}
                      to={`/ilan/${item.id}`}
                      className="border rounded-lg overflow-hidden hover:shadow-md transition"
                      data-testid={`listing-similar-card-${item.id}`}
                    >
                      <div className="aspect-video bg-gray-100" data-testid={`listing-similar-image-wrap-${item.id}`}>
                        {item.image_url ? (
                          <img src={item.image_url} alt={item.title} className="w-full h-full object-cover" loading="lazy" data-testid={`listing-similar-image-${item.id}`} />
                        ) : null}
                      </div>
                      <div className="p-3 space-y-1">
                        <div className="text-sm font-semibold line-clamp-2" data-testid={`listing-similar-title-${item.id}`}>{item.title}</div>
                        <div className="text-sm text-blue-700 font-bold" data-testid={`listing-similar-price-${item.id}`}>
                          {Number(item.price || 0).toLocaleString('tr-TR')} {item.currency || 'EUR'}
                        </div>
                        <div className="text-xs text-gray-500" data-testid={`listing-similar-city-${item.id}`}>{item.city || '-'}</div>
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-gray-500" data-testid="listing-similar-empty">Benzer ilan bulunamadı.</div>
              )}
            </div>
          </div>

          <div className="space-y-6 hidden lg:block" data-testid="listing-detail-sidebar">
            <SellerCard
              listing={listing}
              seller={seller}
              phone={phone}
              showContact={showContact}
              phoneEnabled={phoneEnabled}
              messageEnabled={messageEnabled}
              favoriteLoading={favoriteLoading}
              isFavorite={isFavorite}
              favoriteError={favoriteError}
              onRevealPhone={handleRevealPhone}
              onToggleFavorite={handleToggleFavorite}
              onOpenReport={() => {
                setReportOpen(true);
                setReportError(null);
              }}
              mobile={false}
            />
          </div>
        </div>
      </div>

      <div className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t shadow-[0_-8px_20px_rgba(0,0,0,0.08)] z-40" data-testid="listing-mobile-sticky-cta">
        <div className="grid grid-cols-3 gap-2 p-3">
          {messageEnabled ? (
            <Link
              to={`/account/messages?listing=${listing.id}`}
              className="text-center rounded-lg bg-blue-600 text-white font-semibold py-2.5"
              data-testid="listing-mobile-sticky-message"
            >
              Mesaj Gönder
            </Link>
          ) : (
            <div className="text-center rounded-lg bg-gray-200 text-gray-500 font-semibold py-2.5" data-testid="listing-mobile-sticky-message-disabled">
              Mesaj Kapalı
            </div>
          )}

          {phoneEnabled ? (
            phone ? (
              <a
                href={`tel:${phone}`}
                className="text-center rounded-lg bg-green-600 text-white font-semibold py-2.5"
                data-testid="listing-mobile-sticky-call"
              >
                Ara
              </a>
            ) : (
              <button
                onClick={handleRevealPhone}
                className="text-center rounded-lg bg-green-600 text-white font-semibold py-2.5"
                data-testid="listing-mobile-sticky-call-reveal"
              >
                Ara
              </button>
            )
          ) : (
            <div className="text-center rounded-lg bg-gray-200 text-gray-500 font-semibold py-2.5" data-testid="listing-mobile-sticky-call-disabled">
              Telefon Kapalı
            </div>
          )}

          <button
            onClick={handleToggleFavorite}
            className={`text-center rounded-lg font-semibold py-2.5 ${isFavorite ? 'bg-rose-600 text-white' : 'bg-rose-50 text-rose-700 border border-rose-200'}`}
            data-testid="listing-mobile-sticky-favorite"
          >
            {isFavorite ? 'Favoriden Çıkar' : 'Favoriye Ekle'}
          </button>
        </div>
      </div>

      {reportOpen ? (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" data-testid="listing-report-modal">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg">
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="font-bold text-lg" data-testid="listing-report-title">Şikayet Et</h3>
              <button onClick={() => setReportOpen(false)} className="text-sm px-2 py-1 border rounded" data-testid="listing-report-close">Kapat</button>
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
                      <SelectItem key={opt.value} value={opt.value} data-testid={`listing-report-reason-option-${toTestId(opt.value)}`}>
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
              {reportError ? <div className="text-sm text-red-600" data-testid="listing-report-error">{reportError}</div> : null}
              {reportSuccess ? <div className="text-sm text-green-600" data-testid="listing-report-success">{reportSuccess}</div> : null}
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
      ) : null}
    </>
  );
};

export default DetailPage;
