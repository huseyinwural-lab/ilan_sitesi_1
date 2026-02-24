import React, { useEffect, useState } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AdPlacement({ placement, title }) {
  const [ad, setAd] = useState(null);

  useEffect(() => {
    let active = true;
    fetch(`${API}/ads?placement=${placement}`)
      .then((res) => res.json())
      .then((data) => {
        if (!active) return;
        const item = Array.isArray(data.items) ? data.items[0] : null;
        setAd(item || null);
      })
      .catch(() => {
        if (!active) return;
        setAd(null);
      });
    return () => {
      active = false;
    };
  }, [placement]);

  if (!ad || !ad.asset_url) {
    return null;
  }

  return (
    <div className="rounded-lg border bg-white p-3" data-testid={`ad-placement-${placement}`}>
      {title && <div className="text-xs text-[#415A77]" data-testid={`ad-placement-title-${placement}`}>{title}</div>}
      <a href={ad.target_url || '#'} target="_blank" rel="noreferrer">
        <img src={ad.asset_url} alt="Advertisement" className="mt-2 w-full rounded" />
      </a>
    </div>
  );
}
