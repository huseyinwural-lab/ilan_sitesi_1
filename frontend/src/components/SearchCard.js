import React from 'react';
import { Link } from 'react-router-dom';

const SearchCard = ({ listing }) => {
  const { id, title, price, price_type, price_amount, hourly_rate, currency, location, specs, image_url, badges, published_at } = listing;

  const formatPrice = (amount, currencyLabel, type = 'FIXED', hourlyValue = null) => {
    const numeric = type === 'HOURLY' ? hourlyValue : amount;
    if (numeric === null || numeric === undefined || numeric === '') return '-';
    const formatted = new Intl.NumberFormat('de-DE', { maximumFractionDigits: 0 }).format(Number(numeric));
    const currencyText = currencyLabel || 'EUR';
    return type === 'HOURLY'
      ? `${formatted} ${currencyText} / saat`
      : `${formatted} ${currencyText}`;
  };

  return (
    <Link to={`/ilan/${id}`} className="block group">
      <div className="bg-white border rounded-lg overflow-hidden hover:shadow-md transition duration-200">
        {/* Image */}
        <div className="relative aspect-[4/3] bg-gray-200">
          {image_url ? (
            <img src={image_url} alt={title} className="w-full h-full object-cover" />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-400 text-sm">No Image</div>
          )}
          
          {/* Badges */}
          <div className="absolute top-2 left-2 flex gap-1">
            {badges.includes('premium') && (
              <span className="bg-yellow-400 text-yellow-900 text-xs font-bold px-2 py-1 rounded">PREMIUM</span>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="p-3">
          <div className="font-bold text-lg text-blue-700 mb-1">
            {formatPrice(price, currency)}
          </div>
          
          <h3 className="text-gray-900 font-medium text-sm line-clamp-2 mb-2 group-hover:text-blue-600">
            {title}
          </h3>

          <div className="text-xs text-gray-500 flex flex-wrap gap-2 mb-2">
            {specs.rooms && <span>{specs.rooms}</span>}
            {specs.m2 && <span className="border-l pl-2">{specs.m2} m²</span>}
          </div>

          <div className="flex justify-between items-end text-xs text-gray-400 mt-2 border-t pt-2">
            <span>{location.city}</span>
            <span>{new Date(published_at).toLocaleDateString()}</span>
          </div>
        </div>
      </div>
    </Link>
  );
};

export default SearchCard;
