import React, { useEffect, useMemo, useState } from "react";
import { useCountry } from "../../contexts/CountryContext";

const createDefaultSchema = () => ({
  core_fields: {
    title: {
      required: true,
      min: 10,
      max: 120,
      custom_rule: "",
      custom_message: "",
      messages: {
        required: "Başlık zorunludur.",
        min: "Başlık çok kısa.",
        max: "Başlık çok uzun.",
        duplicate: "Bu başlık zaten kullanılıyor.",
      },
      ui: { bold: true, high_contrast: true },
    },
    description: {
      required: true,
      min: 30,
      max: 4000,
      custom_rule: "",
      custom_message: "",
      messages: {
        required: "Açıklama zorunludur.",
        min: "Açıklama çok kısa.",
        max: "Açıklama çok uzun.",
      },
      ui: { min_rows: 6, auto_grow: true, show_counter: true },
    },
    price: {
      required: true,
      currency_primary: "EUR",
      currency_secondary: "CHF",
      secondary_enabled: false,
      decimal_places: 0,
      range: { min: 0, max: null },
      messages: {
        required: "Fiyat zorunludur.",
        numeric: "Fiyat sayısal olmalıdır.",
        range: "Fiyat aralık dışında.",
      },
    },
  },
  dynamic_fields: [],
  detail_groups: [],
  modules: {
    address: { enabled: true },
    photos: { enabled: true, max_uploads: 12 },
    contact: { enabled: true },
    payment: { enabled: true },
  },
  payment_options: { package: true, doping: false },
  module_order: ["core_fields", "dynamic_fields", "address", "detail_groups", "photos", "contact", "payment"],
  title_uniqueness: { enabled: false, scope: "category" },
  status: "draft",
});

const applySchemaDefaults = (incoming) => {
  const base = createDefaultSchema();
  if (!incoming) return base;
  return {
    ...base,
    ...incoming,
    core_fields: {
      ...base.core_fields,
      ...incoming.core_fields,
      title: {
        ...base.core_fields.title,
        ...(incoming.core_fields?.title || {}),
        messages: { ...base.core_fields.title.messages, ...(incoming.core_fields?.title?.messages || {}) },
        ui: { ...base.core_fields.title.ui, ...(incoming.core_fields?.title?.ui || {}) },
      },
      description: {
        ...base.core_fields.description,
        ...(incoming.core_fields?.description || {}),
        messages: { ...base.core_fields.description.messages, ...(incoming.core_fields?.description?.messages || {}) },
        ui: { ...base.core_fields.description.ui, ...(incoming.core_fields?.description?.ui || {}) },
      },
      price: {
        ...base.core_fields.price,
        ...(incoming.core_fields?.price || {}),
        range: { ...base.core_fields.price.range, ...(incoming.core_fields?.price?.range || {}) },
        messages: { ...base.core_fields.price.messages, ...(incoming.core_fields?.price?.messages || {}) },
      },
    },
    modules: {
      ...base.modules,
      ...incoming.modules,
      photos: { ...base.modules.photos, ...(incoming.modules?.photos || {}) },
    },
    payment_options: { ...base.payment_options, ...(incoming.payment_options || {}) },
    module_order: incoming.module_order || base.module_order,
    title_uniqueness: { ...base.title_uniqueness, ...(incoming.title_uniqueness || {}) },
    status: incoming.status || base.status,
    dynamic_fields: incoming.dynamic_fields || base.dynamic_fields,
    detail_groups: incoming.detail_groups || base.detail_groups,
  };
};

const MODULE_LABELS = {
  address: "Adres",
  photos: "Fotoğraflar",
  contact: "İletişim",
  payment: "Ödeme",
};

const WIZARD_STEPS = [
  { id: "hierarchy", label: "Hiyerarşi" },
  { id: "core", label: "Çekirdek Alanlar" },
  { id: "dynamic", label: "Parametre Alanları (2a)" },
  { id: "detail", label: "Detay Grupları (2c)" },
  { id: "modules", label: "Modüller" },
];

