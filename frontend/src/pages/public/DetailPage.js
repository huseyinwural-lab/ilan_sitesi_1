import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';

const DetailPage = () => {
  const { id } = useParams(); // Expects :id (uuid) or :id-slug? 
  // Router in App.js is /ilan/:id. 
  // If we use /ilan/UUID-slug, we need to parse.
  
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [phone, setPhone] = useState(null);

  // ID parsing is now handled inside useEffect

  useEffect(() => {
    // Extract UUID id from /ilan/vasita/{id}-{slug} or /ilan/{id}
    const match = id.match(/^([a-f0-9\-]{36})/i);
    const realId = match ? match[1] : id;

    setLoading(true);
    fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/listings/vehicle/${realId}`)
      .then(async (r) => {
        if (!r.ok) throw new Error('not found');
        return r.json();
      })
      .then((data) => {
        setListing(data);
      })
      .catch(() => {
        setListing(null);
      })
      .finally(() => setLoading(false));
  }, [id]);

  const handleRevealPhone = async () => {
    // API Call
    // const res = await fetch(`/api/v1/contact/${realId}/phone`);
    setPhone("+49 170 1234567");
  };

  if (loading) return <div className="p-8 text-center">Loading...</div>;
  if (!listing) return <div className="p-8 text-center">Not Found</div>;

  return (
    <>
      <Helmet>
        <title>{`${listing.title} | ${listing.location.city}`}</title>
        <meta name="description" content={`${listing.title}. Price: ${listing.price} ${listing.currency}`} />
        <link rel="canonical" href={`https://platform.com/ilan/vasita/${listing.id}`} />
      </Helmet>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Gallery */}
            <div className="aspect-video bg-gray-200 rounded-xl overflow-hidden">
              <img src={listing.media[0].url} alt={listing.title} className="w-full h-full object-cover" />
            </div>

            {/* Header */}
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{listing.title}</h1>
              <div className="text-2xl font-bold text-blue-600">
                {listing.price.toLocaleString()} {listing.currency}
              </div>
              <div className="text-gray-500 mt-1">
                {listing.location.city || ''} {listing.location.country || ''}
              </div>
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
              <h3 className="font-bold text-lg mb-2">Seller</h3>
              <div className="flex items-center gap-3 mb-4">
                <div className="w-12 h-12 bg-gray-200 rounded-full flex items-center justify-center text-xl">
                  👤
                </div>
                <div>
                  <div className="font-bold">{listing.seller.name || ''}</div>
                  {listing.seller.is_verified && (
                    <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full">Verified</span>
                  )}
                </div>
              </div>

              <div className="space-y-3">
                {listing.contact.phone_protected ? (
                  !phone ? (
                    <button 
                      onClick={handleRevealPhone}
                      className="w-full bg-green-600 text-white py-3 rounded-lg font-bold hover:bg-green-700 transition"
                    >
                      Show Phone Number
                    </button>
                  ) : (
                    <div className="w-full bg-gray-100 py-3 rounded-lg font-bold text-center text-gray-800 border border-green-500">
                      {phone}
                    </div>
                  )
                ) : (
                  <div>Phone hidden by seller</div>
                )}

                <Link 
                  to={`/account/messages/new?listing=${listing.id}`} 
                  className="w-full bg-blue-600 text-white py-3 rounded-lg font-bold block text-center hover:bg-blue-700 transition"
                >
                  Send Message
                </Link>
              </div>
            </div>
          </div>

        </div>
      </div>
    </>
  );
};

export default DetailPage;
