import React, { useEffect, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const emptyForm = {
  listing_quota: '',
  price_amount: '',
  currency: 'EUR',
  publish_days: '90',
  start_at: '',
  end_at: '',
  is_active: true,
};

export default function AdminPricingTiers() {
  const scope = 'individual';
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);

  const authHeader = { Authorization: `Bearer ${localStorage.getItem('access_token')}` };

  const fetchItems = async () => {
    const res = await axios.get(`${API}/admin/pricing/campaign-items`, {
      params: { scope },
      headers: authHeader,
    });
    setItems(res.data?.items || []);
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const openCreate = () => {
    setForm(emptyForm);
    setEditingId(null);
    setStatus('');
    setError('');
    setShowModal(true);
  };

  const openEdit = (item) => {
    setForm({
      listing_quota: item.listing_quota ?? '',
      price_amount: item.price_amount ?? '',
      currency: item.currency || 'EUR',
      publish_days: item.publish_days ?? '90',
      start_at: item.start_at ? item.start_at.slice(0, 16) : '',
      end_at: item.end_at ? item.end_at.slice(0, 16) : '',
      is_active: Boolean(item.is_active),
    });
    setEditingId(item.id);
    setStatus('');
    setError('');
    setShowModal(true);
  };

  const handleSave = async () => {
    setStatus('');
    setError('');
    const payload = {
      scope,
      listing_quota: Number(form.listing_quota),
      price_amount: Number(form.price_amount || 0),
      currency: (form.currency || 'EUR').toUpperCase(),
      publish_days: Number(form.publish_days || 90),
      start_at: form.start_at || null,
      end_at: form.end_at || null,
      is_active: Boolean(form.is_active),
    };

    try {
      if (editingId) {
        const updatePayload = { ...payload };
        delete updatePayload.scope;
        await axios.put(`${API}/admin/pricing/campaign-items/${editingId}`, updatePayload, {
          headers: authHeader,
        });
      } else {
        await axios.post(`${API}/admin/pricing/campaign-items`, payload, { headers: authHeader });
      }
      setStatus('Kaydedildi');
      setShowModal(false);
      fetchItems();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Kaydetme başarısız');
    }
  };

  const toggleStatus = async (item) => {
    setStatus('');
    setError('');
    try {
      await axios.patch(
        `${API}/admin/pricing/campaign-items/${item.id}/status`,
        { is_active: !item.is_active },
        { headers: authHeader }
      );
      fetchItems();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Güncelleme başarısız');
    }
  };

  const deleteItem = async (item) => {
    setStatus('');
    setError('');
    if (!window.confirm('Kampanya silinsin mi?')) return;
    try {
      await axios.delete(`${API}/admin/pricing/campaign-items/${item.id}`, { headers: authHeader });
      fetchItems();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Silme başarısız');
    }
  };

  return (
    <div className="space-y-5" data-testid="admin-pricing-individual-page">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="admin-pricing-individual-title">Bireysel Kampanyalar</h1>
          <p className="text-sm text-muted-foreground" data-testid="admin-pricing-individual-subtitle">
            Bireysel ilan kampanyalarını manuel oluşturun.
          </p>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
          data-testid="admin-pricing-individual-create"
        >
          Kampanya Yap
        </button>
      </div>

      <div className="rounded-lg border bg-white p-4" data-testid="admin-pricing-individual-table">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm" data-testid="admin-pricing-individual-table-grid">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="py-2 pr-3">İlan Adedi</th>
                <th className="py-2 pr-3">Fiyat</th>
                <th className="py-2 pr-3">Süre (gün)</th>
                <th className="py-2 pr-3">Durum</th>
                <th className="py-2">Aksiyon</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 && (
                <tr>
                  <td colSpan="5" className="py-6 text-center text-xs text-muted-foreground" data-testid="admin-pricing-individual-empty">
                    Henüz kampanya yok.
                  </td>
                </tr>
              )}
              {items.map((item) => (
                <tr key={item.id} className="border-t" data-testid={`admin-pricing-individual-row-${item.id}`}>
                  <td className="py-3 pr-3" data-testid={`admin-pricing-individual-quota-${item.id}`}>
                    {item.listing_quota}
                  </td>
                  <td className="py-3 pr-3" data-testid={`admin-pricing-individual-price-${item.id}`}>
                    {item.price_amount} {item.currency}
                  </td>
                  <td className="py-3 pr-3" data-testid={`admin-pricing-individual-days-${item.id}`}>
                    {item.publish_days}
                  </td>
                  <td className="py-3 pr-3" data-testid={`admin-pricing-individual-status-${item.id}`}>
                    {item.is_active ? 'Aktif' : 'Pasif'}
                  </td>
                  <td className="py-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="text-xs underline"
                      onClick={() => openEdit(item)}
                      data-testid={`admin-pricing-individual-edit-${item.id}`}
                    >
                      Düzenle
                    </button>
                    <button
                      type="button"
                      className="text-xs underline"
                      onClick={() => toggleStatus(item)}
                      data-testid={`admin-pricing-individual-toggle-${item.id}`}
                    >
                      {item.is_active ? 'Pasif Yap' : 'Aktif Yap'}
                    </button>
                    <button
                      type="button"
                      className="text-xs text-rose-600 underline"
                      onClick={() => deleteItem(item)}
                      data-testid={`admin-pricing-individual-delete-${item.id}`}
                    >
                      Sil
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {error && (
        <div className="text-xs text-rose-600" data-testid="admin-pricing-individual-error">{error}</div>
      )}
      {status && (
        <div className="text-xs text-emerald-600" data-testid="admin-pricing-individual-status">{status}</div>
      )}

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" data-testid="admin-pricing-individual-modal">
          <div className="w-full max-w-md rounded-lg bg-white p-5 space-y-4" data-testid="admin-pricing-individual-modal-card">
            <div className="flex items-center justify-between">
              <div className="text-lg font-semibold" data-testid="admin-pricing-individual-modal-title">
                {editingId ? 'Kampanya Düzenle' : 'Yeni Kampanya'}
              </div>
              <button
                type="button"
                className="text-sm text-muted-foreground"
                onClick={() => setShowModal(false)}
                data-testid="admin-pricing-individual-modal-close"
              >
                Kapat
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs">İlan Adedi</label>
                <input
                  type="number"
                  className="mt-1 h-9 w-full rounded-md border px-2"
                  value={form.listing_quota}
                  onChange={(e) => setForm((prev) => ({ ...prev, listing_quota: e.target.value }))}
                  data-testid="admin-pricing-individual-modal-quota"
                />
              </div>
              <div>
                <label className="text-xs">Fiyat</label>
                <input
                  type="number"
                  className="mt-1 h-9 w-full rounded-md border px-2"
                  value={form.price_amount}
                  onChange={(e) => setForm((prev) => ({ ...prev, price_amount: e.target.value }))}
                  data-testid="admin-pricing-individual-modal-price"
                />
              </div>
              <div>
                <label className="text-xs">Para Birimi</label>
                <input
                  className="mt-1 h-9 w-full rounded-md border px-2"
                  value={form.currency}
                  onChange={(e) => setForm((prev) => ({ ...prev, currency: e.target.value.toUpperCase() }))}
                  data-testid="admin-pricing-individual-modal-currency"
                />
              </div>
              <div>
                <label className="text-xs">İlan Süresi (gün)</label>
                <input
                  type="number"
                  className="mt-1 h-9 w-full rounded-md border px-2"
                  value={form.publish_days}
                  onChange={(e) => setForm((prev) => ({ ...prev, publish_days: e.target.value }))}
                  data-testid="admin-pricing-individual-modal-days"
                />
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                <div>
                  <label className="text-xs">Başlangıç (opsiyonel)</label>
                  <input
                    type="datetime-local"
                    className="mt-1 h-9 w-full rounded-md border px-2"
                    value={form.start_at}
                    onChange={(e) => setForm((prev) => ({ ...prev, start_at: e.target.value }))}
                    data-testid="admin-pricing-individual-modal-start"
                  />
                </div>
                <div>
                  <label className="text-xs">Bitiş (opsiyonel)</label>
                  <input
                    type="datetime-local"
                    className="mt-1 h-9 w-full rounded-md border px-2"
                    value={form.end_at}
                    onChange={(e) => setForm((prev) => ({ ...prev, end_at: e.target.value }))}
                    data-testid="admin-pricing-individual-modal-end"
                  />
                </div>
              </div>
              <label className="flex items-center gap-2 text-xs" data-testid="admin-pricing-individual-modal-active">
                <input
                  type="checkbox"
                  checked={Boolean(form.is_active)}
                  onChange={(e) => setForm((prev) => ({ ...prev, is_active: e.target.checked }))}
                  data-testid="admin-pricing-individual-modal-active-toggle"
                />
                Aktif
              </label>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleSave}
                className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
                data-testid="admin-pricing-individual-modal-save"
              >
                Kaydet
              </button>
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="h-9 px-4 rounded-md border text-sm"
                data-testid="admin-pricing-individual-modal-cancel"
              >
                Vazgeç
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
