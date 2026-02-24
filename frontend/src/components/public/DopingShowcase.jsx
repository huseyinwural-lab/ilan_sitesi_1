import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function DopingShowcase({ placement }) {
  const [items, setItems] = useState([]);

  useEffect(() => {
    let active = true;
    const qs = placement ? `?placement=${placement}` : '';
    fetch(`${API}/doping/placements${qs}`)
      .then((res) => res.json())
      .then((data) => {
        if (!active) return;
        setItems(Array.isArray(data.items) ? data.items : []);
      })
      .catch(() => {
        if (!active) return;
        setItems([]);
      });
    return () => {
      active = false;
    };
  }, [placement]);

  if (items.length === 0) return null;

  return (
    <div className="space-y-3" data-testid={`doping-showcase-${placement}`}>
      <div className="text-sm font-semibold text-[#1B263B]">Öne Çıkan İlanlar</div>
      <div className="grid gap-3 md:grid-cols-2">
        {items.map((item) => (
          <div key={item.doping_id} className="rounded-lg border bg-white p-3" data-testid={`doping-card-${item.doping_id}`}>
            <div className="text-sm font-semibold" data-testid={`doping-title-${item.doping_id}`}>{item.title}</div>
            <div className="text-xs text-[#415A77]" data-testid={`doping-price-${item.doping_id}`}>
              {item.price ? `${item.price} ${item.currency}` : 'Fiyat yok'}
            </div>
            <Link
              to={`/listing/${item.listing_id}`}
              className="mt-2 inline-flex text-xs font-semibold text-[#F57C00]"
              data-testid={`doping-link-${item.doping_id}`}
            >
              İlana Git
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
