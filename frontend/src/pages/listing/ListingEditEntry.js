import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const FORM_STORAGE_KEY = 'ilan_ver_listing_form';

export default function ListingEditEntry() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  useEffect(() => {
    let alive = true;

    const bootstrap = async () => {
      const token = localStorage.getItem('access_token') || localStorage.getItem('token') || '';
      if (!token) {
        navigate('/login', { replace: true });
        return;
      }

      try {
        const res = await fetch(`${API}/v1/listings/vehicle/${id}/draft`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(data?.detail?.message || data?.detail || 'İlan yüklenemedi');
        }

        const item = data?.item;
        if (!item) throw new Error('İlan bulunamadı');

        const selectedPath = Array.isArray(item.selected_category_path) ? item.selected_category_path : [];
        const categoryName = selectedPath.length > 0
          ? selectedPath[selectedPath.length - 1]?.name
          : (item.title || 'Kategori');

        localStorage.setItem('ilan_ver_listing_id', String(item.id || id));
        localStorage.setItem('ilan_ver_module', String(item.module || 'vehicle'));
        localStorage.setItem('ilan_ver_category', JSON.stringify({
          id: item.category_id,
          name: categoryName,
          module: item.module || 'vehicle',
        }));
        localStorage.setItem('ilan_ver_category_path', JSON.stringify(selectedPath));
        localStorage.setItem('ilan_ver_vehicle_selection', JSON.stringify(item.vehicle || {}));

        const detailMap = {};
        (item.detail_groups || []).forEach((group) => {
          if (!group?.id) return;
          detailMap[group.id] = Array.isArray(group.selected) ? group.selected : [];
        });

        const preloadForm = {
          title: item?.core_fields?.title || item?.title || '',
          description: item?.core_fields?.description || item?.description || '',
          price: item?.price?.amount || item?.price_amount || '',
          city: item?.location?.city || '',
          address_country: (item?.location?.country || localStorage.getItem('selected_country') || 'DE').toUpperCase(),
          postal_code: item?.location?.postal_code || '',
          district: item?.location?.district || '',
          neighborhood: item?.location?.neighborhood || '',
          latitude: item?.location?.latitude ?? '',
          longitude: item?.location?.longitude ?? '',
          address_line: item?.location?.address_line || '',
          contact_name: item?.contact?.contact_name || '',
          contact_phone: item?.contact?.contact_phone || '',
          allow_phone: item?.contact?.allow_phone !== false,
          allow_message: item?.contact?.allow_message !== false,
          dynamic_values: item?.attributes || {},
          detail_values: detailMap,
          video_url: item?.modules?.video_url || '',
          duration_key: item?.payment_options?.listing_duration_key || '',
          duration_days: Number(item?.payment_options?.listing_duration_days || 0),
          duration_price_eur: Number(item?.payment_options?.listing_duration_price_eur || 0),
          duration_old_price_eur: Number(item?.payment_options?.listing_duration_old_price_eur || 0),
          accepted_terms: false,
        };
        localStorage.setItem(FORM_STORAGE_KEY, JSON.stringify(preloadForm));

        if (alive) navigate('/ilan-ver/detaylar?mode=edit', { replace: true });
      } catch (err) {
        if (alive) setError(err.message || 'İlan düzenleme başlatılamadı');
      }
    };

    bootstrap();
    return () => {
      alive = false;
    };
  }, [id, navigate]);

  if (error) {
    return <div className="p-6 text-sm text-rose-600" data-testid="listing-edit-entry-error">{error}</div>;
  }
  return <div className="p-6 text-sm text-slate-600" data-testid="listing-edit-entry-loading">İlan düzenleme yükleniyor...</div>;
}
