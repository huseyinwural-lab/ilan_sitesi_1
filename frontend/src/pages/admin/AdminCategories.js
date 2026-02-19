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

  const currentStepIndex = WIZARD_STEPS.findIndex((step) => step.id === wizardStep);
  const nextStep = WIZARD_STEPS[currentStepIndex + 1]?.id;
  const prevStep = WIZARD_STEPS[currentStepIndex - 1]?.id;
  const schemaStatusLabel = schema.status === "published" ? "Yayında" : "Taslak";

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
      country_code: selectedCountry || "",
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
    setWizardStep("core");
    setHierarchyComplete(item.hierarchy_complete ?? true);
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
    setModalOpen(true);
  };

  const handleCreate = () => {
    resetForm();
    setWizardStep("hierarchy");
    setHierarchyComplete(false);
    setModalOpen(true);
  };

  const handleSave = async (status = "draft") => {
    setHierarchyError("");
    if (!hierarchyComplete) {
      setHierarchyError("Önce kategori hiyerarşisini tamamlayın.");
      return;
    }
    const payload = {
      ...form,
      sort_order: Number(form.sort_order || 0),
      hierarchy_complete: true,
      form_schema: { ...schema, status },
    };
    if (!payload.name || !payload.slug) {
      setHierarchyError("Kategori adı ve slug zorunludur.");
      return;
    }
    const url = editing
      ? `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${editing.id}`
      : `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories`;
    const method = editing ? "PATCH" : "POST";
    const res = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...authHeader,
      },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setHierarchyError(data?.detail || "Kaydetme sırasında hata oluştu.");
      return;
    }
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

  const canAccessStep = (stepId) => {
    if (stepId === "hierarchy") return true;
    return hierarchyComplete;
  };

  const addSubcategory = () => {
    setSubcategories((prev) => ([
      ...prev,
      { name: "", slug: "", active_flag: true, sort_order: 0 },
    ]));
  };

  const updateSubcategory = (index, patch) => {
    setSubcategories((prev) => {
      const updated = [...prev];
      updated[index] = { ...updated[index], ...patch };
      return updated;
    });
  };

  const removeSubcategory = (index) => {
    setSubcategories((prev) => prev.filter((_, i) => i !== index));
  };

  const handleHierarchyComplete = async () => {
    setHierarchyError("");

    const name = form.name.trim();
    const slug = form.slug.trim().toLowerCase();
    const country = (form.country_code || "").trim().toUpperCase();

    if (!name || !slug) {
      setHierarchyError("Ana kategori adı ve slug zorunludur.");
      return;
    }
    if (!country) {
      setHierarchyError("Ülke (country) zorunludur.");
      return;
    }

    const cleanedSubs = subcategories
      .map((item) => ({
        ...item,
        name: item.name.trim(),
        slug: item.slug.trim().toLowerCase(),
      }))
      .filter((item) => item.name || item.slug);

    const invalidSub = cleanedSubs.find((item) => !item.name || !item.slug);
    if (invalidSub) {
      setHierarchyError("Alt kategorilerde ad + slug zorunludur.");
      return;
    }

    if (editing) {
      setHierarchyComplete(true);
      setWizardStep("core");
      return;
    }

    try {
      const parentPayload = {
        name,
        slug,
        country_code: country,
        active_flag: form.active_flag,
        sort_order: Number(form.sort_order || 0),
        hierarchy_complete: false,
      };
      const parentRes = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeader,
        },
        body: JSON.stringify(parentPayload),
      });
      const parentData = await parentRes.json();
      if (!parentRes.ok) {
        setHierarchyError(parentData?.detail || "Ana kategori oluşturulamadı.");
        return;
      }
      const parent = parentData.category;

      for (const child of cleanedSubs) {
        const childPayload = {
          name: child.name,
          slug: child.slug,
          parent_id: parent.id,
          country_code: country,
          active_flag: child.active_flag,
          sort_order: Number(child.sort_order || 0),
          hierarchy_complete: true,
        };
        const childRes = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...authHeader,
          },
          body: JSON.stringify(childPayload),
        });
        if (!childRes.ok) {
          const childData = await childRes.json();
          setHierarchyError(childData?.detail || "Alt kategori oluşturulamadı.");
          return;
        }
      }

      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${parent.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...authHeader,
        },
        body: JSON.stringify({ hierarchy_complete: true }),
      });

      setEditing(parent);
      setForm({
        name: parent.name || name,
        slug: parent.slug || slug,
        parent_id: parent.parent_id || "",
        country_code: parent.country_code || country,
        active_flag: parent.active_flag ?? true,
        sort_order: parent.sort_order || 0,
      });
      setHierarchyComplete(true);
      setWizardStep("core");
      fetchItems();
    } catch (error) {
      setHierarchyError("Hiyerarşi oluşturulurken hata oluştu.");
    }
  };

  const handleDynamicNext = () => {
    setDynamicError("");
    const label = dynamicDraft.label.trim();
    const key = dynamicDraft.key.trim();
    const type = dynamicDraft.type;
    if (!label || !key) {
      setDynamicError("Etiket ve key zorunludur.");
      return;
    }
    const options = (dynamicDraft.optionsInput || "")
      .split(",")
      .map((opt) => opt.trim())
      .filter(Boolean);
    if ((type === "select" || type === "radio") && options.length === 0) {
      setDynamicError("Select/Radio için seçenek listesi zorunludur.");
      return;
    }
    const messages = { ...dynamicDraft.messages };
    if (!dynamicDraft.required) {
      messages.required = "";
    }
    const payload = {
      id: dynamicDraft.id || createId("field"),
      label,
      key,
      type,
      options: type === "select" || type === "radio" ? options : [],
      required: dynamicDraft.required,
      sort_order: Number(dynamicDraft.sort_order || 0),
      messages,
    };
    setSchema((prev) => {
      const updated = [...prev.dynamic_fields];
      if (dynamicEditIndex !== null) {
        updated[dynamicEditIndex] = payload;
      } else {
        updated.push(payload);
      }
      return { ...prev, dynamic_fields: updated };
    });
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
  };

  const handleDynamicEdit = (index) => {
    const field = schema.dynamic_fields[index];
    setDynamicEditIndex(index);
    setDynamicDraft({
      id: field.id,
      label: field.label || "",
      key: field.key || "",
      type: field.type || "select",
      required: field.required || false,
      sort_order: field.sort_order || 0,
      optionsInput: (field.options || []).join(", "),
      messages: { required: field.messages?.required || "", invalid: field.messages?.invalid || "" },
    });
    setDynamicError("");
  };

  const handleDynamicRemove = (index) => {
    setSchema((prev) => ({
      ...prev,
      dynamic_fields: prev.dynamic_fields.filter((_, i) => i !== index),
    }));
  };

  const handleDetailOptionAdd = () => {
    const value = detailOptionInput.trim();
    if (!value) return;
    setDetailOptions((prev) => [...prev, value]);
    setDetailOptionInput("");
  };

  const handleDetailNext = () => {
    setDetailError("");
    const title = detailDraft.title.trim();
    const id = detailDraft.id.trim();
    if (!title || !id) {
      setDetailError("Grup başlığı ve key zorunludur.");
      return;
    }
    if (detailOptions.length === 0) {
      setDetailError("En az 1 checkbox seçeneği ekleyin.");
      return;
    }
    const messages = { ...detailDraft.messages };
    if (!detailDraft.required) {
      messages.required = "";
    }
    const payload = {
      id,
      title,
      options: detailOptions,
      required: detailDraft.required,
      sort_order: Number(detailDraft.sort_order || 0),
      messages,
    };
    setSchema((prev) => {
      const updated = [...prev.detail_groups];
      if (detailEditIndex !== null) {
        updated[detailEditIndex] = payload;
      } else {
        updated.push(payload);
      }
      return { ...prev, detail_groups: updated };
    });
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
  };

  const handleDetailEdit = (index) => {
    const group = schema.detail_groups[index];
    setDetailEditIndex(index);
    setDetailDraft({
      id: group.id || "",
      title: group.title || "",
      required: group.required || false,
      sort_order: group.sort_order || 0,
      messages: { required: group.messages?.required || "", invalid: group.messages?.invalid || "" },
    });
    setDetailOptions(group.options || []);
    setDetailOptionInput("");
    setDetailError("");
  };

  const handleDetailRemove = (index) => {
    setSchema((prev) => ({
      ...prev,
      detail_groups: prev.detail_groups.filter((_, i) => i !== index),
    }));
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
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap gap-2" data-testid="category-wizard-steps">
                  {WIZARD_STEPS.map((step) => {
                    const active = wizardStep === step.id;
                    const disabled = !canAccessStep(step.id);
                    return (
                      <button
                        key={step.id}
                        type="button"
                        disabled={disabled}
                        onClick={() => !disabled && setWizardStep(step.id)}
                        className={`px-3 py-1 rounded text-xs border ${active ? 'bg-slate-900 text-white' : 'bg-white text-slate-700'} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                        data-testid={`category-step-${step.id}`}
                      >
                        {step.label}
                      </button>
                    );
                  })}
                </div>
                <div
                  className={`text-xs px-2 py-1 rounded ${schema.status === 'published' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}
                  data-testid="schema-status-badge"
                >
                  {schemaStatusLabel}
                </div>
              </div>

              {hierarchyError && (
                <div className="p-3 rounded border border-rose-200 bg-rose-50 text-rose-700 text-sm" data-testid="categories-hierarchy-error">
                  {hierarchyError}
                </div>
              )}

              {wizardStep === "hierarchy" && (
                <div className="space-y-4" data-testid="category-hierarchy-step">
                  <div className="rounded-lg border p-4 space-y-4">
                    <h3 className="text-md font-semibold">Ana Kategori</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <label className={labelClassName}>Ana kategori adı</label>
                        <input
                          className={inputClassName}
                          value={form.name}
                          onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                          data-testid="categories-name-input"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Slug</label>
                        <input
                          className={inputClassName}
                          value={form.slug}
                          onChange={(e) => setForm((prev) => ({ ...prev, slug: e.target.value }))}
                          data-testid="categories-slug-input"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Ülke</label>
                        <input
                          className={inputClassName}
                          value={form.country_code}
                          onChange={(e) => setForm((prev) => ({ ...prev, country_code: e.target.value.toUpperCase() }))}
                          data-testid="categories-country-input"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Sıra</label>
                        <input
                          type="number"
                          min={0}
                          className={inputClassName}
                          value={form.sort_order}
                          onChange={(e) => setForm((prev) => ({ ...prev, sort_order: e.target.value }))}
                          data-testid="categories-sort-input"
                        />
                      </div>
                      <label className="flex items-center gap-2 text-sm text-slate-800" data-testid="categories-active-wrapper">
                        <input
                          type="checkbox"
                          checked={form.active_flag}
                          onChange={(e) => setForm((prev) => ({ ...prev, active_flag: e.target.checked }))}
                          data-testid="categories-active-checkbox"
                        />
                        Aktif
                      </label>
                    </div>
                  </div>

                  {!editing && (
                    <div className="rounded-lg border p-4 space-y-3" data-testid="categories-subcategory-section">
                      <div className="flex items-center justify-between">
                        <h3 className="text-md font-semibold">Alt Kategoriler</h3>
                        <button
                          type="button"
                          className="px-3 py-1 border rounded text-sm"
                          onClick={addSubcategory}
                          data-testid="categories-subcategory-add"
                        >
                          Alt kategori ekle
                        </button>
                      </div>
                      {subcategories.length === 0 ? (
                        <div className="text-sm text-slate-500" data-testid="categories-subcategory-empty">Henüz alt kategori eklenmedi.</div>
                      ) : (
                        <div className="space-y-3">
                          {subcategories.map((sub, index) => (
                            <div key={`sub-${index}`} className="grid grid-cols-1 md:grid-cols-5 gap-2 items-end" data-testid={`categories-subcategory-row-${index}`}>
                              <div className="space-y-1">
                                <label className={labelClassName}>Ad</label>
                                <input
                                  className={inputClassName}
                                  value={sub.name}
                                  onChange={(e) => updateSubcategory(index, { name: e.target.value })}
                                  data-testid={`categories-subcategory-name-${index}`}
                                />
                              </div>
                              <div className="space-y-1">
                                <label className={labelClassName}>Slug</label>
                                <input
                                  className={inputClassName}
                                  value={sub.slug}
                                  onChange={(e) => updateSubcategory(index, { slug: e.target.value })}
                                  data-testid={`categories-subcategory-slug-${index}`}
                                />
                              </div>
                              <div className="space-y-1">
                                <label className={labelClassName}>Sıra</label>
                                <input
                                  type="number"
                                  min={0}
                                  className={inputClassName}
                                  value={sub.sort_order}
                                  onChange={(e) => updateSubcategory(index, { sort_order: e.target.value })}
                                  data-testid={`categories-subcategory-sort-${index}`}
                                />
                              </div>
                              <label className="flex items-center gap-2 text-sm text-slate-800" data-testid={`categories-subcategory-active-${index}`}>
                                <input
                                  type="checkbox"
                                  checked={sub.active_flag}
                                  onChange={(e) => updateSubcategory(index, { active_flag: e.target.checked })}
                                />
                                Aktif
                              </label>
                              <button
                                type="button"
                                className="text-sm text-rose-600 border rounded px-2 py-1"
                                onClick={() => removeSubcategory(index)}
                                data-testid={`categories-subcategory-remove-${index}`}
                              >
                                Sil
                              </button>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {editing && (
                    <div className="rounded-lg border border-dashed p-4 text-sm text-slate-600" data-testid="categories-hierarchy-locked">
                      Mevcut kategori üzerinde hiyerarşi düzenleme devre dışı. Devam ederek form şemasını güncelleyebilirsiniz.
                    </div>
                  )}

                  <div className="text-xs text-slate-500" data-testid="categories-hierarchy-warning">
                    Hiyerarşi tamamlanmadan çekirdek alanlara geçilemez.
                  </div>
                </div>
              )}

              {wizardStep !== "hierarchy" && (
                <>
                  <div className="rounded-lg border p-4 text-sm" data-testid="categories-summary">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      <div>
                        <div className="text-xs text-slate-500">Ana Kategori</div>
                        <div className="font-medium">{form.name || '-'}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">Slug</div>
                        <div className="font-medium">{form.slug || '-'}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">Ülke</div>
                        <div className="font-medium">{form.country_code || '-'}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-500">Durum</div>
                        <div className="font-medium">{form.active_flag ? 'Aktif' : 'Pasif'}</div>
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-slate-500">Sıra: {form.sort_order || 0}</div>
                  </div>

              {wizardStep === "core" && (
                <div className="border-t pt-4 space-y-4" data-testid="categories-core-step">
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
                    min={0}
                    max={200}
                    aria-label="Başlık min"
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
                    min={0}
                    max={200}
                    aria-label="Başlık max"
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
                  {schema.title_uniqueness.enabled && (
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
                  )}
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
                    min={0}
                    max={10000}
                    aria-label="Açıklama min"
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
                    min={0}
                    max={20000}
                    aria-label="Açıklama max"
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
                  {schema.core_fields.price.secondary_enabled && (
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
                  )}
                  <select
                    className={inputClassName}
                    aria-label="Ondalık basamak"
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
                    min={0}
                    aria-label="Min fiyat"
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
                    min={0}
                    aria-label="Max fiyat"
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
                  {schema.title_uniqueness.enabled && (
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
                  )}
                </div>
              </div>

              </div>
              )}

              {wizardStep === "dynamic" && (
                <div className="border-t pt-4 space-y-4" data-testid="categories-dynamic-step">
                  <div className="flex items-center justify-between">
                    <h3 className="text-md font-semibold">Parametre Alanları (2a)</h3>
                    <span className="text-xs text-slate-500">Tek tek ekleme + Next</span>
                  </div>

                  {dynamicError && (
                    <div className="p-2 rounded border border-rose-200 bg-rose-50 text-rose-700 text-sm" data-testid="categories-dynamic-error">
                      {dynamicError}
                    </div>
                  )}

                  <div className="rounded-lg border p-4 space-y-3" data-testid="categories-dynamic-draft">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div className="space-y-1">
                        <label className={labelClassName}>Etiket</label>
                        <input
                          className={inputClassName}
                          value={dynamicDraft.label}
                          onChange={(e) => setDynamicDraft((prev) => ({ ...prev, label: e.target.value }))}
                          data-testid="categories-dynamic-draft-label"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Key</label>
                        <input
                          className={inputClassName}
                          value={dynamicDraft.key}
                          onChange={(e) => setDynamicDraft((prev) => ({ ...prev, key: e.target.value }))}
                          data-testid="categories-dynamic-draft-key"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Tip</label>
                        <select
                          className={selectClassName}
                          value={dynamicDraft.type}
                          onChange={(e) => setDynamicDraft((prev) => ({
                            ...prev,
                            type: e.target.value,
                            optionsInput: ['text', 'number'].includes(e.target.value) ? '' : prev.optionsInput,
                          }))}
                          data-testid="categories-dynamic-draft-type"
                        >
                          <option value="select">Select</option>
                          <option value="radio">Radio</option>
                          <option value="text">Text</option>
                          <option value="number">Number</option>
                        </select>
                      </div>
                    </div>

                    {(dynamicDraft.type === 'select' || dynamicDraft.type === 'radio') && (
                      <div className="space-y-1">
                        <label className={labelClassName}>Seçenekler (virgülle)</label>
                        <input
                          className={inputClassName}
                          value={dynamicDraft.optionsInput}
                          onChange={(e) => setDynamicDraft((prev) => ({ ...prev, optionsInput: e.target.value }))}
                          data-testid="categories-dynamic-draft-options"
                        />
                      </div>
                    )}

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {dynamicDraft.required && (
                        <div className="space-y-1">
                          <label className={labelClassName}>Required mesajı</label>
                          <input
                            className={inputClassName}
                            value={dynamicDraft.messages.required}
                            onChange={(e) => setDynamicDraft((prev) => ({
                              ...prev,
                              messages: { ...prev.messages, required: e.target.value },
                            }))}
                            data-testid="categories-dynamic-draft-required-message"
                          />
                        </div>
                      )}
                      <div className="space-y-1">
                        <label className={labelClassName}>Invalid mesajı</label>
                        <input
                          className={inputClassName}
                          value={dynamicDraft.messages.invalid}
                          onChange={(e) => setDynamicDraft((prev) => ({
                            ...prev,
                            messages: { ...prev.messages, invalid: e.target.value },
                          }))}
                          data-testid="categories-dynamic-draft-invalid-message"
                        />
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-3">
                      <label className="flex items-center gap-2 text-sm text-slate-800" data-testid="categories-dynamic-draft-required">
                        <input
                          type="checkbox"
                          checked={dynamicDraft.required}
                          onChange={(e) => setDynamicDraft((prev) => ({ ...prev, required: e.target.checked }))}
                        />
                        Zorunlu
                      </label>
                      <div className="space-y-1">
                        <label className={labelClassName}>Sıra</label>
                        <input
                          type="number"
                          min={0}
                          className={`${inputClassName} w-32`}
                          value={dynamicDraft.sort_order}
                          onChange={(e) => setDynamicDraft((prev) => ({ ...prev, sort_order: e.target.value }))}
                          data-testid="categories-dynamic-draft-sort"
                        />
                      </div>
                      <button
                        type="button"
                        className="ml-auto px-4 py-2 bg-slate-900 text-white rounded text-sm"
                        onClick={handleDynamicNext}
                        data-testid="categories-dynamic-next"
                      >
                        {dynamicEditIndex !== null ? 'Güncelle' : 'Next'}
                      </button>
                    </div>
                  </div>

                  <div className="space-y-2" data-testid="categories-dynamic-list">
                    {schema.dynamic_fields.length === 0 ? (
                      <div className="text-sm text-slate-500">Henüz parametre alanı eklenmedi.</div>
                    ) : (
                      schema.dynamic_fields.map((field, index) => (
                        <div key={field.id || field.key} className="border rounded p-3 flex flex-wrap items-center gap-3">
                          <div className="flex-1">
                            <div className="font-medium">{field.label} ({field.key})</div>
                            <div className="text-xs text-slate-500">Tip: {field.type} · Sıra: {field.sort_order || 0}</div>
                          </div>
                          <button
                            type="button"
                            className="text-sm px-3 py-1 border rounded"
                            onClick={() => handleDynamicEdit(index)}
                            data-testid={`categories-dynamic-edit-${index}`}
                          >
                            Düzenle
                          </button>
                          <button
                            type="button"
                            className="text-sm px-3 py-1 border rounded text-rose-600"
                            onClick={() => handleDynamicRemove(index)}
                            data-testid={`categories-dynamic-remove-${index}`}
                          >
                            Sil
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {wizardStep === "detail" && (
                <div className="border-t pt-4 space-y-4" data-testid="categories-detail-step">
                  <div className="flex items-center justify-between">
                    <h3 className="text-md font-semibold">Detay Grupları (2c)</h3>
                    <span className="text-xs text-slate-500">Önce grup tanımı → checkbox listesi</span>
                  </div>

                  {detailError && (
                    <div className="p-2 rounded border border-rose-200 bg-rose-50 text-rose-700 text-sm" data-testid="categories-detail-error">
                      {detailError}
                    </div>
                  )}

                  <div className="rounded-lg border p-4 space-y-3" data-testid="categories-detail-draft">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div className="space-y-1">
                        <label className={labelClassName}>Grup başlığı</label>
                        <input
                          className={inputClassName}
                          value={detailDraft.title}
                          onChange={(e) => setDetailDraft((prev) => ({ ...prev, title: e.target.value }))}
                          data-testid="categories-detail-draft-title"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Key (teknik)</label>
                        <input
                          className={inputClassName}
                          value={detailDraft.id}
                          onChange={(e) => setDetailDraft((prev) => ({ ...prev, id: e.target.value }))}
                          data-testid="categories-detail-draft-key"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Sıra</label>
                        <input
                          type="number"
                          min={0}
                          className={inputClassName}
                          value={detailDraft.sort_order}
                          onChange={(e) => setDetailDraft((prev) => ({ ...prev, sort_order: e.target.value }))}
                          data-testid="categories-detail-draft-sort"
                        />
                      </div>
                    </div>

                    <label className="flex items-center gap-2 text-sm text-slate-800" data-testid="categories-detail-draft-required">
                      <input
                        type="checkbox"
                        checked={detailDraft.required}
                        onChange={(e) => setDetailDraft((prev) => ({ ...prev, required: e.target.checked }))}
                      />
                      Zorunlu
                    </label>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {detailDraft.required && (
                        <div className="space-y-1">
                          <label className={labelClassName}>Required mesajı</label>
                          <input
                            className={inputClassName}
                            value={detailDraft.messages.required}
                            onChange={(e) => setDetailDraft((prev) => ({
                              ...prev,
                              messages: { ...prev.messages, required: e.target.value },
                            }))}
                            data-testid="categories-detail-draft-required-message"
                          />
                        </div>
                      )}
                      <div className="space-y-1">
                        <label className={labelClassName}>Invalid mesajı</label>
                        <input
                          className={inputClassName}
                          value={detailDraft.messages.invalid}
                          onChange={(e) => setDetailDraft((prev) => ({
                            ...prev,
                            messages: { ...prev.messages, invalid: e.target.value },
                          }))}
                          data-testid="categories-detail-draft-invalid-message"
                        />
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2 items-end">
                      <div className="flex-1 space-y-1">
                        <label className={labelClassName}>Checkbox seçeneği</label>
                        <input
                          className={inputClassName}
                          value={detailOptionInput}
                          onChange={(e) => setDetailOptionInput(e.target.value)}
                          data-testid="categories-detail-option-input"
                        />
                      </div>
                      <button
                        type="button"
                        className="px-3 py-2 border rounded text-sm"
                        onClick={handleDetailOptionAdd}
                        data-testid="categories-detail-option-add"
                      >
                        Ekle
                      </button>
                    </div>

                    {detailOptions.length > 0 && (
                      <div className="flex flex-wrap gap-2" data-testid="categories-detail-options">
                        {detailOptions.map((opt, index) => (
                          <div key={`${opt}-${index}`} className="flex items-center gap-2 border rounded px-2 py-1 text-xs" data-testid={`categories-detail-option-${index}`}>
                            <span>{opt}</span>
                            <button
                              type="button"
                              className="text-rose-600"
                              onClick={() => setDetailOptions((prev) => prev.filter((_, i) => i !== index))}
                              data-testid={`categories-detail-option-remove-${index}`}
                            >
                              ✕
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    <div className="flex justify-end">
                      <button
                        type="button"
                        className="px-4 py-2 bg-slate-900 text-white rounded text-sm"
                        onClick={handleDetailNext}
                        data-testid="categories-detail-next"
                      >
                        {detailEditIndex !== null ? 'Güncelle' : 'Next grup'}
                      </button>
                    </div>
                  </div>

                  <div className="space-y-2" data-testid="categories-detail-list">
                    {schema.detail_groups.length === 0 ? (
                      <div className="text-sm text-slate-500">Henüz detay grubu eklenmedi.</div>
                    ) : (
                      schema.detail_groups.map((group, index) => (
                        <div key={group.id || group.title} className="border rounded p-3 flex flex-wrap items-center gap-3">
                          <div className="flex-1">
                            <div className="font-medium">{group.title} ({group.id})</div>
                            <div className="text-xs text-slate-500">Seçenek: {group.options?.length || 0} · Sıra: {group.sort_order || 0}</div>
                          </div>
                          <button
                            type="button"
                            className="text-sm px-3 py-1 border rounded"
                            onClick={() => handleDetailEdit(index)}
                            data-testid={`categories-detail-edit-${index}`}
                          >
                            Düzenle
                          </button>
                          <button
                            type="button"
                            className="text-sm px-3 py-1 border rounded text-rose-600"
                            onClick={() => handleDetailRemove(index)}
                            data-testid={`categories-detail-remove-${index}`}
                          >
                            Sil
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}

              {wizardStep === "modules" && (
                <div className="border-t pt-4 space-y-4" data-testid="categories-modules-step">
                  <h3 className="text-md font-semibold">Sabit Modüller</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                    {Object.keys(schema.modules).map((key) => (
                      <div key={key} className="flex items-center justify-between border rounded p-3" data-testid={`categories-module-row-${key}`}>
                        <div>
                          <div className="font-medium">{MODULE_LABELS[key] || key}</div>
                          <div className="text-xs text-slate-500">Key: {key} · Kaynak: schema.modules</div>
                        </div>
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
                      </div>
                    ))}
                  </div>

                  {schema.modules.photos?.enabled && (
                    <div className="space-y-1">
                      <label className={labelClassName}>Foto limit</label>
                      <input
                        type="number"
                        min={1}
                        max={50}
                        className={`${inputClassName} w-48`}
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
                      <div className="text-xs text-slate-500">Önerilen aralık: 1–50</div>
                    </div>
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
              )}
                </>
              )}

            <div className="flex flex-wrap justify-between items-center gap-3 mt-6 pt-4 border-t">
              <button
                className="px-4 py-2 border rounded"
                onClick={() => {
                  setModalOpen(false);
                  resetForm();
                }}
                data-testid="categories-cancel"
              >
                Vazgeç
              </button>
              <div className="flex flex-wrap gap-2">
                {prevStep && (
                  <button
                    className="px-4 py-2 border rounded"
                    onClick={() => setWizardStep(prevStep)}
                    data-testid="categories-step-prev"
                  >
                    Geri
                  </button>
                )}
                {wizardStep === "modules" ? (
                  <>
                    <button
                      className="px-4 py-2 border rounded"
                      onClick={() => handleSave("draft")}
                      data-testid="categories-save-draft"
                    >
                      Taslak Kaydet
                    </button>
                    <button
                      className="px-4 py-2 bg-blue-600 text-white rounded"
                      onClick={() => handleSave("published")}
                      data-testid="categories-publish"
                    >
                      Yayınla
                    </button>
                  </>
                ) : (
                  nextStep && (
                    <button
                      className="px-4 py-2 bg-blue-600 text-white rounded"
                      onClick={() => {
                        if (wizardStep === "hierarchy") {
                          handleHierarchyComplete();
                          return;
                        }
                        setWizardStep(nextStep);
                      }}
                      data-testid="categories-step-next"
                    >
                      {wizardStep === "hierarchy" ? "Tamam" : wizardStep === "dynamic" ? "Bitti" : "Devam"}
                    </button>
                  )
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminCategories;