const createId = (prefix) => `${prefix}-${Date.now()}-${Math.floor(Math.random() * 10000)}`;

const AdminCategories = () => {
  const { selectedCountry } = useCountry();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({
    name: "",
    slug: "",
    parent_id: "",
    country_code: "",
    active_flag: true,
    sort_order: 0,
  });
  const [schema, setSchema] = useState(createDefaultSchema());
  const [wizardStep, setWizardStep] = useState("hierarchy");
  const [hierarchyComplete, setHierarchyComplete] = useState(false);
  const [hierarchyError, setHierarchyError] = useState("");
  const [subcategories, setSubcategories] = useState([]);
  const [dynamicDraft, setDynamicDraft] = useState({
    label: "",
    key: "",
    type: "select",
    required: false,
    sort_order: 0,
    optionsInput: "",
    messages: { required: "", invalid: "" },
  });
  const [dynamicEditIndex, setDynamicEditIndex] = useState(null);
  const [dynamicError, setDynamicError] = useState("");
  const [detailDraft, setDetailDraft] = useState({
    id: "",
    title: "",
    required: false,
    sort_order: 0,
    messages: { required: "", invalid: "" },
  });
  const [detailOptions, setDetailOptions] = useState([]);
  const [detailOptionInput, setDetailOptionInput] = useState("");
  const [detailEditIndex, setDetailEditIndex] = useState(null);
  const [detailError, setDetailError] = useState("");
  const inputClassName = "w-full border rounded p-2 text-slate-900 placeholder-slate-600 disabled:text-slate-500 disabled:bg-slate-100";
  const selectClassName = "w-full border rounded p-2 text-slate-900 disabled:text-slate-500 disabled:bg-slate-100";
  const labelClassName = "text-sm text-slate-800";

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const fetchItems = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories?country=${selectedCountry}`, {
        headers: authHeader,
      });
      const data = await res.json();
      setItems(data.items || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, [selectedCountry]);

  const parentOptions = useMemo(() => items.filter((item) => item.id !== editing?.id), [items, editing]);

  const resetForm = () => {
    setForm({
      name: "",
      slug: "",
      parent_id: "",
      country_code: "",
      active_flag: true,
      sort_order: 0,
    });
    setSchema(createDefaultSchema());
    setEditing(null);
    setWizardStep("hierarchy");
    setHierarchyComplete(false);
    setHierarchyError("");
    setSubcategories([]);
    setDynamicDraft({
      label: "",
      key: "",
      type: "select",
      required: false,
      sort_order: 0,
      optionsInput: "",
      messages: { required: "", invalid: "" },
    });
    setDynamicEditIndex(null);
    setDynamicError("");
    setDetailDraft({
      id: "",
      title: "",
      required: false,
      sort_order: 0,
      messages: { required: "", invalid: "" },
    });
    setDetailOptions([]);
    setDetailOptionInput("");
    setDetailEditIndex(null);
    setDetailError("");
  };

  const handleEdit = (item) => {
    setEditing(item);
    setForm({
      name: item.name || "",
      slug: item.slug || "",
      parent_id: item.parent_id || "",
      country_code: item.country_code || "",
      active_flag: item.active_flag ?? true,
      sort_order: item.sort_order || 0,
    });
    setSchema(applySchemaDefaults(item.form_schema));
    setModalOpen(true);
  };

  const handleCreate = () => {
    resetForm();
    setModalOpen(true);
  };

  const handleSave = async () => {
    const payload = {
      ...form,
      sort_order: Number(form.sort_order || 0),
      form_schema: schema,
    };
    if (!payload.name || !payload.slug) {
      return;
    }
    const url = editing
      ? `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${editing.id}`
      : `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories`;
    const method = editing ? "PATCH" : "POST";
    await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...authHeader,
      },
      body: JSON.stringify(payload),
    });
    setModalOpen(false);
    resetForm();
    fetchItems();
  };

  const handleToggle = async (item) => {
    await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${item.id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        ...authHeader,
      },
      body: JSON.stringify({ active_flag: !item.active_flag }),
    });
    fetchItems();
  };

  const handleDelete = async (item) => {
    await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${item.id}`, {
      method: "DELETE",
      headers: {
        ...authHeader,
      },
    });
    fetchItems();
  };

  const updateDynamicField = (index, patch) => {
    setSchema((prev) => {
      const updated = [...prev.dynamic_fields];
      updated[index] = { ...updated[index], ...patch };
      return { ...prev, dynamic_fields: updated };
    });
  };

  const updateDetailGroup = (index, patch) => {
    setSchema((prev) => {
      const updated = [...prev.detail_groups];
      updated[index] = { ...updated[index], ...patch };
      return { ...prev, detail_groups: updated };
    });
  };

  return (
    <div className="p-6" data-testid="categories-page">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-semibold">Kategoriler</h1>
          <p className="text-sm text-gray-500">İlan form şablonlarını yönetin.</p>
        </div>
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded"
          onClick={handleCreate}
          data-testid="categories-create-open"
        >
          Yeni Kategori
        </button>
      </div>

      <div className="bg-white border rounded-lg">
        <div className="grid grid-cols-6 text-xs font-semibold uppercase px-4 py-2 border-b bg-gray-50">
          <div>Ad</div>
          <div>Slug</div>
          <div>Ülke</div>
          <div>Sıra</div>
          <div>Durum</div>
          <div className="text-right">Aksiyon</div>
        </div>
        {loading ? (
          <div className="p-4 text-sm" data-testid="categories-loading">Yükleniyor...</div>
        ) : items.length === 0 ? (
          <div className="p-4 text-sm" data-testid="categories-empty">Kayıt yok.</div>
        ) : (
          items.map((item) => (
            <div key={item.id} className="grid grid-cols-6 px-4 py-3 border-b text-sm items-center">
              <div className="font-medium">{item.name}</div>
              <div className="text-gray-600">{item.slug}</div>
              <div className="text-gray-600">{item.country_code || "global"}</div>
              <div>{item.sort_order}</div>
              <div>
                <span className={`px-2 py-1 rounded text-xs ${item.active_flag ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-600"}`}>
                  {item.active_flag ? "Aktif" : "Pasif"}
                </span>
              </div>
              <div className="flex justify-end gap-2">
                <button className="text-sm px-3 py-1 border rounded" onClick={() => handleEdit(item)} data-testid={`categories-edit-${item.id}`}>
                  Düzenle
                </button>
                <button className="text-sm px-3 py-1 border rounded" onClick={() => handleToggle(item)} data-testid={`categories-toggle-${item.id}`}>
                  {item.active_flag ? "Pasif Et" : "Aktif Et"}
                </button>
                <button className="text-sm px-3 py-1 border rounded" onClick={() => handleDelete(item)} data-testid={`categories-delete-${item.id}`}>
                  Sil
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {modalOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50" data-testid="categories-modal">
          <div className="bg-white p-6 rounded-lg w-full max-w-4xl max-h-[80vh] overflow-y-auto text-slate-900">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{editing ? "Kategori Düzenle" : "Yeni Kategori"}</h2>
              <button onClick={() => setModalOpen(false)} data-testid="categories-modal-close">✕</button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <input
                  className={inputClassName}
                  placeholder="Kategori adı"
                  value={form.name}
                  onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                  data-testid="categories-name-input"
                />
                <input
                  className={inputClassName}
                  placeholder="Slug"
                  value={form.slug}
                  onChange={(e) => setForm((prev) => ({ ...prev, slug: e.target.value }))}
                  data-testid="categories-slug-input"
                />
                <select
                  className={selectClassName}
                  value={form.parent_id}
                  onChange={(e) => setForm((prev) => ({ ...prev, parent_id: e.target.value }))}
                  data-testid="categories-parent-select"
                >
                  <option value="">Parent (optional)</option>
                  {parentOptions.map((cat) => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
                <input
                  className={inputClassName}
                  placeholder="Country code (optional)"
                  value={form.country_code}
                  onChange={(e) => setForm((prev) => ({ ...prev, country_code: e.target.value.toUpperCase() }))}
                  data-testid="categories-country-input"
                />
                <input
                  type="number"
                  className={inputClassName}
                  placeholder="Sort order"
                  value={form.sort_order}
                  onChange={(e) => setForm((prev) => ({ ...prev, sort_order: e.target.value }))}
                  data-testid="categories-sort-input"
                />
                <label className="flex items-center gap-2 text-sm text-slate-800">
                  <input
                    type="checkbox"
                    checked={form.active_flag}
                    onChange={(e) => setForm((prev) => ({ ...prev, active_flag: e.target.checked }))}
                    data-testid="categories-active-checkbox"
                  />
                  Aktif
                </label>
              </div>

              <div className="border-t pt-4 space-y-4">
                <h3 className="text-md font-semibold">Çekirdek Alanlar</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <label className="flex items-center gap-2 text-sm text-slate-800">
                    <input
                      type="checkbox"
                      checked={schema.core_fields.title.required}
                      onChange={(e) => setSchema((prev) => ({
                        ...prev,
                        core_fields: {
                          ...prev.core_fields,
                          title: { ...prev.core_fields.title, required: e.target.checked },
                        },
                      }))}
                      data-testid="categories-title-required"
                    />
                    Başlık zorunlu
                  </label>
                  <label className="flex items-center gap-2 text-sm text-slate-800">
                    <input
                      type="checkbox"
                      checked={schema.core_fields.description.required}
                      onChange={(e) => setSchema((prev) => ({
                        ...prev,
                        core_fields: {
                          ...prev.core_fields,
                          description: { ...prev.core_fields.description, required: e.target.checked },
                        },
                      }))}
                      data-testid="categories-description-required"
                    />
                    Açıklama zorunlu
                  </label>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <input
                    type="number"
                    className={inputClassName}
                    placeholder="Başlık min"
                    value={schema.core_fields.title.min}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        title: { ...prev.core_fields.title, min: Number(e.target.value) },
                      },
                    }))}
                    data-testid="categories-title-min"
                  />
                  <input
                    type="number"
                    className={inputClassName}
                    placeholder="Başlık max"
                    value={schema.core_fields.title.max}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        title: { ...prev.core_fields.title, max: Number(e.target.value) },
                      },
                    }))}
                    data-testid="categories-title-max"
                  />
                  <input
                    type="text"
                    className={inputClassName}
                    placeholder="Başlık custom rule (regex)"
                    value={schema.core_fields.title.custom_rule}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        title: { ...prev.core_fields.title, custom_rule: e.target.value },
                      },
                    }))}
                    data-testid="categories-title-custom-rule"
                  />
                  <input
                    type="text"
                    className={inputClassName}
                    placeholder="Başlık required mesajı"
                    value={schema.core_fields.title.messages.required}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        title: {
                          ...prev.core_fields.title,
                          messages: { ...prev.core_fields.title.messages, required: e.target.value },
                        },
                      },
                    }))}
                    data-testid="categories-title-required-message"
                  />
                  <input
                    type="text"
                    className={inputClassName}
                    placeholder="Başlık min mesajı"
                    value={schema.core_fields.title.messages.min}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        title: {
                          ...prev.core_fields.title,
                          messages: { ...prev.core_fields.title.messages, min: e.target.value },
                        },
                      },
                    }))}
                    data-testid="categories-title-min-message"
                  />
                  <input
                    type="text"
                    className={inputClassName}
                    placeholder="Başlık max mesajı"
                    value={schema.core_fields.title.messages.max}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        title: {
                          ...prev.core_fields.title,
                          messages: { ...prev.core_fields.title.messages, max: e.target.value },
                        },
                      },
                    }))}
                    data-testid="categories-title-max-message"
                  />
                  <input
                    type="text"
                    className={inputClassName}
                    placeholder="Başlık duplicate mesajı"
                    value={schema.core_fields.title.messages.duplicate}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        title: {
                          ...prev.core_fields.title,
                          messages: { ...prev.core_fields.title.messages, duplicate: e.target.value },
                        },
                      },
                    }))}
                    data-testid="categories-title-duplicate-message"
                  />
                  <input
                    type="text"
                    className={inputClassName}
                    placeholder="Başlık custom mesajı"
                    value={schema.core_fields.title.custom_message}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        title: { ...prev.core_fields.title, custom_message: e.target.value },
                      },
                    }))}
                    data-testid="categories-title-custom-message"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <input
                    type="number"
                    className={inputClassName}
                    placeholder="Açıklama min"
                    value={schema.core_fields.description.min}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        description: { ...prev.core_fields.description, min: Number(e.target.value) },
                      },
                    }))}
                    data-testid="categories-description-min"
                  />
                  <input
                    type="number"
                    className={inputClassName}
                    placeholder="Açıklama max"
                    value={schema.core_fields.description.max}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        description: { ...prev.core_fields.description, max: Number(e.target.value) },
                      },
                    }))}
                    data-testid="categories-description-max"
                  />
                  <input
                    type="text"
                    className={inputClassName}
                    placeholder="Açıklama custom rule (regex)"
                    value={schema.core_fields.description.custom_rule}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        description: { ...prev.core_fields.description, custom_rule: e.target.value },
                      },
                    }))}
                    data-testid="categories-description-custom-rule"
                  />
                  <input
                    type="text"
                    className={inputClassName}
                    placeholder="Açıklama required mesajı"
                    value={schema.core_fields.description.messages.required}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        description: {
                          ...prev.core_fields.description,
                          messages: { ...prev.core_fields.description.messages, required: e.target.value },
                        },
                      },
                    }))}
                    data-testid="categories-description-required-message"
                  />
                  <input
                    type="text"
                    className={inputClassName}
                    placeholder="Açıklama min mesajı"
                    value={schema.core_fields.description.messages.min}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        description: {
                          ...prev.core_fields.description,
                          messages: { ...prev.core_fields.description.messages, min: e.target.value },
                        },
                      },
                    }))}
                    data-testid="categories-description-min-message"
                  />
                  <input
                    type="text"
                    className={inputClassName}
                    placeholder="Açıklama max mesajı"
                    value={schema.core_fields.description.messages.max}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        description: {
                          ...prev.core_fields.description,
                          messages: { ...prev.core_fields.description.messages, max: e.target.value },
                        },
                      },
                    }))}
                    data-testid="categories-description-max-message"
                  />
                  <input
                    type="text"
                    className={inputClassName}
                    placeholder="Açıklama custom mesajı"
                    value={schema.core_fields.description.custom_message}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        description: { ...prev.core_fields.description, custom_message: e.target.value },
                      },
                    }))}
                    data-testid="categories-description-custom-message"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <select
                    className={inputClassName}
                    value={schema.core_fields.price.currency_primary}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        price: { ...prev.core_fields.price, currency_primary: e.target.value },
                      },
                    }))}
                    data-testid="categories-price-primary"
                  >
                    <option value="EUR">EUR</option>
                    <option value="CHF">CHF</option>
                  </select>
                  <select
                    className={inputClassName}
                    value={schema.core_fields.price.currency_secondary}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        price: { ...prev.core_fields.price, currency_secondary: e.target.value },
                      },
                    }))}
                    data-testid="categories-price-secondary"
                  >
                    <option value="CHF">CHF</option>
                    <option value="EUR">EUR</option>
                  </select>
                  <select
                    className={inputClassName}
                    value={schema.core_fields.price.decimal_places}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        price: { ...prev.core_fields.price, decimal_places: Number(e.target.value) },
                      },
                    }))}
                    data-testid="categories-price-decimals"
                  >
                    <option value={0}>0 basamak</option>
                    <option value={2}>2 basamak</option>
                  </select>
                  <input
                    type="number"
                    className={inputClassName}
                    placeholder="Min fiyat"
                    value={schema.core_fields.price.range.min ?? ''}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        price: {
                          ...prev.core_fields.price,
                          range: { ...prev.core_fields.price.range, min: Number(e.target.value) },
                        },
                      },
                    }))}
                    data-testid="categories-price-range-min"
                  />
                  <input
                    type="number"
                    className={inputClassName}
                    placeholder="Max fiyat"
                    value={schema.core_fields.price.range.max ?? ''}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        price: {
                          ...prev.core_fields.price,
                          range: { ...prev.core_fields.price.range, max: e.target.value ? Number(e.target.value) : null },
                        },
                      },
                    }))}
                    data-testid="categories-price-range-max"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  <input
                    type="text"
                    className={inputClassName}
                    placeholder="Fiyat required mesajı"
                    value={schema.core_fields.price.messages.required}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        price: {
                          ...prev.core_fields.price,
                          messages: { ...prev.core_fields.price.messages, required: e.target.value },
                        },
                      },
                    }))}
                    data-testid="categories-price-required-message"
                  />
                  <input
                    type="text"
                    className={inputClassName}
                    placeholder="Fiyat numeric mesajı"
                    value={schema.core_fields.price.messages.numeric}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        price: {
                          ...prev.core_fields.price,
                          messages: { ...prev.core_fields.price.messages, numeric: e.target.value },
                        },
                      },
                    }))}
                    data-testid="categories-price-numeric-message"
                  />
                  <input
                    type="text"
                    className={inputClassName}
                    placeholder="Fiyat range mesajı"
                    value={schema.core_fields.price.messages.range}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        price: {
                          ...prev.core_fields.price,
                          messages: { ...prev.core_fields.price.messages, range: e.target.value },
                        },
                      },
                    }))}
                    data-testid="categories-price-range-message"
                  />
                </div>
                <label className="flex items-center gap-2 text-sm text-slate-800">
                  <input
                    type="checkbox"
                    checked={schema.core_fields.price.secondary_enabled}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      core_fields: {
                        ...prev.core_fields,
                        price: { ...prev.core_fields.price, secondary_enabled: e.target.checked },
                      },
                    }))}
                    data-testid="categories-price-secondary-toggle"
                  />
                  İkincil para birimi göster
                </label>
              </div>

              <div className="border-t pt-4 space-y-4">
                <h3 className="text-md font-semibold">Başlık Benzersizliği</h3>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2 text-sm text-slate-800">
                    <input
                      type="checkbox"
                      checked={schema.title_uniqueness.enabled}
                      onChange={(e) => setSchema((prev) => ({
                        ...prev,
                        title_uniqueness: { ...prev.title_uniqueness, enabled: e.target.checked },
                      }))}
                      data-testid="categories-title-unique-toggle"
                    />
                    Aynı başlıkla ilanı engelle
                  </label>
                  <select
                    className={`${inputClassName} text-sm`}
                    value={schema.title_uniqueness.scope}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      title_uniqueness: { ...prev.title_uniqueness, scope: e.target.value },
                    }))}
                    data-testid="categories-title-unique-scope"
                  >
                    <option value="category">Kategori genelinde</option>
                    <option value="category_user">Kategori + kullanıcı</option>
                  </select>
                </div>
              </div>

              <div className="border-t pt-4 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-md font-semibold">Parametre Alanları (2a)</h3>
                  <button
                    className="px-3 py-1 border rounded"
                    onClick={(e) => {
                      e.preventDefault();
                      setSchema((prev) => ({
                        ...prev,
                        dynamic_fields: [
                          ...prev.dynamic_fields,
                          {
                            id: createId('field'),
                            label: "",
                            key: "",
                            type: "select",
                            options: [],
                            required: false,
                            sort_order: 0,
                            messages: { required: "", invalid: "" },
                          },
                        ],
                      }));
                    }}
                    data-testid="categories-add-dynamic-field"
                  >
                    Alan Ekle
                  </button>
                </div>

                {schema.dynamic_fields.map((field, index) => (
                  <div key={field.id} className="border rounded p-3 space-y-2">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                      <input
                        className={inputClassName}
                        placeholder="Etiket"
                        value={field.label}
                        onChange={(e) => updateDynamicField(index, { label: e.target.value })}
                        data-testid={`categories-dynamic-label-${index}`}
                      />
                      <input
                        className={inputClassName}
                        placeholder="Key"
                        value={field.key}
                        onChange={(e) => updateDynamicField(index, { key: e.target.value })}
                        data-testid={`categories-dynamic-key-${index}`}
                      />
                      <select
                        className={inputClassName}
                        value={field.type}
                        onChange={(e) => updateDynamicField(index, { type: e.target.value })}
                        data-testid={`categories-dynamic-type-${index}`}
                      >
                        <option value="select">Select</option>
                        <option value="radio">Radio</option>
                      </select>
                    </div>
                    <input
                      className={inputClassName}
                      placeholder="Seçenekler (virgülle)"
                      value={(field.options || []).join(', ')}
                      onChange={(e) => updateDynamicField(index, { options: e.target.value.split(',').map((o) => o.trim()).filter(Boolean) })}
                      data-testid={`categories-dynamic-options-${index}`}
                    />
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      <input
                        className={inputClassName}
                        placeholder="Required mesajı"
                        value={field.messages?.required || ''}
                        onChange={(e) => updateDynamicField(index, { messages: { ...field.messages, required: e.target.value } })}
                        data-testid={`categories-dynamic-required-message-${index}`}
                      />
                      <input
                        className={inputClassName}
                        placeholder="Invalid mesajı"
                        value={field.messages?.invalid || ''}
                        onChange={(e) => updateDynamicField(index, { messages: { ...field.messages, invalid: e.target.value } })}
                        data-testid={`categories-dynamic-invalid-message-${index}`}
                      />
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                <label className="flex items-center gap-2 text-slate-800">
                        <input
                          type="checkbox"
                          checked={field.required}
                          onChange={(e) => updateDynamicField(index, { required: e.target.checked })}
                          data-testid={`categories-dynamic-required-${index}`}
                        />
                        Zorunlu
                      </label>
                      <input
                        type="number"
                        className={`${inputClassName} w-32`}
                        placeholder="Sıra"
                        value={field.sort_order}
                        onChange={(e) => updateDynamicField(index, { sort_order: Number(e.target.value) })}
                        data-testid={`categories-dynamic-sort-${index}`}
                      />
                      <button
                        className="ml-auto text-sm text-red-500"
                        onClick={(e) => {
                          e.preventDefault();
                          setSchema((prev) => ({
                            ...prev,
                            dynamic_fields: prev.dynamic_fields.filter((_, i) => i != index),
                          }));
                        }}
                        data-testid={`categories-dynamic-remove-${index}`}
                      >
                        Sil
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              <div className="border-t pt-4 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-md font-semibold">Özel Detay Grupları (2c)</h3>
                  <button
                    className="px-3 py-1 border rounded"
                    onClick={(e) => {
                      e.preventDefault();
                      setSchema((prev) => ({
                        ...prev,
                        detail_groups: [
                          ...prev.detail_groups,
                          {
                            id: createId('group'),
                            title: "",
                            options: [],
                            required: false,
                            sort_order: 0,
                            messages: { required: "", invalid: "" },
                          },
                        ],
                      }));
                    }}
                    data-testid="categories-add-detail-group"
                  >
                    Grup Ekle
                  </button>
                </div>

                {schema.detail_groups.map((group, index) => (
                  <div key={group.id} className="border rounded p-3 space-y-2">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                      <input
                        className={inputClassName}
                        placeholder="Grup başlığı"
                        value={group.title}
                        onChange={(e) => updateDetailGroup(index, { title: e.target.value })}
                        data-testid={`categories-group-title-${index}`}
                      />
                      <input
                        className={inputClassName}
                        placeholder="Seçenekler (virgülle)"
                        value={(group.options || []).join(', ')}
                        onChange={(e) => updateDetailGroup(index, { options: e.target.value.split(',').map((o) => o.trim()).filter(Boolean) })}
                        data-testid={`categories-group-options-${index}`}
                      />
                      <input
                        type="number"
                        className={inputClassName}
                        placeholder="Sıra"
                        value={group.sort_order}
                        onChange={(e) => updateDetailGroup(index, { sort_order: Number(e.target.value) })}
                        data-testid={`categories-group-sort-${index}`}
                      />
                    </div>
                    <label className="flex items-center gap-2 text-sm text-slate-800">
                      <input
                        type="checkbox"
                        checked={group.required}
                        onChange={(e) => updateDetailGroup(index, { required: e.target.checked })}
                        data-testid={`categories-group-required-${index}`}
                      />
                      Zorunlu
                    </label>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      <input
                        className={inputClassName}
                        placeholder="Required mesajı"
                        value={group.messages?.required || ''}
                        onChange={(e) => updateDetailGroup(index, { messages: { ...group.messages, required: e.target.value } })}
                        data-testid={`categories-group-required-message-${index}`}
                      />
                      <input
                        className={inputClassName}
                        placeholder="Invalid mesajı"
                        value={group.messages?.invalid || ''}
                        onChange={(e) => updateDetailGroup(index, { messages: { ...group.messages, invalid: e.target.value } })}
                        data-testid={`categories-group-invalid-message-${index}`}
                      />
                    </div>
                    <button
                      className="text-sm text-red-500"
                      onClick={(e) => {
                        e.preventDefault();
                        setSchema((prev) => ({
                          ...prev,
                          detail_groups: prev.detail_groups.filter((_, i) => i != index),
                        }));
                      }}
                      data-testid={`categories-group-remove-${index}`}
                    >
                      Sil
                    </button>
                  </div>
                ))}
              </div>

              <div className="border-t pt-4 space-y-4">
                <h3 className="text-md font-semibold">Sabit Modüller</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                  {Object.keys(schema.modules).map((key) => (
                    <label key={key} className="flex items-center gap-2 text-slate-800">
                      <input
                        type="checkbox"
                        checked={schema.modules[key].enabled}
                        onChange={(e) => setSchema((prev) => ({
                          ...prev,
                          modules: {
                            ...prev.modules,
                            [key]: { ...prev.modules[key], enabled: e.target.checked },
                          },
                        }))}
                        data-testid={`categories-module-${key}`}
                      />
                      {key}
                    </label>
                  ))}
                </div>
                {schema.modules.photos?.enabled && (
                  <input
                    type="number"
                    className={`${inputClassName} w-48`}
                    placeholder="Fotoğraf limiti"
                    value={schema.modules.photos.max_uploads}
                    onChange={(e) => setSchema((prev) => ({
                      ...prev,
                      modules: {
                        ...prev.modules,
                        photos: { ...prev.modules.photos, max_uploads: Number(e.target.value) },
                      },
                    }))}
                    data-testid="categories-photos-max"
                  />
                )}
                {schema.modules.payment?.enabled && (
                  <div className="flex gap-4 text-sm">
                    <label className="flex items-center gap-2 text-slate-800">
                      <input
                        type="checkbox"
                        checked={schema.payment_options.package}
                        onChange={(e) => setSchema((prev) => ({
                          ...prev,
                          payment_options: { ...prev.payment_options, package: e.target.checked },
                        }))}
                        data-testid="categories-payment-package"
                      />
                      Paket
                    </label>
                    <label className="flex items-center gap-2 text-slate-800">
                      <input
                        type="checkbox"
                        checked={schema.payment_options.doping}
                        onChange={(e) => setSchema((prev) => ({
                          ...prev,
                          payment_options: { ...prev.payment_options, doping: e.target.checked },
                        }))}
                        data-testid="categories-payment-doping"
                      />
                      Doping
                    </label>
                  </div>
                )}
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button className="px-4 py-2 border rounded" onClick={() => setModalOpen(false)} data-testid="categories-cancel">
                Vazgeç
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={handleSave} data-testid="categories-save">
                Kaydet
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminCategories;
