import React, { useEffect, useMemo, useState } from 'react';
import axios from 'axios';
import SiteFooter from '@/components/public/SiteFooter';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const createColumn = (type = 'text') => {
  if (type === 'link_group') {
    return { type, title: '', links: [] };
  }
  if (type === 'social') {
    return { type, title: '', links: [] };
  }
  return { type: 'text', title: '', text: { tr: '', de: '', fr: '' } };
};

const createRow = (count = 1) => ({
  columns: Array.from({ length: count }, () => createColumn('text')),
});

export default function AdminFooterManagement() {
  const [layout, setLayout] = useState({ rows: [] });
  const [versions, setVersions] = useState([]);
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const authHeader = { Authorization: `Bearer ${localStorage.getItem('access_token')}` };

  const fetchLayout = async () => {
    const res = await axios.get(`${API}/admin/footer/layout`, { headers: authHeader });
    if (res.data?.layout) {
      setLayout(res.data.layout);
    } else {
      setLayout({ rows: [] });
    }
  };

  const fetchVersions = async () => {
    const res = await axios.get(`${API}/admin/footer/layouts`, { headers: authHeader });
    setVersions(res.data?.items || []);
  };

  useEffect(() => {
    fetchLayout();
    fetchVersions();
  }, []);

  const addRow = () => {
    setLayout((prev) => ({
      ...prev,
      rows: [...(prev.rows || []), createRow(1)],
    }));
  };

  const removeRow = (rowIndex) => {
    setLayout((prev) => ({
      ...prev,
      rows: (prev.rows || []).filter((_, idx) => idx !== rowIndex),
    }));
  };

  const updateColumnCount = (rowIndex, count) => {
    setLayout((prev) => {
      const rows = [...(prev.rows || [])];
      const row = rows[rowIndex] || createRow(count);
      const currentCols = row.columns || [];
      if (count > currentCols.length) {
        const extra = Array.from({ length: count - currentCols.length }, () => createColumn('text'));
        row.columns = [...currentCols, ...extra];
      } else {
        row.columns = currentCols.slice(0, count);
      }
      rows[rowIndex] = row;
      return { ...prev, rows };
    });
  };

  const updateColumn = (rowIndex, colIndex, updater) => {
    setLayout((prev) => {
      const rows = [...(prev.rows || [])];
      const row = rows[rowIndex] || createRow(1);
      const columns = [...(row.columns || [])];
      const column = { ...(columns[colIndex] || createColumn('text')) };
      columns[colIndex] = updater(column);
      row.columns = columns;
      rows[rowIndex] = row;
      return { ...prev, rows };
    });
  };

  const addLink = (rowIndex, colIndex) => {
    updateColumn(rowIndex, colIndex, (column) => {
      const links = Array.isArray(column.links) ? column.links : [];
      return { ...column, links: [...links, { label: '', target: '', type: column.type === 'link_group' ? 'info' : 'external' }] };
    });
  };

  const updateLink = (rowIndex, colIndex, linkIndex, field, value) => {
    updateColumn(rowIndex, colIndex, (column) => {
      const links = Array.isArray(column.links) ? [...column.links] : [];
      const link = { ...(links[linkIndex] || { label: '', target: '', type: 'info' }) };
      link[field] = value;
      links[linkIndex] = link;
      return { ...column, links };
    });
  };

  const removeLink = (rowIndex, colIndex, linkIndex) => {
    updateColumn(rowIndex, colIndex, (column) => {
      const links = Array.isArray(column.links) ? column.links.filter((_, idx) => idx !== linkIndex) : [];
      return { ...column, links };
    });
  };

  const saveLayout = async (statusValue = 'draft') => {
    setSaving(true);
    setStatus('');
    setError('');
    try {
      const res = await axios.put(
        `${API}/admin/footer/layout`,
        { layout, status: statusValue },
        { headers: authHeader }
      );
      setStatus(`Kaydedildi (v${res.data?.version || '-'})`);
      await fetchVersions();
      return res.data;
    } catch (err) {
      setError(err?.response?.data?.detail || 'Kaydetme başarısız');
      return null;
    } finally {
      setSaving(false);
    }
  };

  const publishLayout = async () => {
    const saved = await saveLayout('draft');
    if (!saved?.id) return;
    try {
      await axios.post(`${API}/admin/footer/layout/${saved.id}/publish`, {}, { headers: authHeader });
      setStatus(`Yayınlandı (v${saved.version || '-'})`);
      await fetchVersions();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Yayınlama başarısız');
    }
  };

  const publishVersion = async (id) => {
    try {
      await axios.post(`${API}/admin/footer/layout/${id}/publish`, {}, { headers: authHeader });
      setStatus('Rollback yayınlandı');
      await fetchVersions();
    } catch (err) {
      setError(err?.response?.data?.detail || 'Rollback başarısız');
    }
  };

  const loadVersion = async (id) => {
    try {
      const res = await axios.get(`${API}/admin/footer/layout/${id}`, { headers: authHeader });
      setLayout(res.data?.layout || { rows: [] });
      setStatus(`Versiyon yüklendi (v${res.data?.version || '-'})`);
    } catch (err) {
      setError(err?.response?.data?.detail || 'Versiyon yükleme başarısız');
    }
  };

  const rows = layout?.rows || [];

  const previewLayout = useMemo(() => layout, [layout]);

  return (
    <div className="space-y-6" data-testid="admin-footer-management">
      <div>
        <h1 className="text-2xl font-semibold" data-testid="admin-footer-title">Footer Yönetimi</h1>
        <p className="text-sm text-muted-foreground" data-testid="admin-footer-subtitle">
          Footer satır/sütun düzenini oluşturun ve yayınlamadan önce önizleyin.
        </p>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="admin-footer-builder">
        <div className="flex flex-wrap gap-2" data-testid="admin-footer-actions">
          <button
            type="button"
            onClick={addRow}
            className="h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm"
            data-testid="admin-footer-add-row"
          >
            Satır Ekle
          </button>
          <button
            type="button"
            onClick={() => saveLayout('draft')}
            className="h-9 px-4 rounded-md border text-sm"
            data-testid="admin-footer-save-draft"
            disabled={saving}
          >
            Taslağı Kaydet
          </button>
          <button
            type="button"
            onClick={publishLayout}
            className="h-9 px-4 rounded-md bg-emerald-600 text-white text-sm"
            data-testid="admin-footer-publish"
            disabled={saving}
          >
            Yayınla
          </button>
        </div>

        {status && (
          <div className="text-xs text-emerald-600" data-testid="admin-footer-status">{status}</div>
        )}
        {error && (
          <div className="text-xs text-rose-600" data-testid="admin-footer-error">{error}</div>
        )}

        <div className="space-y-6" data-testid="admin-footer-rows">
          {rows.length === 0 && (
            <div className="text-sm text-muted-foreground" data-testid="admin-footer-empty">
              Henüz satır yok. "Satır Ekle" ile başlayın.
            </div>
          )}

          {rows.map((row, rowIndex) => (
            <div key={rowIndex} className="border rounded-lg p-4 space-y-4" data-testid={`admin-footer-row-${rowIndex}`}>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="text-sm font-semibold" data-testid={`admin-footer-row-title-${rowIndex}`}>Satır {rowIndex + 1}</div>
                <div className="flex items-center gap-2">
                  <label className="text-xs">Sütun</label>
                  <select
                    value={row.columns?.length || 1}
                    onChange={(e) => updateColumnCount(rowIndex, Number(e.target.value))}
                    className="h-9 rounded-md border px-2 text-sm"
                    data-testid={`admin-footer-row-columns-${rowIndex}`}
                  >
                    {[1, 2, 3, 4, 5].map((count) => (
                      <option key={count} value={count} label={`${count}`} />
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={() => removeRow(rowIndex)}
                    className="text-xs text-rose-600 underline"
                    data-testid={`admin-footer-row-remove-${rowIndex}`}
                  >
                    Satırı Sil
                  </button>
                </div>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                {(row.columns || []).map((col, colIndex) => (
                  <div key={colIndex} className="border rounded-md p-3 space-y-3" data-testid={`admin-footer-col-${rowIndex}-${colIndex}`}>
                    <div className="flex items-center justify-between">
                      <div className="text-xs font-semibold">Sütun {colIndex + 1}</div>
                      <select
                        value={col.type || 'text'}
                        onChange={(e) => updateColumn(rowIndex, colIndex, () => createColumn(e.target.value))}
                        className="h-8 rounded-md border px-2 text-xs"
                        data-testid={`admin-footer-col-type-${rowIndex}-${colIndex}`}
                      >
                        <option value="text" label="Metin" />
                        <option value="link_group" label="Link Group" />
                        <option value="social" label="Sosyal Link" />
                      </select>
                    </div>

                    <div>
                      <label className="text-xs">Başlık</label>
                      <input
                        className="mt-1 h-9 w-full rounded-md border px-2 text-sm"
                        value={col.title || ''}
                        onChange={(e) => updateColumn(rowIndex, colIndex, (column) => ({ ...column, title: e.target.value }))}
                        data-testid={`admin-footer-col-title-input-${rowIndex}-${colIndex}`}
                      />
                    </div>

                    {col.type === 'text' && (
                      <div className="space-y-2">
                        <div>
                          <label className="text-xs">Metin (TR)</label>
                          <textarea
                            className="mt-1 min-h-[80px] w-full rounded-md border px-2 py-1 text-sm"
                            value={col.text?.tr || ''}
                            onChange={(e) => updateColumn(rowIndex, colIndex, (column) => ({
                              ...column,
                              text: { ...(column.text || {}), tr: e.target.value },
                            }))}
                            data-testid={`admin-footer-col-text-tr-${rowIndex}-${colIndex}`}
                          />
                        </div>
                        <div>
                          <label className="text-xs">Metin (DE)</label>
                          <textarea
                            className="mt-1 min-h-[60px] w-full rounded-md border px-2 py-1 text-sm"
                            value={col.text?.de || ''}
                            onChange={(e) => updateColumn(rowIndex, colIndex, (column) => ({
                              ...column,
                              text: { ...(column.text || {}), de: e.target.value },
                            }))}
                            data-testid={`admin-footer-col-text-de-${rowIndex}-${colIndex}`}
                          />
                        </div>
                        <div>
                          <label className="text-xs">Metin (FR)</label>
                          <textarea
                            className="mt-1 min-h-[60px] w-full rounded-md border px-2 py-1 text-sm"
                            value={col.text?.fr || ''}
                            onChange={(e) => updateColumn(rowIndex, colIndex, (column) => ({
                              ...column,
                              text: { ...(column.text || {}), fr: e.target.value },
                            }))}
                            data-testid={`admin-footer-col-text-fr-${rowIndex}-${colIndex}`}
                          />
                        </div>
                      </div>
                    )}

                    {(col.type === 'link_group' || col.type === 'social') && (
                      <div className="space-y-2" data-testid={`admin-footer-col-links-${rowIndex}-${colIndex}`}>
                        {(col.links || []).map((link, linkIndex) => (
                          <div key={linkIndex} className="grid gap-2 md:grid-cols-3" data-testid={`admin-footer-link-${rowIndex}-${colIndex}-${linkIndex}`}>
                            <input
                              className="h-9 rounded-md border px-2 text-sm"
                              placeholder="Etiket"
                              value={link.label || ''}
                              onChange={(e) => updateLink(rowIndex, colIndex, linkIndex, 'label', e.target.value)}
                              data-testid={`admin-footer-link-label-${rowIndex}-${colIndex}-${linkIndex}`}
                            />
                            <input
                              className="h-9 rounded-md border px-2 text-sm"
                              placeholder={col.type === 'link_group' ? 'Slug veya URL' : 'URL'}
                              value={link.target || ''}
                              onChange={(e) => updateLink(rowIndex, colIndex, linkIndex, 'target', e.target.value)}
                              data-testid={`admin-footer-link-target-${rowIndex}-${colIndex}-${linkIndex}`}
                            />
                            <div className="flex items-center gap-2">
                              {col.type === 'link_group' && (
                                <select
                                  value={link.type || 'info'}
                                  onChange={(e) => updateLink(rowIndex, colIndex, linkIndex, 'type', e.target.value)}
                                  className="h-9 rounded-md border px-2 text-sm"
                                  data-testid={`admin-footer-link-type-${rowIndex}-${colIndex}-${linkIndex}`}
                                >
                                  <option value="info" label="Bilgi" />
                                  <option value="external" label="Harici" />
                                </select>
                              )}
                              <button
                                type="button"
                                className="text-xs text-rose-600 underline"
                                onClick={() => removeLink(rowIndex, colIndex, linkIndex)}
                                data-testid={`admin-footer-link-remove-${rowIndex}-${colIndex}-${linkIndex}`}
                              >
                                Sil
                              </button>
                            </div>
                          </div>
                        ))}
                        <button
                          type="button"
                          onClick={() => addLink(rowIndex, colIndex)}
                          className="text-xs text-primary underline"
                          data-testid={`admin-footer-link-add-${rowIndex}-${colIndex}`}
                        >
                          Link Ekle
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-4" data-testid="admin-footer-preview">
        <div className="text-sm font-semibold">Önizleme (Taslak)</div>
        <SiteFooter layoutOverride={previewLayout} />
      </div>

      <div className="rounded-lg border bg-white p-4 space-y-3" data-testid="admin-footer-versions">
        <div className="text-sm font-semibold">Versiyonlar</div>
        {versions.length === 0 ? (
          <div className="text-xs text-muted-foreground" data-testid="admin-footer-versions-empty">Versiyon bulunamadı.</div>
        ) : (
          <div className="space-y-2">
            {versions.map((item) => (
              <div key={item.id} className="flex flex-wrap items-center justify-between gap-2 border-b pb-2" data-testid={`admin-footer-version-${item.id}`}>
                <div className="text-xs">
                  v{item.version} • {item.status} • {item.updated_at || '-'}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    className="text-xs underline"
                    onClick={() => loadVersion(item.id)}
                    data-testid={`admin-footer-version-load-${item.id}`}
                  >
                    Yükle
                  </button>
                  <button
                    type="button"
                    className="text-xs text-emerald-600 underline"
                    onClick={() => publishVersion(item.id)}
                    data-testid={`admin-footer-version-publish-${item.id}`}
                  >
                    Yayınla
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
