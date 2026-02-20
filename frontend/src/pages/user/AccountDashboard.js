import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { LoadingState, ErrorState } from '@/components/account/AccountStates';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AccountDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [listingTotal, setListingTotal] = useState(0);
  const [favoritesCount, setFavoritesCount] = useState(0);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    let active = true;
    const fetchStats = async () > {
      setLoading(true);
      try {
        const headers = { Authorization: `Bearer ${localStorage.getItem('access_token')}` };
        const [listingsRes, favRes, msgRes] = await Promise.all([
          fetch(`${API}/v1/listings/my?page=1&limit=1`, { headers }),
          fetch(`${API}/v1/favorites/count`, { headers }),
          fetch(`${API}/v1/messages/unread-count`, { headers }),
        ]);
        if (!listingsRes.ok) throw new Error('Liste yüklenemedi');
        const listingsData = await listingsRes.json();
        const favData = favRes.ok ? await favRes.json() : { count: 0 };
        const msgData = msgRes.ok ? await msgRes.json() : { count: 0 };
        if (active) {
          setListingTotal(listingsData.pagination?.total || 0);
          setFavoritesCount(favData.count || 0);
          setUnreadCount(msgData.count || 0);
          setError('');
        }
      } catch (err) {
        if (active) {
          setError('Dashboard verileri alınamadı');
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };
    fetchStats();
    return () => {
      active = false;
    };
  }, []);

  if (loading) {
    return <LoadingState label="Dashboard yükleniyor..." />;
  }

  if (error) {
    return <ErrorState message={error} />;
  }

  return (
    <div className="space-y-6" data-testid="account-dashboard">
      <div className="flex flex-wrap items-center justify-between gap-3" data-testid="account-dashboard-header">
        <div>
          <h1 className="text-2xl font-bold" data-testid="account-dashboard-title">Hoş geldiniz</h1>
          <p className="text-sm text-muted-foreground" data-testid="account-dashboard-subtitle">
            Bireysel portal özetiniz aşağıda.
          </p>
        </div>
        <Link
          to="/account/create/vehicle-wizard"
          className="h-10 px-4 rounded-md bg-primary text-primary-foreground text-sm inline-flex items-center"
          data-testid="account-dashboard-create-listing"
        >
          Yeni İlan Oluştur
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4" data-testid="account-dashboard-cards">
        <div className="rounded-lg border bg-white p-4" data-testid="account-dashboard-card-listings">
          <div className="text-xs text-muted-foreground">Toplam İlan</div>
          <div className="text-2xl font-semibold" data-testid="account-dashboard-listings-count">{listingTotal}</div>
        </div>
        <div className="rounded-lg border bg-white p-4" data-testid="account-dashboard-card-favorites">
          <div className="text-xs text-muted-foreground">Favoriler</div>
          <div className="text-2xl font-semibold" data-testid="account-dashboard-favorites-count">{favoritesCount}</div>
        </div>
        <div className="rounded-lg border bg-white p-4" data-testid="account-dashboard-card-messages">
          <div className="text-xs text-muted-foreground">Okunmamış Mesaj</div>
          <div className="text-2xl font-semibold" data-testid="account-dashboard-unread-count">{unreadCount}</div>
        </div>
      </div>

      <div className="rounded-lg border bg-white p-6" data-testid="account-dashboard-cta">
        <div className="text-lg font-semibold">Sonraki adım</div>
        <p className="text-sm text-muted-foreground mt-1">
          İlan oluşturma sihirbazını tamamlayarak ilanınızı yayına alın.
        </p>
        <Link
          to="/account/create/vehicle-wizard"
          className="mt-4 inline-flex h-10 items-center rounded-md border px-4 text-sm"
          data-testid="account-dashboard-cta-button"
        >
          Sihirbaza Git
        </Link>
      </div>
    </div>
  );
}
