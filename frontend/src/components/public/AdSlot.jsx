import React, { useEffect, useState } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function resolveAssetUrl(assetUrl) {
  if (!assetUrl) return null;
  if (assetUrl.startsWith('http')) return assetUrl;
  return `${BACKEND_URL}${assetUrl}`;
}

export default function AdSlot({ placement, className = '' }) {
  const [ad, setAd] = useState(null);
  const [impressionLogged, setImpressionLogged] = useState(false);

  useEffect(() => {
    let active = true;
    setAd(null);
    setImpressionLogged(false);
    fetch(`${API}/ads?placement=${encodeURIComponent(placement)}`)
      .then((res) => res.json())
      .then((data) => {
        if (!active) return;
        const items = Array.isArray(data.items) ? data.items : [];
        setAd(items[0] || null);
      })
      .catch(() => {
        if (!active) return;
        setAd(null);
      });
    return () => {
      active = false;
    };
  }, [placement]);

  useEffect(() => {
    if (!ad?.id || impressionLogged) return;
    const payload = JSON.stringify({ placement });
    const endpoint = `${API}/ads/${ad.id}/impression`;
    try {
      if (navigator.sendBeacon) {
        const blob = new Blob([payload], { type: 'application/json' });
        navigator.sendBeacon(endpoint, blob);
      } else {
        fetch(endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: payload,
          keepalive: true,
        });
      }
    } catch (e) {
      // ignore impression failures
    }
    setImpressionLogged(true);
  }, [ad?.id, impressionLogged, placement]);

  if (!ad) return null;

  const assetUrl = resolveAssetUrl(ad.asset_url);
  const clickUrl = `${API}/ads/${ad.id}/click`;

  return (
    <div className={className} data-testid={`ad-slot-${placement}`}>
      <a
        href={clickUrl}
        className="block"
        target="_blank"
        rel="noreferrer"
        data-testid={`ad-slot-click-${placement}`}
      >
        {assetUrl ? (
          <img
            src={assetUrl}
            alt="Reklam"
            className="w-full rounded-lg border object-cover"
            data-testid={`ad-slot-image-${placement}`}
          />
        ) : (
          <div
            className="rounded-lg border bg-white px-4 py-6 text-sm text-muted-foreground"
            data-testid={`ad-slot-empty-${placement}`}
          >
            Reklam alanı
          </div>
        )}
      </a>
    </div>
  );
}
