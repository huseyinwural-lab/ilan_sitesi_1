import React, { useEffect, useState } from 'react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function resolveAssetUrl(assetUrl) {
  if (!assetUrl) return null;
  if (assetUrl.startsWith('http')) return assetUrl;
  return `${BACKEND_URL}${assetUrl}`;
}

export default function AdSlot({ placement, className = '', country = '', rotation = false, size = 'auto' }) {
  const [ad, setAd] = useState(null);
  const [impressionLogged, setImpressionLogged] = useState(false);

  useEffect(() => {
    let active = true;
    setAd(null);
    setImpressionLogged(false);
    const params = new URLSearchParams();
    params.set('placement', placement);
    if (country) params.set('country', String(country).toUpperCase());
    params.set('rotation', rotation ? 'true' : 'false');
    fetch(`${API}/ads/resolve?${params.toString()}`)
      .then((res) => res.json())
      .then((data) => {
        if (!active) return;
        const items = Array.isArray(data.items) ? data.items : [];
        setAd(data.item || items[0] || null);
      })
      .catch(() => {
        if (!active) return;
        setAd(null);
      });
    return () => {
      active = false;
    };
  }, [placement, country, rotation]);

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

  if (!ad) {
    return (
      <div className={className} data-testid={`ad-slot-${placement}`}>
        <div
          className="rounded-lg border bg-white px-4 py-6 text-sm text-muted-foreground"
          data-testid={`ad-slot-empty-${placement}`}
        >
          Bu placement için aktif reklam yok
        </div>
      </div>
    );
  }

  const assetUrl = resolveAssetUrl(ad.asset_url);
  const clickUrl = `${API}/ads/${ad.id}/click`;
  const sizeClassMap = {
    auto: 'w-full',
    horizontal: 'aspect-[16/4] w-full',
    vertical: 'aspect-[3/4] max-w-[280px]',
    square: 'aspect-square max-w-[320px]',
  };
  const imageSizeClass = sizeClassMap[String(size || 'auto').toLowerCase()] || sizeClassMap.auto;

  return (
    <div className={className} data-testid={`ad-slot-${placement}`}>
      <a
        href={clickUrl}
        className="block"
        data-testid={`ad-slot-click-${placement}`}
      >
        {assetUrl ? (
          <img
            src={assetUrl}
            alt="Reklam"
            className={`${imageSizeClass} rounded-lg border object-cover`}
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
