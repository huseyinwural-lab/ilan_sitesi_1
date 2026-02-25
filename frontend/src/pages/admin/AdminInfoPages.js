import React, { useEffect, useState } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const emptyForm = {
  slug: '',
  title_tr: '',
  title_de: '',
  title_fr: '',
  content_tr: '',
  content_de: '',
  content_fr: '',
  is_published: false,
};

export default function AdminInfoPages() {
  const [pages, setPages] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewPage, setPreviewPage] = useState(null);

  const authHeader = { Authorization: `Bearer ${localStorage.getItem('access_token')}` };

  const fetchPages = async () => {
    const res = await axios.get(`${API}/admin/info-pages`, { headers: authHeader });
    setPages(res.data?.items || []);
  };

  useEffect(() => {
    fetchPages();
  }, []);

  const openCreate = () => {
    setForm(emptyForm);
    setEditingId(null);
    setStatus('');
    setError('');
    setShowModal(true);
  };

  const openEdit = async (id) => {
    try {
      const res = await axios.get(`${API}/admin/info-pages/${id}`, { headers: authHeader });
      setForm({
        slug: res.data?.slug || '',
        title_tr: res.data?.title_tr || '',
        title_de: res.data?.title_de || '',
        title_fr: res.data?.title_fr || '',
        content_tr: res.data?.content_tr || '',
        content_de: res.data?.content_de || '',
        content_fr: res.data?.content_fr || '',
        is_published: Boolean(res.data?.is_published),
      });
      setEditingId(id);
      setStatus('');
      setError('');
      setShowModal(true);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Sayfa yüklenemedi');
    }
  };

  const handleSave = async () => {
    setStatus('');
    setError('');
    try {
      if (editingId) {
        await axios.patch(`${API}/admin/info-pages/${editingId}`, form, { headers: authHeader });
      } else {
        await axios.post(`${API}/admin/info-pages`, form, { headers: authHeader });
      }
      setStatus('Kaydedildi');
      setShowModal(false);
      fetchPages();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Kaydetme başarısız');
    }
  };

  const openPreview = async (page) => {
    try {
      const res = await axios.get(`${API}/admin/info-pages/${page.id}`, { headers: authHeader });
      setPreviewPage(res.data);
      setPreviewOpen(true);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Önizleme başarısız');
    }
  };

  return (
    <div className="space-y-6" data-testid="admin-info-pages">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="admin-info-pages-title">Bilgi Sayfaları</h1>
          <p className="text-sm text-muted-foreground" data-testid="admin-info-pages-subtitle">
            Bilgi sayfalarını oluşturun, taslakta tutun veya yayınlayın.
          </p>
        </div>
        <button
          type="button"
          onClick={openCreate}
          className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
          data-testid="admin-info-pages-create"
        >
          Yeni Sayfa
        </button>
      </div>

      {error && (
        <div className="text-xs text-rose-600" data-testid="admin-info-pages-error">{error}</div>
      )}
      {status && (
        <div className="text-xs text-emerald-600" data-testid="admin-info-pages-status">{status}</div>
      )}

      <div className="rounded-lg border bg-white p-4" data-testid="admin-info-pages-table">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm" data-testid="admin-info-pages-table-grid">
            <thead>
              <tr className="text-left text-xs text-muted-foreground">
                <th className="py-2 pr-3">Slug</th>
                <th className="py-2 pr-3">Başlık (TR)</th>
                <th className="py-2 pr-3">Durum</th>
                <th className="py-2 pr-3">Güncelleme</th>
                <th className="py-2">Aksiyon</th>
              </tr>
            </thead>
            <tbody>
              {pages.length === 0 && (
                <tr>
                  <td colSpan="5" className="py-6 text-center text-xs text-muted-foreground" data-testid="admin-info-pages-empty">
                    Henüz sayfa yok.
                  </td>
                </tr>
              )}
              {pages.map((page) => (
                <tr key={page.id} className="border-t" data-testid={`admin-info-pages-row-${page.id}`}>
                  <td className="py-3 pr-3" data-testid={`admin-info-pages-slug-${page.id}`}>{page.slug}</td>
                  <td className="py-3 pr-3" data-testid={`admin-info-pages-title-${page.id}`}>{page.title_tr}</td>
                  <td className="py-3 pr-3" data-testid={`admin-info-pages-status-${page.id}`}>
                    {page.is_published ? 'Yayınlı' : 'Taslak'}
                  </td>
                  <td className="py-3 pr-3" data-testid={`admin-info-pages-updated-${page.id}`}>{page.updated_at || '-'}</td>
                  <td className="py-3 flex flex-wrap gap-2">
                    <button
                      type="button"
                      className="text-xs underline"
                      onClick={() => openEdit(page.id)}
                      data-testid={`admin-info-pages-edit-${page.id}`}
                    >
                      Düzenle
                    </button>
                    <button
                      type="button"
                      className="text-xs underline"
                      onClick={() => openPreview(page)}
                      data-testid={`admin-info-pages-preview-${page.id}`}
                    >
                      Önizle
                    </button>
                    {page.is_published && (
                      <a
                        href={`/bilgi/${page.slug}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs underline text-emerald-600"
                        data-testid={`admin-info-pages-live-${page.id}`}
                      >
                        Canlı Gör
                      </a>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" data-testid="admin-info-pages-modal">
          <div className="w-full max-w-2xl rounded-lg bg-white p-5 space-y-4" data-testid="admin-info-pages-modal-card">
            <div className="flex items-center justify-between">
              <div className="text-lg font-semibold" data-testid="admin-info-pages-modal-title">
                {editingId ? 'Sayfa Düzenle' : 'Yeni Sayfa'}
              </div>
              <button
                type="button"
                className="text-sm text-muted-foreground"
                onClick={() => setShowModal(false)}
                data-testid="admin-info-pages-modal-close"
              >
                Kapat
              </button>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-xs">Slug</label>
                <input
                  className="mt-1 h-9 w-full rounded-md border px-2"
                  value={form.slug}
                  onChange={(e) => setForm((prev) => ({ ...prev, slug: e.target.value }))}
                  data-testid="admin-info-pages-slug-input"
                />
              </div>
              <label className="flex items-center gap-2 text-xs" data-testid="admin-info-pages-publish-toggle">
                <input
                  type="checkbox"
                  checked={Boolean(form.is_published)}
                  onChange={(e) => setForm((prev) => ({ ...prev, is_published: e.target.checked }))}
                  data-testid="admin-info-pages-publish-checkbox"
                />
                Yayınla
              </label>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-xs">Başlık (TR)</label>
                <input
                  className="mt-1 h-9 w-full rounded-md border px-2"
                  value={form.title_tr}
                  onChange={(e) => setForm((prev) => ({ ...prev, title_tr: e.target.value }))}
                  data-testid="admin-info-pages-title-tr"
                />
              </div>
              <div>
                <label className="text-xs">Başlık (DE)</label>
                <input
                  className="mt-1 h-9 w-full rounded-md border px-2"
                  value={form.title_de}
                  onChange={(e) => setForm((prev) => ({ ...prev, title_de: e.target.value }))}
                  data-testid="admin-info-pages-title-de"
                />
              </div>
              <div>
                <label className="text-xs">Başlık (FR)</label>
                <input
                  className="mt-1 h-9 w-full rounded-md border px-2"
                  value={form.title_fr}
                  onChange={(e) => setForm((prev) => ({ ...prev, title_fr: e.target.value }))}
                  data-testid="admin-info-pages-title-fr"
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="text-xs">İçerik (TR)</label>
                <textarea
                  className="mt-1 min-h-[120px] w-full rounded-md border px-2 py-1"
                  value={form.content_tr}
                  onChange={(e) => setForm((prev) => ({ ...prev, content_tr: e.target.value }))}
                  data-testid="admin-info-pages-content-tr"
                />
              </div>
              <div>
                <label className="text-xs">İçerik (DE)</label>
                <textarea
                  className="mt-1 min-h-[120px] w-full rounded-md border px-2 py-1"
                  value={form.content_de}
                  onChange={(e) => setForm((prev) => ({ ...prev, content_de: e.target.value }))}
                  data-testid="admin-info-pages-content-de"
                />
              </div>
              <div>
                <label className="text-xs">İçerik (FR)</label>
                <textarea
                  className="mt-1 min-h-[120px] w-full rounded-md border px-2 py-1"
                  value={form.content_fr}
                  onChange={(e) => setForm((prev) => ({ ...prev, content_fr: e.target.value }))}
                  data-testid="admin-info-pages-content-fr"
                />
              </div>
            </div>

            <div className="rounded-md border p-3" data-testid="admin-info-pages-preview">
              <div className="text-xs font-semibold text-muted-foreground">Önizleme (TR)</div>
              <div className="mt-2 text-sm font-semibold" data-testid="admin-info-pages-preview-title">{form.title_tr}</div>
              <div className="mt-1 text-sm text-muted-foreground whitespace-pre-line" data-testid="admin-info-pages-preview-content">
                {form.content_tr}
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={handleSave}
                className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
                data-testid="admin-info-pages-save"
              >
                Kaydet
              </button>
              <button
                type="button"
                onClick={() => setShowModal(false)}
                className="h-9 px-4 rounded-md border text-sm"
                data-testid="admin-info-pages-cancel"
              >
                Vazgeç
              </button>
            </div>
          </div>
        </div>
      )}

      {previewOpen && previewPage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" data-testid="admin-info-pages-preview-modal">
          <div className="w-full max-w-lg rounded-lg bg-white p-5 space-y-3" data-testid="admin-info-pages-preview-card">
            <div className="flex items-center justify-between">
              <div className="text-lg font-semibold">Önizleme</div>
              <button
                type="button"
                className="text-sm text-muted-foreground"
                onClick={() => setPreviewOpen(false)}
                data-testid="admin-info-pages-preview-close"
              >
                Kapat
              </button>
            </div>
            <div className="text-sm text-muted-foreground" data-testid="admin-info-pages-preview-slug">/{previewPage.slug}</div>
            <div className="text-lg font-semibold" data-testid="admin-info-pages-preview-title-text">{previewPage.title_tr}</div>
            <div className="text-sm text-muted-foreground whitespace-pre-line" data-testid="admin-info-pages-preview-content-text">
              {previewPage.content_tr}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
