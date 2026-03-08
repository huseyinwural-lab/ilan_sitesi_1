const ICON_LIBRARY_SEEDS = [
  { key: 'home', label: 'Ev', code: 'EV', color: '#0ea5e9', tags: ['emlak', 'konut'] },
  { key: 'apartment', label: 'Daire', code: 'DR', color: '#0284c7', tags: ['emlak', 'konut'] },
  { key: 'villa', label: 'Villa', code: 'VL', color: '#06b6d4', tags: ['emlak', 'konut'] },
  { key: 'office', label: 'Ofis', code: 'OF', color: '#0f766e', tags: ['emlak', 'ticari'] },
  { key: 'shop', label: 'Dükkan', code: 'DK', color: '#0891b2', tags: ['emlak', 'ticari'] },
  { key: 'land', label: 'Arsa', code: 'AR', color: '#16a34a', tags: ['emlak', 'arsa'] },
  { key: 'warehouse', label: 'Depo', code: 'DP', color: '#059669', tags: ['emlak', 'ticari'] },
  { key: 'hotel', label: 'Otel', code: 'OT', color: '#0d9488', tags: ['emlak', 'turizm'] },

  { key: 'car', label: 'Araba', code: 'AB', color: '#3b82f6', tags: ['vasita', 'otomobil'] },
  { key: 'suv', label: 'SUV', code: 'SV', color: '#2563eb', tags: ['vasita', 'otomobil'] },
  { key: 'motorcycle', label: 'Motosiklet', code: 'MT', color: '#1d4ed8', tags: ['vasita', 'motosiklet'] },
  { key: 'truck', label: 'Kamyon', code: 'KM', color: '#1e40af', tags: ['vasita', 'ticari'] },
  { key: 'van', label: 'Minivan', code: 'MN', color: '#312e81', tags: ['vasita', 'ticari'] },
  { key: 'bus', label: 'Otobüs', code: 'OB', color: '#3730a3', tags: ['vasita', 'ticari'] },
  { key: 'tractor', label: 'Traktör', code: 'TR', color: '#4338ca', tags: ['vasita', 'tarim'] },
  { key: 'boat', label: 'Tekne', code: 'TK', color: '#4f46e5', tags: ['vasita', 'deniz'] },

  { key: 'phone', label: 'Telefon', code: 'TL', color: '#7c3aed', tags: ['teknoloji', 'elektronik'] },
  { key: 'computer', label: 'Bilgisayar', code: 'PC', color: '#6d28d9', tags: ['teknoloji', 'elektronik'] },
  { key: 'tablet', label: 'Tablet', code: 'TB', color: '#5b21b6', tags: ['teknoloji', 'elektronik'] },
  { key: 'camera', label: 'Kamera', code: 'KM', color: '#8b5cf6', tags: ['teknoloji', 'elektronik'] },
  { key: 'tv', label: 'TV', code: 'TV', color: '#a855f7', tags: ['teknoloji', 'elektronik'] },
  { key: 'audio', label: 'Ses', code: 'SS', color: '#9333ea', tags: ['teknoloji', 'elektronik'] },

  { key: 'furniture', label: 'Mobilya', code: 'MB', color: '#f59e0b', tags: ['yasam', 'ev'] },
  { key: 'fashion', label: 'Moda', code: 'MD', color: '#f97316', tags: ['yasam', 'giyim'] },
  { key: 'beauty', label: 'Kozmetik', code: 'KZ', color: '#ea580c', tags: ['yasam', 'bakim'] },
  { key: 'kids', label: 'Bebek', code: 'BB', color: '#fb7185', tags: ['yasam', 'aile'] },
  { key: 'pet', label: 'Evcil', code: 'EV', color: '#ec4899', tags: ['yasam', 'hobi'] },
  { key: 'sport', label: 'Spor', code: 'SP', color: '#ef4444', tags: ['yasam', 'hobi'] },
  { key: 'hobby', label: 'Hobi', code: 'HB', color: '#dc2626', tags: ['yasam', 'hobi'] },
  { key: 'art', label: 'Sanat', code: 'SN', color: '#f43f5e', tags: ['yasam', 'hobi'] },

  { key: 'job', label: 'İş', code: 'IS', color: '#14b8a6', tags: ['hizmet', 'kariyer'] },
  { key: 'education', label: 'Eğitim', code: 'EG', color: '#06b6d4', tags: ['hizmet', 'egitim'] },
  { key: 'health', label: 'Sağlık', code: 'SG', color: '#22c55e', tags: ['hizmet', 'saglik'] },
  { key: 'food', label: 'Yemek', code: 'YM', color: '#f59e0b', tags: ['hizmet', 'gida'] },
  { key: 'travel', label: 'Seyahat', code: 'SY', color: '#0ea5e9', tags: ['hizmet', 'turizm'] },
  { key: 'event', label: 'Etkinlik', code: 'ET', color: '#eab308', tags: ['hizmet', 'organizasyon'] },
  { key: 'music', label: 'Müzik', code: 'MZ', color: '#6366f1', tags: ['hizmet', 'hobi'] },
  { key: 'tools', label: 'Alet', code: 'AL', color: '#475569', tags: ['hizmet', 'teknik'] },
  { key: 'cleaning', label: 'Temizlik', code: 'TM', color: '#0ea5e9', tags: ['hizmet', 'ev'] },
  { key: 'repair', label: 'Tamir', code: 'TR', color: '#64748b', tags: ['hizmet', 'teknik'] },
];

const escapeSvgText = (value = '') => String(value || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const buildBadgeSvg = ({ code, color }) => {
  const safeCode = escapeSvgText(code || '--').slice(0, 2).toUpperCase();
  const safeColor = String(color || '#0ea5e9');
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"><rect x="2" y="2" width="20" height="20" rx="6" fill="${safeColor}"/><rect x="4" y="4" width="16" height="16" rx="5" fill="rgba(255,255,255,0.18)"/><text x="12" y="14.5" text-anchor="middle" fill="#ffffff" font-size="6.5" font-family="Arial, sans-serif" font-weight="700">${safeCode}</text></svg>`;
};

export const APPROVED_CATEGORY_ICON_LIBRARY = ICON_LIBRARY_SEEDS.map((seed) => ({
  ...seed,
  svg: buildBadgeSvg(seed),
}));
