import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useCountry } from "../../contexts/CountryContext";
import { useAuth } from "../../contexts/AuthContext";
import { useToast } from "@/components/ui/toaster";

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
  const fallbackStatus = "published";
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
    status: incoming.status || fallbackStatus,
    dynamic_fields: incoming.dynamic_fields || base.dynamic_fields,
    detail_groups: incoming.detail_groups || base.detail_groups,
  };
};

const MODULE_LABELS = {
  address: "Adres",
  photos: "Fotoğraf",
  contact: "İletişim",
  payment: "Ödeme",
};

const CATEGORY_MODULE_OPTIONS = [
  { value: "real_estate", label: "Emlak" },
  { value: "vehicle", label: "Vasıta" },
  { value: "other", label: "Diğer" },
];

const TRANSACTION_TYPE_OPTIONS = [
  { value: "satilik", label: "Satılık" },
  { value: "kiralik", label: "Kiralık" },
  { value: "gunluk", label: "Günlük Kiralık" },
];

const WIZARD_STEPS = [
  { id: "hierarchy", label: "Kategori" },
  { id: "core", label: "Çekirdek Alanlar" },
  { id: "dynamic", label: "Parametre Alanları (2a)" },
  { id: "detail", label: "Detay Grupları (2c)" },
  { id: "modules", label: "Modüller" },
  { id: "preview", label: "Önizleme" },
];

const WIZARD_PROGRESS_ORDER = [
  "draft",
  "category_completed",
  "core_completed",
  "param_completed",
  "detail_completed",
  "module_completed",
  "ready_for_preview",
];

const STEP_PROGRESS_STATE = {
  hierarchy: "category_completed",
  core: "core_completed",
  dynamic: "param_completed",
  detail: "detail_completed",
  modules: "module_completed",
  preview: "ready_for_preview",
};

const DIRTY_DEPENDENCIES = {
  hierarchy: ["core", "dynamic", "detail", "modules", "preview"],
  core: ["dynamic", "detail", "modules", "preview"],
  dynamic: ["detail", "modules", "preview"],
  detail: ["modules", "preview"],
  modules: ["preview"],
  preview: [],
};

const createId = (prefix) => `${prefix}-${Date.now()}-${Math.floor(Math.random() * 10000)}`;
const createSubcategoryDraft = () => ({
  name: "",
  slug: "",
  active_flag: true,
  sort_order: 1,
  transaction_type: "",
  is_complete: false,
  children: [],
});
const createSubcategoryGroupDraft = () => ({
  ...createSubcategoryDraft(),
  children: [createSubcategoryDraft()],
});

const normalizeSlugValue = (value) => {
  if (!value) return "";
  return String(value)
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/ı/g, "i")
    .replace(/ş/g, "s")
    .replace(/ğ/g, "g")
    .replace(/ç/g, "c")
    .replace(/ö/g, "o")
    .replace(/ü/g, "u")
    .replace(/[^a-z0-9-\s]/g, "")
    .replace(/\s+/g, "-")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
};

const reorderArray = (items, fromIndex, toIndex) => {
  if (!Array.isArray(items)) return [];
  if (fromIndex === toIndex) return [...items];
  const next = [...items];
  const [moved] = next.splice(fromIndex, 1);
  next.splice(toIndex, 0, moved);
  return next;
};

const CATEGORY_IMAGE_MAX_BYTES = 2 * 1024 * 1024;
const CATEGORY_IMAGE_ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "webp"];

const resolveCategoryImagePreviewUrl = (imageUrl, cacheBuster) => {
  if (!imageUrl) return "";
  const separator = imageUrl.includes("?") ? "&" : "?";
  return `${imageUrl}${separator}v=${cacheBuster}`;
};

const TURKISH_CHAR_MAP = {
  ç: "c",
  Ç: "C",
  ğ: "g",
  Ğ: "G",
  ı: "i",
  İ: "I",
  ö: "o",
  Ö: "O",
  ş: "s",
  Ş: "S",
  ü: "u",
  Ü: "U",
};

const sanitizeSchemaStrings = (value) => {
  if (typeof value === "string") {
    return value.replace(/[çÇğĞıİöÖşŞüÜ]/g, (char) => TURKISH_CHAR_MAP[char] || char);
  }
  if (Array.isArray(value)) {
    return value.map((item) => sanitizeSchemaStrings(item));
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, val]) => [key, sanitizeSchemaStrings(val)])
    );
  }
  return value;
};

const parseApiError = (payload, fallbackMessage) => {
  const detail = payload?.detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const firstError = detail[0] || {};
    const location = Array.isArray(firstError.loc) ? firstError.loc.join(".") : "";
    const baseMessage = firstError.msg || firstError.message || fallbackMessage;
    return {
      errorCode: payload?.error_code || "",
      message: location ? `${location}: ${baseMessage}` : baseMessage,
    };
  }
  if (typeof detail === "string") {
    return { errorCode: payload?.error_code || "", message: detail || fallbackMessage };
  }
  if (detail && typeof detail === "object") {
    return {
      errorCode: detail.error_code || payload?.error_code || "",
      message: detail.message || payload?.message || fallbackMessage,
    };
  }
  return {
    errorCode: payload?.error_code || "",
    message: payload?.message || fallbackMessage,
  };
};

const TriStateCheckbox = ({ checked, indeterminate, onChange, disabled, testId }) => {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.indeterminate = Boolean(indeterminate);
    }
  }, [indeterminate]);

  return (
    <input
      ref={ref}
      type="checkbox"
      checked={Boolean(checked)}
      disabled={disabled}
      onChange={onChange}
      data-testid={testId}
    />
  );
};

const AdminCategories = () => {
  const { selectedCountry } = useCountry();
  const { user, hasPermission } = useAuth();
  const [items, setItems] = useState([]);
  const [listFilters, setListFilters] = useState({
    module: "all",
    status: "all",
    image_presence: "all",
  });
  const [selectedIds, setSelectedIds] = useState([]);
  const [bulkRunning, setBulkRunning] = useState(false);
  const [bulkJob, setBulkJob] = useState(null);
  const [bulkJobPolling, setBulkJobPolling] = useState(false);
  const [bulkConfirmOpen, setBulkConfirmOpen] = useState(false);
  const [bulkConfirmValue, setBulkConfirmValue] = useState("");
  const [pendingBulkAction, setPendingBulkAction] = useState("");
  const [loading, setLoading] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({
    name: "",
    slug: "",
    parent_id: "",
    country_code: "",
    module: "",
    active_flag: true,
    sort_order: 1,
    image_url: "",
  });
  const [vehicleSegment, setVehicleSegment] = useState("");
  const [vehicleSegmentError, setVehicleSegmentError] = useState("");
  const [vehicleLinkStatus, setVehicleLinkStatus] = useState({
    checking: false,
    linked: false,
    make_count: 0,
    model_count: 0,
    message: "",
  });
  const [orderPreview, setOrderPreview] = useState({
    checking: false,
    available: true,
    message: "",
    conflict: null,
    suggested_next_sort_order: null,
  });
  const [categoryImageUploading, setCategoryImageUploading] = useState(false);
  const [categoryImageError, setCategoryImageError] = useState("");
  const [categoryImageCacheBuster, setCategoryImageCacheBuster] = useState(Date.now());
  const [schema, setSchema] = useState(createDefaultSchema());
  const [wizardStep, setWizardStep] = useState("hierarchy");
  const [wizardProgress, setWizardProgress] = useState({ state: "draft", dirty_steps: [] });
  const [editModeStep, setEditModeStep] = useState(null);
  const [hierarchyComplete, setHierarchyComplete] = useState(false);
  const [hierarchyError, setHierarchyError] = useState("");
  const [hierarchyFieldErrors, setHierarchyFieldErrors] = useState({});
  const [subcategories, setSubcategories] = useState([createSubcategoryGroupDraft()]);
  const [levelSelections, setLevelSelections] = useState([]);
  const [levelCompletion, setLevelCompletion] = useState({});
  const [draggingGroupIndex, setDraggingGroupIndex] = useState(null);
  const [draggingChild, setDraggingChild] = useState(null);
  const [isModalFullscreen, setIsModalFullscreen] = useState(false);
  const [modalSize, setModalSize] = useState({ width: 1280, height: 820 });
  const [dynamicDraft, setDynamicDraft] = useState({
    label: "",
    key: "",
    type: "select",
    required: false,
    sort_order: 0,
    optionInput: "",
    options: [],
    messages: { required: "", invalid: "" },
  });
  const [dynamicEditIndex, setDynamicEditIndex] = useState(null);
  const [dynamicError, setDynamicError] = useState("");
  const [detailDraft, setDetailDraft] = useState({
    id: "",
    title: "",
    required: false,
    sort_order: 0,
    options: [],
    messages: { required: "", invalid: "" },
  });
  const [detailOptionInput, setDetailOptionInput] = useState("");
  const [detailEditIndex, setDetailEditIndex] = useState(null);
  const [detailError, setDetailError] = useState("");
  const [publishError, setPublishError] = useState("");
  const [previewComplete, setPreviewComplete] = useState(false);
  const [jsonCopyStatus, setJsonCopyStatus] = useState("");
  const [versions, setVersions] = useState([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [versionsError, setVersionsError] = useState("");
  const [selectedVersions, setSelectedVersions] = useState([]);
  const [versionDetails, setVersionDetails] = useState({});
  const [lastSavedAt, setLastSavedAt] = useState("");
  const [autosaveStatus, setAutosaveStatus] = useState("idle");
  const [stepSaving, setStepSaving] = useState(false);
  const autosaveTimeoutRef = useRef(null);
  const autosaveToastRef = useRef(null);
  const lastSavedSnapshotRef = useRef("");

  const { toast } = useToast();
  const effectiveHierarchyComplete = hierarchyComplete;
  const inputClassName = "w-full border rounded p-2 text-slate-900 placeholder-slate-700 disabled:text-slate-700 disabled:bg-slate-100";
  const selectClassName = "w-full border rounded p-2 text-slate-900 disabled:text-slate-700 disabled:bg-slate-100";
  const labelClassName = "text-sm font-semibold text-slate-900";

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const selectedIdSet = useMemo(() => new Set(selectedIds), [selectedIds]);
  const visibleItems = useMemo(() => {
    const rootOnlyItems = items.filter((item) => !item.parent_id);

    if (listFilters.image_presence === "with_image") {
      return rootOnlyItems.filter((item) => Boolean((item.image_url || "").trim()));
    }
    if (listFilters.image_presence === "without_image") {
      return rootOnlyItems.filter((item) => !Boolean((item.image_url || "").trim()));
    }
    return rootOnlyItems;
  }, [items, listFilters.image_presence]);
  const visibleItemIds = useMemo(() => visibleItems.map((item) => item.id), [visibleItems]);
  const allVisibleSelected = useMemo(
    () => visibleItemIds.length > 0 && visibleItemIds.every((id) => selectedIdSet.has(id)),
    [visibleItemIds, selectedIdSet],
  );
  const someVisibleSelected = useMemo(
    () => visibleItemIds.some((id) => selectedIdSet.has(id)),
    [visibleItemIds, selectedIdSet],
  );

  const descendantsByItem = useMemo(() => {
    const childrenByParent = new Map();
    items.forEach((item) => {
      const parentKey = item.parent_id || "__root__";
      if (!childrenByParent.has(parentKey)) {
        childrenByParent.set(parentKey, []);
      }
      childrenByParent.get(parentKey).push(item.id);
    });

    const collectDescendants = (nodeId) => {
      const stack = [nodeId];
      const acc = [];
      while (stack.length > 0) {
        const currentId = stack.pop();
        acc.push(currentId);
        const children = childrenByParent.get(currentId) || [];
        children.forEach((childId) => stack.push(childId));
      }
      return acc;
    };

    const result = new Map();
    visibleItems.forEach((item) => {
      result.set(item.id, collectDescendants(item.id));
    });
    return result;
  }, [visibleItems]);

  const trackAdminWizardEvent = useCallback(async (eventName, details = {}) => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    if (!details.category_id || !details.step_id) return;
    try {
      await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/analytics/events`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          event_name: eventName,
          category_id: details.category_id,
          step_id: details.step_id,
          admin_user_id: user?.id,
          wizard_state: details.wizard_state,
        }),
      });
    } catch (error) {
      console.error("Admin analytics error", error);
    }
  }, [user?.id]);

  const currentStepIndex = WIZARD_STEPS.findIndex((step) => step.id === wizardStep);
  const nextStep = WIZARD_STEPS[currentStepIndex + 1]?.id;
  const prevStep = WIZARD_STEPS[currentStepIndex - 1]?.id;
  const wizardProgressState = wizardProgress?.state || "draft";
  const dirtySteps = Array.isArray(wizardProgress?.dirty_steps) ? wizardProgress.dirty_steps : [];
  const editModeActive = Boolean(editModeStep || dirtySteps.length > 0);
  const firstDirtyStep = useMemo(
    () => WIZARD_STEPS.find((step) => dirtySteps.includes(step.id))?.id || null,
    [dirtySteps]
  );
  const canEditUnlock = useMemo(() => hasPermission?.(["super_admin", "country_admin"]) ?? false, [hasPermission]);
  const getProgressIndex = (state) => {
    const idx = WIZARD_PROGRESS_ORDER.indexOf(state || "draft");
    return idx === -1 ? 0 : idx;
  };
  const wizardProgressIndex = getProgressIndex(wizardProgressState);
  const isStepDirty = (stepId) => dirtySteps.includes(stepId);
  const isStepCompleted = (stepId) => {
    if (isStepDirty(stepId)) return false;
    if (stepId === "hierarchy") {
      return hierarchyComplete || wizardProgressIndex >= getProgressIndex(STEP_PROGRESS_STATE[stepId] || "draft");
    }
    return wizardProgressIndex >= getProgressIndex(STEP_PROGRESS_STATE[stepId] || "draft");
  };
  const isHierarchyLocked = isStepCompleted("hierarchy");
  const isRootCategory = !form.parent_id;
  const categoryImagePreviewUrl = useMemo(
    () => resolveCategoryImagePreviewUrl(form.image_url, categoryImageCacheBuster),
    [form.image_url, categoryImageCacheBuster],
  );
  const isNextEnabled = Boolean(nextStep) && isStepCompleted(wizardStep) && !stepSaving;
  const nextTooltip = stepSaving
    ? "Kaydediliyor..."
    : !isStepCompleted(wizardStep)
      ? "Önce bu adımı tamamlayın."
      : "";
  const schemaStatusLabel = schema.status === "published" ? "Yayında" : "Taslak";
  const publishValidation = useMemo(() => {
    const errors = [];
    const dirtyLabels = dirtySteps
      .map((stepId) => WIZARD_STEPS.find((step) => step.id === stepId)?.label)
      .filter(Boolean);
    if (dirtyLabels.length > 0) {
      errors.push(`Dirty adımlar tamamlanmalı: ${dirtyLabels.join(", ")}.`);
    }
    if (!effectiveHierarchyComplete) {
      errors.push("Kategori tamamlanmalı.");
    }
    const titleRangeValid = schema.core_fields.title.min <= schema.core_fields.title.max;
    const descriptionRangeValid = schema.core_fields.description.min <= schema.core_fields.description.max;
    const priceRange = schema.core_fields.price.range || { min: 0, max: null };
    const priceRangeValid = priceRange.max === null || priceRange.max === undefined || priceRange.min <= priceRange.max;
    const coreRequiredValid = schema.core_fields.title.required && schema.core_fields.description.required && schema.core_fields.price.required;
    if (!coreRequiredValid || !titleRangeValid || !descriptionRangeValid || !priceRangeValid) {
      errors.push("Çekirdek alanlarda zorunlu ve aralık kontrolleri tamamlanmalı.");
    }
    const dynamicValid = (schema.dynamic_fields || []).every((field) => {
      if (!field.label || !field.key) return false;
      if (field.type === "select" || field.type === "radio") {
        return Array.isArray(field.options) && field.options.length > 0;
      }
      return true;
    });
    if (!dynamicValid) {
      errors.push("Parametre alanlarında type-driven kurallar geçerli olmalı.");
    }
    const detailValid = (schema.detail_groups || []).length > 0 && (schema.detail_groups || []).every((group) => (
      group.title && group.id && Array.isArray(group.options) && group.options.length > 0
    ));
    if (!detailValid) {
      errors.push("Detay gruplarında en az 1 seçenekli grup bulunmalı.");
    }
    if (!previewComplete) {
      errors.push("Önizleme adımı tamamlanmalı.");
    }
    return { canPublish: errors.length === 0, errors };
  }, [effectiveHierarchyComplete, schema, previewComplete, dirtySteps]);
  const isPaymentEnabled = Boolean(schema.modules?.payment?.enabled);
  const isPhotosEnabled = Boolean(schema.modules?.photos?.enabled);
  const autosaveEnabled = Boolean(modalOpen && editing && schema.status === "draft" && effectiveHierarchyComplete);
  const autosaveSnapshot = useMemo(() => JSON.stringify({
    form,
    schema,
    vehicle_segment: vehicleSegment,
    hierarchy_complete: effectiveHierarchyComplete,
    wizard_progress: wizardProgress,
  }), [form, schema, vehicleSegment, effectiveHierarchyComplete, wizardProgress]);

  const formatTime = (value) => {
    if (!value) return "";
    const date = typeof value === "string" ? new Date(value) : value;
    if (Number.isNaN(date.getTime())) return "";
    return date.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  };

  const normalizeWizardProgress = (progress) => ({
    state: progress?.state || "draft",
    dirty_steps: Array.isArray(progress?.dirty_steps) ? progress.dirty_steps : [],
  });

  const persistSnapshot = (override = {}) => {
    const snapshot = {
      form: override.form ?? form,
      schema: override.schema ?? schema,
      vehicle_segment: override.vehicle_segment ?? vehicleSegment,
      hierarchy_complete: override.hierarchy_complete ?? effectiveHierarchyComplete,
      wizard_progress: override.wizard_progress ?? wizardProgress,
    };
    lastSavedSnapshotRef.current = JSON.stringify(snapshot);
  };

  const restoreSnapshot = () => {
    if (!lastSavedSnapshotRef.current) return;
    try {
      const snapshot = JSON.parse(lastSavedSnapshotRef.current);
      if (snapshot.form) {
        setForm(snapshot.form);
      }
      if (snapshot.schema) {
        setSchema(snapshot.schema);
      }
      if (typeof snapshot.vehicle_segment === "string") {
        setVehicleSegment(snapshot.vehicle_segment);
      }
      if (typeof snapshot.hierarchy_complete === "boolean") {
        setHierarchyComplete(snapshot.hierarchy_complete);
      }
      if (snapshot.wizard_progress) {
        setWizardProgress(normalizeWizardProgress(snapshot.wizard_progress));
      }
    } catch (error) {
      // ignore
    }
  };

  const applyCategoryFromServer = (category, options = {}) => {
    if (!category) return;
    const serverVehicleSegment = category.vehicle_segment || category.form_schema?.category_meta?.vehicle_segment || "";
    const serverVehicleLinked = Boolean(
      category.vehicle_master_linked ?? category.form_schema?.category_meta?.master_data_linked
    );
    const nextForm = {
      name: category.name || form.name,
      slug: category.slug || form.slug,
      parent_id: category.parent_id || form.parent_id,
      country_code: category.country_code || form.country_code,
      module: category.module || form.module,
      active_flag: category.active_flag ?? form.active_flag,
      sort_order: category.sort_order ?? form.sort_order,
      image_url: category.image_url || "",
    };
    const nextSchema = category.form_schema ? applySchemaDefaults(category.form_schema) : schema;
    const nextWizardProgress = normalizeWizardProgress(category.wizard_progress);

    setEditing(category);
    setForm(nextForm);
    if (category.form_schema) {
      setSchema(nextSchema);
    }
    setWizardProgress(nextWizardProgress);
    setHierarchyComplete(Boolean(category.hierarchy_complete));
    setLastSavedAt(formatTime(category.updated_at || new Date()));
    setVehicleSegment(serverVehicleSegment);
    setVehicleSegmentError("");
    setVehicleLinkStatus((prev) => ({
      ...prev,
      linked: serverVehicleLinked,
      message: serverVehicleSegment
        ? (serverVehicleLinked ? "Master data bağlantısı hazır." : "Master data bağlantısı doğrulanmadı.")
        : "",
    }));
    setOrderPreview({ checking: false, available: true, message: "", conflict: null, suggested_next_sort_order: null });
    setCategoryImageError("");
    setCategoryImageCacheBuster(Date.now());
    persistSnapshot({
      form: nextForm,
      schema: nextSchema,
      vehicle_segment: serverVehicleSegment,
      hierarchy_complete: Boolean(category.hierarchy_complete),
      wizard_progress: nextWizardProgress,
    });
    if (options.clearEditMode) {
      setEditModeStep(null);
    }
  };

  const showDraftToast = (payload) => {
    if (autosaveToastRef.current?.update) {
      autosaveToastRef.current.update(payload);
      return;
    }
    autosaveToastRef.current = toast(payload);
  };

  const dismissDraftToast = (delay = 2000) => {
    if (!autosaveToastRef.current?.dismiss) return;
    setTimeout(() => autosaveToastRef.current?.dismiss(), delay);
  };

  const buildSavePayload = (status, activeEditing, progressState, options = {}) => {
    const payload = {
      ...form,
      sort_order: Number(form.sort_order || 1),
      vehicle_segment: form.module === "vehicle" ? vehicleSegment : undefined,
      hierarchy_complete: effectiveHierarchyComplete,
      expected_updated_at: activeEditing?.updated_at,
    };
    if (effectiveHierarchyComplete || status !== "draft") {
      payload.form_schema = sanitizeSchemaStrings({ ...schema, status });
    }
    if (progressState) {
      payload.wizard_progress = {
        state: progressState,
        dirty_steps: options.dirtySteps ?? dirtySteps,
      };
    }
    if (options.wizardEditEvent) {
      payload.wizard_edit_event = options.wizardEditEvent;
    }
    return payload;
  };

  const buildDirtyChain = (stepId) => {
    const chain = DIRTY_DEPENDENCIES[stepId] || [];
    return [stepId, ...chain];
  };

  const diffObjects = (prevValue, nextValue, prefix = "") => {
    if (prevValue === nextValue) return [];
    if (typeof prevValue !== "object" || prevValue === null || typeof nextValue !== "object" || nextValue === null) {
      return [prefix || "root"];
    }
    const keys = new Set([...Object.keys(prevValue), ...Object.keys(nextValue)]);
    const changes = [];
    keys.forEach((key) => {
      const path = prefix ? `${prefix}.${key}` : key;
      changes.push(...diffObjects(prevValue[key], nextValue[key], path));
    });
    return changes;
  };


  const fetchItems = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (selectedCountry) {
        params.set("country", selectedCountry);
      }
      if (listFilters.module !== "all") {
        params.set("module", listFilters.module);
      }
      if (listFilters.status === "active") {
        params.set("active_flag", "true");
      }
      if (listFilters.status === "passive") {
        params.set("active_flag", "false");
      }
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories?${params.toString()}`, {
        headers: authHeader,
      });
      const data = await res.json();
      setItems(data.items || []);
      setSelectedIds([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchVehicleSegmentLinkStatus = useCallback(async (segment, countryCode) => {
    if (!segment) {
      setVehicleSegmentError("");
      setVehicleLinkStatus({
        checking: false,
        linked: false,
        make_count: 0,
        model_count: 0,
        message: "Segment adı giriniz.",
      });
      return;
    }
    setVehicleLinkStatus((prev) => ({ ...prev, checking: true, message: "Master data bağlantısı kontrol ediliyor..." }));
    try {
      const params = new URLSearchParams({ segment });
      if (countryCode) {
        params.set("country", countryCode);
      }
      const res = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/vehicle-segment/link-status?${params.toString()}`,
        { headers: authHeader }
      );
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const parsed = parseApiError(data, "Master data bağlantısı doğrulanamadı.");
        setVehicleSegmentError(parsed.message);
        setVehicleLinkStatus({
          checking: false,
          linked: false,
          make_count: 0,
          model_count: 0,
          message: parsed.message,
        });
        return;
      }
      const linked = Boolean(data?.linked);
      const makeCount = Number(data?.make_count || 0);
      const modelCount = Number(data?.model_count || 0);
      setVehicleSegmentError("");
      setVehicleLinkStatus({
        checking: false,
        linked,
        make_count: makeCount,
        model_count: modelCount,
        message: linked
          ? `Master Data Linked • ${makeCount} make / ${modelCount} model`
          : "Bu segment için master data kaydı bulunamadı.",
      });
    } catch (error) {
      setVehicleSegmentError("Master data bağlantısı doğrulanamadı.");
      setVehicleLinkStatus({
        checking: false,
        linked: false,
        make_count: 0,
        model_count: 0,
        message: "Master data bağlantısı doğrulanamadı.",
      });
    }
  }, [authHeader]);

  const fetchOrderPreview = useCallback(async ({ moduleValue, countryCode, parentId, sortOrder, excludeId }) => {
    if (!moduleValue || !countryCode || !Number.isFinite(sortOrder) || sortOrder <= 0) {
      setOrderPreview({ checking: false, available: true, message: "", conflict: null, suggested_next_sort_order: null });
      return;
    }

    setOrderPreview((prev) => ({ ...prev, checking: true }));
    try {
      const params = new URLSearchParams({
        module: moduleValue,
        country: countryCode,
        sort_order: String(sortOrder),
      });
      if (parentId) params.set("parent_id", parentId);
      if (excludeId) params.set("exclude_id", excludeId);

      const res = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/order-index/preview?${params.toString()}`,
        { headers: authHeader }
      );
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const parsed = parseApiError(data, "Sıra önizleme kontrolü başarısız.");
        setOrderPreview({ checking: false, available: true, message: parsed.message, conflict: null, suggested_next_sort_order: null });
        return;
      }

      setOrderPreview({
        checking: false,
        available: Boolean(data?.available),
        message: data?.message || "",
        conflict: data?.conflict || null,
        suggested_next_sort_order: Number.isFinite(Number(data?.suggested_next_sort_order)) ? Number(data.suggested_next_sort_order) : null,
      });
    } catch (error) {
      setOrderPreview({ checking: false, available: true, message: "Sıra kontrolü yapılamadı.", conflict: null, suggested_next_sort_order: null });
    }
  }, [authHeader]);

  const findNextAvailableSortOrder = useCallback(async ({ moduleValue, countryCode, parentId, startOrder = 1, excludeId }) => {
    if (!moduleValue || !countryCode) return null;
    let candidate = Number.isFinite(Number(startOrder)) ? Math.max(1, Number(startOrder)) : 1;
    for (let index = 0; index < 50; index += 1) {
      try {
        const params = new URLSearchParams({
          module: moduleValue,
          country: countryCode,
          sort_order: String(candidate),
        });
        if (parentId) params.set("parent_id", parentId);
        if (excludeId) params.set("exclude_id", excludeId);

        const res = await fetch(
          `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/order-index/preview?${params.toString()}`,
          { headers: authHeader }
        );
        const data = await res.json().catch(() => ({}));
        if (res.ok && data?.available) return candidate;
      } catch (error) {
        return null;
      }
      candidate += 1;
    }
    return null;
  }, [authHeader]);

  const createCategoryWithSortFallback = useCallback(async (initialPayload, fallbackMessage) => {
    const moduleValue = (initialPayload.module || "").trim().toLowerCase();
    const countryCode = (initialPayload.country_code || "").trim().toUpperCase();
    const parentId = initialPayload.parent_id || "";
    const baseSlug = normalizeSlugValue(initialPayload.slug || initialPayload.name || "") || `kategori-${Date.now().toString().slice(-5)}`;
    let payload = {
      ...initialPayload,
      slug: baseSlug,
      sort_order: Number(initialPayload.sort_order || 1),
    };

    for (let attempt = 0; attempt < 12; attempt += 1) {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeader,
        },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        return { ok: true, data, payload, autoAdjusted: attempt > 0 };
      }

      const parsed = parseApiError(data, fallbackMessage);

      const parsedMessageLower = String(parsed?.message || "").toLowerCase();
      const hasSlugConflict = parsedMessageLower.includes("slug") && parsedMessageLower.includes("exists");
      const hasSlugFormatError = parsedMessageLower.includes("slug") && parsedMessageLower.includes("format");
      if ((hasSlugConflict || hasSlugFormatError) && baseSlug) {
        const uniqueSuffix = `${Date.now().toString().slice(-4)}-${attempt + 2}`;
        payload = { ...payload, slug: normalizeSlugValue(`${baseSlug}-${uniqueSuffix}`) };
        continue;
      }

      if (parsed.errorCode === "ORDER_INDEX_ALREADY_USED") {
        const nextSort = await findNextAvailableSortOrder({
          moduleValue,
          countryCode,
          parentId,
          startOrder: Number(payload.sort_order || 1) + 1,
        });
        if (nextSort && nextSort !== payload.sort_order) {
          payload = { ...payload, sort_order: nextSort };
          continue;
        }
      }

      return { ok: false, parsed, payload };
    }

    return { ok: false, parsed: { errorCode: "", message: fallbackMessage }, payload };
  }, [authHeader, findNextAvailableSortOrder]);

  const fetchVersions = async () => {
    if (!editing?.id) return;
    setVersionsLoading(true);
    setVersionsError("");
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${editing.id}/versions`, {
        headers: authHeader,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setVersionsError(data?.detail || "Versiyonlar yüklenemedi.");
        setVersions([]);
        return;
      }
      const data = await res.json();
      setVersions(data.items || []);
    } catch (error) {
      setVersionsError("Versiyonlar yüklenemedi.");
      setVersions([]);
    } finally {
      setVersionsLoading(false);
    }
  };

  const fetchVersionDetail = async (versionId) => {
    if (!editing?.id || !versionId) return;
    if (versionDetails[versionId]) return;
    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${editing.id}/versions/${versionId}`, {
        headers: authHeader,
      });
      if (!res.ok) return;
      const data = await res.json();
      if (data?.version) {
        setVersionDetails((prev) => ({ ...prev, [versionId]: data.version }));
      }
    } catch (error) {
      // ignore
    }
  };

  const handleVersionSelect = (versionId) => {
    setSelectedVersions((prev) => {
      if (prev.includes(versionId)) {
        return prev.filter((id) => id !== versionId);
      }
      if (prev.length >= 2) {
        return [prev[1], versionId];
      }
      return [...prev, versionId];
    });
  };

  const buildDiffPaths = (left, right, basePath = "") => {
    if (left === right) return [];
    const leftIsObj = left && typeof left === "object";
    const rightIsObj = right && typeof right === "object";
    if (!leftIsObj || !rightIsObj) {
      return [basePath || "root"];
    }
    const keys = new Set([...(Array.isArray(left) ? left.keys() : Object.keys(left)), ...(Array.isArray(right) ? right.keys() : Object.keys(right))]);
    const paths = [];
    keys.forEach((key) => {
      const path = basePath ? `${basePath}.${key}` : `${key}`;
      const leftValue = Array.isArray(left) ? left[key] : left[key];
      const rightValue = Array.isArray(right) ? right[key] : right[key];
      paths.push(...buildDiffPaths(leftValue, rightValue, path));
    });
    return paths;
  };

  const versionCompare = useMemo(() => {
    if (selectedVersions.length !== 2) {
      return { left: null, right: null, diffPaths: [] };
    }
    const left = versionDetails[selectedVersions[0]];
    const right = versionDetails[selectedVersions[1]];
    if (!left || !right) {
      return { left, right, diffPaths: [] };
    }
    const diffPaths = buildDiffPaths(left.schema_snapshot, right.schema_snapshot);
    return { left, right, diffPaths };
  }, [selectedVersions, versionDetails]);

  useEffect(() => {
    fetchItems();
  }, [selectedCountry, listFilters.module, listFilters.status]);

  useEffect(() => {
    if (!bulkJobPolling || !bulkJob?.job_id) return;
    let cancelled = false;

    const poll = async () => {
      try {
        const res = await fetch(
          `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/bulk-actions/jobs/${bulkJob.job_id}`,
          { headers: authHeader },
        );
        const data = await res.json().catch(() => ({}));
        if (!res.ok || !data?.job) return;
        if (cancelled) return;

        setBulkJob(data.job);
        if (["done", "failed"].includes(data.job.status)) {
          setBulkJobPolling(false);
          if (data.job.status === "done") {
            toast({
              title: "Toplu işlem tamamlandı",
              description: `Etkilenen: ${data.job.changed_records || 0}, değişmeden kalan: ${data.job.unchanged_records || 0}`,
            });
            setSelectedIds([]);
            setBulkConfirmOpen(false);
            setBulkConfirmValue("");
            setPendingBulkAction("");
            await fetchItems();
          } else {
            toast({
              title: "Toplu işlem başarısız",
              description: data.job.error_message || data.job.error_code || "Job başarısız oldu.",
              variant: "destructive",
            });
          }
        }
      } catch (error) {
        // polling best-effort
      }
    };

    poll();
    const timer = setInterval(poll, 2500);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [bulkJobPolling, bulkJob?.job_id, authHeader]);

  useEffect(() => {
    if (form.module !== "vehicle") {
      setVehicleSegmentError("");
      setVehicleLinkStatus({
        checking: false,
        linked: false,
        make_count: 0,
        model_count: 0,
        message: "",
      });
      return;
    }
    const code = (form.country_code || "").trim().toUpperCase();
    fetchVehicleSegmentLinkStatus(vehicleSegment, code);
  }, [form.module, form.country_code, vehicleSegment, fetchVehicleSegmentLinkStatus]);

  useEffect(() => {
    if (!modalOpen || wizardStep !== "hierarchy") return;
    const moduleValue = (form.module || "").trim().toLowerCase();
    const countryCode = (form.country_code || "").trim().toUpperCase();
    const sortOrder = Number(form.sort_order || 0);
    const timer = setTimeout(() => {
      fetchOrderPreview({
        moduleValue,
        countryCode,
        parentId: form.parent_id || "",
        sortOrder,
        excludeId: editing?.id || "",
      });
    }, 350);
    return () => clearTimeout(timer);
  }, [
    modalOpen,
    wizardStep,
    form.module,
    form.country_code,
    form.parent_id,
    form.sort_order,
    editing?.id,
    fetchOrderPreview,
  ]);

  useEffect(() => {
    setPreviewComplete(false);
  }, [schema, form, hierarchyComplete]);

  useEffect(() => {
    setPublishError("");
  }, [wizardStep]);

  useEffect(() => {
    if (modalOpen && editing?.id) {
      fetchVersions();
      persistSnapshot();
      setLastSavedAt(formatTime(editing.updated_at));
      return;
    }
    setVersions([]);
    setVersionsError("");
    setSelectedVersions([]);
    setVersionDetails({});
    setLastSavedAt("");
    setAutosaveStatus("idle");
    lastSavedSnapshotRef.current = "";
    setLastSavedAt("");
  }, [modalOpen, editing?.id]);

  useEffect(() => {
    selectedVersions.forEach((versionId) => {
      if (!versionDetails[versionId]) {
        fetchVersionDetail(versionId);
      }
    });
  }, [selectedVersions, versionDetails]);

  useEffect(() => {
    if (!autosaveEnabled) return;
    if (!effectiveHierarchyComplete) return;
    if (autosaveSnapshot === lastSavedSnapshotRef.current) return;

    if (autosaveTimeoutRef.current) {
      clearTimeout(autosaveTimeoutRef.current);
    }
    autosaveTimeoutRef.current = setTimeout(() => {
      handleSave("draft", null, false, { autosave: true });
    }, 2500);

    return () => {
      if (autosaveTimeoutRef.current) {
        clearTimeout(autosaveTimeoutRef.current);
      }
    };
  }, [autosaveSnapshot, autosaveEnabled, effectiveHierarchyComplete]);

  useEffect(() => {
    const handleBeforeUnload = () => {
      if (!autosaveEnabled) return;
      if (autosaveSnapshot === lastSavedSnapshotRef.current) return;
      if (!effectiveHierarchyComplete || !editing?.id) return;

      const token = localStorage.getItem("access_token");
      if (!token) return;
      const payload = buildSavePayload("draft", editing);
      const url = `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${editing.id}`;
      const body = JSON.stringify(payload);
      if (navigator.sendBeacon) {
        const blob = new Blob([body], { type: "application/json" });
        navigator.sendBeacon(url, blob);
      } else {
        fetch(url, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body,
          keepalive: true,
        });
      }
    };
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [autosaveEnabled, autosaveSnapshot, effectiveHierarchyComplete, editing]);

  const parentOptions = useMemo(() => items.filter((item) => item.id !== editing?.id), [items, editing]);

  const getSubcategoryLabel = (path) => `Alt kategori ${path.map((index) => index + 1).join(".")}`;

  const getNodeByPath = (nodes, path) => {
    let current = null;
    let list = nodes;
    for (const idx of path) {
      current = list[idx];
      if (!current) return null;
      list = current.children || [];
    }
    return current;
  };

  const updateNodeByPath = (nodes, path, updater) => {
    if (!path.length) return nodes;
    const [index, ...rest] = path;
    return nodes.map((node, idx) => {
      if (idx !== index) return node;
      if (rest.length === 0) {
        return typeof updater === "function" ? updater(node) : { ...node, ...updater };
      }
      return { ...node, children: updateNodeByPath(node.children || [], rest, updater) };
    });
  };

  const removeNodeByPath = (nodes, path) => {
    if (!path.length) return nodes;
    const [index, ...rest] = path;
    if (rest.length === 0) {
      return nodes.filter((_, idx) => idx !== index);
    }
    return nodes.map((node, idx) => {
      if (idx !== index) return node;
      return { ...node, children: removeNodeByPath(node.children || [], rest) };
    });
  };

  const buildSubcategoryTree = (parentId) => {
    const children = items
      .filter((child) => child.parent_id === parentId)
      .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
    return children.map((child) => ({
      id: child.id,
      name: child.name || "",
      slug: child.slug || "",
      active_flag: child.active_flag ?? true,
      sort_order: child.sort_order || 0,
      transaction_type: child.form_schema?.category_meta?.transaction_type || "",
      is_complete: true,
      children: buildSubcategoryTree(child.id),
    }));
  };

  const mapTreeToGroupRows = (treeNodes = []) => {
    if (!Array.isArray(treeNodes) || treeNodes.length === 0) {
      return [createSubcategoryGroupDraft()];
    }
    return treeNodes.map((node) => {
      const directChildren = Array.isArray(node.children) ? node.children : [];
      const normalizedChildren = (directChildren.length > 0 ? directChildren : [node]).map((child) => ({
        id: child.id,
        name: child.name || "",
        slug: child.slug || "",
        active_flag: child.active_flag ?? true,
        sort_order: child.sort_order || 0,
        transaction_type: child.transaction_type || "",
        is_complete: true,
        children: [],
      }));
      return {
        ...createSubcategoryGroupDraft(),
        is_complete: true,
        children: normalizedChildren,
      };
    });
  };

  const getParentPathForLevel = (levelIndex) => {
    if (levelIndex === 0) return [];
    return levelSelections.slice(0, levelIndex);
  };

  const getCategoryNumberLabel = (levelIndex, itemIndex) => {
    const parentPath = getParentPathForLevel(levelIndex);
    const pathNumbers = [...parentPath, itemIndex].map((part) => Number(part) + 1);
    return pathNumbers.join(".");
  };

  const getLevelItems = (levelIndex) => {
    if (levelIndex === 0) return subcategories;
    const parent = getNodeByPath(subcategories, getParentPathForLevel(levelIndex));
    return parent?.children || [];
  };

  const resetLevelCompletionFrom = (levelIndex) => {
    setLevelCompletion((prev) => {
      const next = { ...prev };
      Object.keys(next).forEach((key) => {
        if (Number(key) >= levelIndex) {
          delete next[key];
        }
      });
      return next;
    });
  };

  const handleLevelSelect = (levelIndex, itemIndex) => {
    setLevelSelections((prev) => {
      const next = prev.slice(0, levelIndex);
      next[levelIndex] = itemIndex;
      return next;
    });
    resetLevelCompletionFrom(levelIndex + 1);
  };

  const addLevelItem = (levelIndex) => {
    resetLevelCompletionFrom(levelIndex);
    if (levelIndex === 0) {
      setSubcategories((prev) => [...prev, createSubcategoryGroupDraft()]);
      return;
    }
    const parentPath = getParentPathForLevel(levelIndex);
    if (parentPath.length === 0) return;
    setSubcategories((prev) => updateNodeByPath(prev, parentPath, (node) => ({
      ...node,
      children: [...(node.children || []), createSubcategoryDraft()],
    })));
  };

  const updateLevelItem = (levelIndex, itemIndex, patch) => {
    resetLevelCompletionFrom(levelIndex);
    const path = [...getParentPathForLevel(levelIndex), itemIndex];
    updateSubcategory(path, patch);
  };

  const removeLevelItem = (levelIndex, itemIndex) => {
    resetLevelCompletionFrom(levelIndex);
    const path = [...getParentPathForLevel(levelIndex), itemIndex];
    removeSubcategory(path);
    if (levelSelections[levelIndex] === itemIndex) {
      setLevelSelections((prev) => {
        const next = prev.slice(0, levelIndex);
        return next;
      });
    }
  };

  const handleLevelComplete = (levelIndex, items) => {
    if (!items || items.length === 0) {
      setHierarchyError(`Kategori ${levelIndex + 1} için en az bir kayıt gerekir.`);
      return;
    }
    const missing = items.find((item) => !item.name?.trim() || !item.slug?.trim());
    if (missing) {
      setHierarchyError(`Kategori ${levelIndex + 1} için ad ve slug zorunludur.`);
      return;
    }
    const invalidSort = items.find((item) => !Number.isFinite(Number(item.sort_order)) || Number(item.sort_order) <= 0);
    if (invalidSort) {
      setHierarchyError(`Kategori ${levelIndex + 1} için sıra 1 veya daha büyük olmalıdır.`);
      return;
    }

    const normalizedItems = items.map((item) => ({
      ...item,
      name: item.name.trim(),
      slug: item.slug.trim().toLowerCase(),
      sort_order: Number(item.sort_order || 0),
      is_complete: true,
      children: item.children || [],
    }));

    if (levelIndex === 0) {
      setSubcategories(normalizedItems);
    } else {
      const parentPath = getParentPathForLevel(levelIndex);
      if (parentPath.length === 0) {
        setHierarchyError("Önce üst seviyeden bir kategori seçin.");
        return;
      }
      setSubcategories((prev) => updateNodeByPath(prev, parentPath, (node) => ({
        ...node,
        children: normalizedItems,
      })));
    }

    setHierarchyError("");
    setLevelCompletion((prev) => ({ ...prev, [levelIndex]: true }));
    if (levelSelections[levelIndex] === undefined) {
      setLevelSelections((prev) => {
        const next = prev.slice(0, levelIndex);
        next[levelIndex] = 0;
        return next;
      });
    }
  };


  const handleUnlockStep = async (stepId) => {
    if (!editing) return;
    if (!canEditUnlock) {
      setHierarchyError("Bu adımı düzenlemek için yetkiniz yok.");
      return;
    }
    const dirtyChain = buildDirtyChain(stepId);
    const nextDirtySteps = Array.from(new Set([...dirtySteps, ...dirtyChain]));
    const previousWizardStep = wizardStep;
    const previousEditModeStep = editModeStep;

    setWizardStep(stepId);
    setEditModeStep(stepId);
    setStepSaving(true);

    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${editing.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...authHeader,
        },
        body: JSON.stringify({
          wizard_progress: {
            state: wizardProgressState,
            dirty_steps: nextDirtySteps,
          },
          wizard_edit_event: {
            action: "unlock",
            step_id: stepId,
            dirty_chain: dirtyChain,
            changed_fields: [],
            event_timestamp: new Date().toISOString(),
          },
          expected_updated_at: editing.updated_at,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data?.category) {
        throw new Error(data?.detail || "Edit modu açılamadı.");
      }
      applyCategoryFromServer(data.category);
    } catch (error) {
      setHierarchyError(error?.message || "Edit modu açılamadı.");
      setWizardStep(previousWizardStep);
      setEditModeStep(previousEditModeStep);
      restoreSnapshot();
    } finally {
      setStepSaving(false);
    }
  };

  const handleDirtyCta = async () => {
    if (!firstDirtyStep || !editing?.id) return;
    await trackAdminWizardEvent("admin_dirty_cta_clicked", {
      category_id: editing.id,
      step_id: firstDirtyStep,
      wizard_state: wizardProgressState,
    });
    setHierarchyError("");
    setWizardStep(firstDirtyStep);
    await trackAdminWizardEvent("admin_dirty_first_step_opened", {
      category_id: editing.id,
      step_id: firstDirtyStep,
      wizard_state: wizardProgressState,
    });
  };

  const handleHierarchyEdit = async () => {
    if (!editing) return;
    await handleUnlockStep("hierarchy");
  };

  const handleLevelEditColumn = async (levelIndex, items) => {
    if (!items || items.length === 0) return;
    await handleUnlockStep("hierarchy");
    const resetItems = items.map((item) => ({
      ...item,
      is_complete: false,
      children: item.children || [],
    }));
    if (levelIndex === 0) {
      setSubcategories(resetItems);
    } else {
      const parentPath = getParentPathForLevel(levelIndex);
      if (parentPath.length === 0) return;
      setSubcategories((prev) => updateNodeByPath(prev, parentPath, (node) => ({
        ...node,
        children: resetItems,
      })));
    }
    setLevelCompletion((prev) => {
      const next = { ...prev };
      Object.keys(next).forEach((key) => {
        if (Number(key) >= levelIndex) {
          delete next[key];
        }
      });
      return next;
    });
    setLevelSelections((prev) => prev.slice(0, levelIndex));
    setHierarchyError("");
    setHierarchyFieldErrors({});
  };

  const handleLevelEditItem = async (levelIndex, itemIndex) => {
    await handleUnlockStep("hierarchy");
    const path = [...getParentPathForLevel(levelIndex), itemIndex];
    updateSubcategory(path, { is_complete: false });
    setLevelCompletion((prev) => {
      const next = { ...prev };
      Object.keys(next).forEach((key) => {
        if (Number(key) >= levelIndex) {
          delete next[key];
        }
      });
      return next;
    });
    setLevelSelections((prev) => prev.slice(0, levelIndex + 1));
    setHierarchyError("");
    setHierarchyFieldErrors({});
  };


  const resetForm = () => {
    setForm({
      name: "",
      slug: "",
      parent_id: "",
      country_code: selectedCountry || "",
      module: "",
      active_flag: true,
      sort_order: 1,
      image_url: "",
    });
    setSchema(createDefaultSchema());
    setEditing(null);
    setWizardStep("hierarchy");
    setWizardProgress({ state: "draft", dirty_steps: [] });
    setHierarchyComplete(false);
    setHierarchyError("");
    setHierarchyFieldErrors({});
    const initialSubcategories = [createSubcategoryGroupDraft()];
    setSubcategories(initialSubcategories);
    setLevelSelections([]);
    setLevelCompletion({});
    setDynamicDraft({
      label: "",
      key: "",
      type: "select",
      required: false,
      sort_order: 0,
      optionInput: "",
      options: [],
      messages: { required: "", invalid: "" },
    });
    setDynamicEditIndex(null);
    setDynamicError("");
    setDetailDraft({
      id: "",
      title: "",
      required: false,
      sort_order: 0,
      options: [],
      messages: { required: "", invalid: "" },
    });
    setDetailOptionInput("");
    setDetailEditIndex(null);
    setDetailError("");
    setPreviewComplete(false);
    setJsonCopyStatus("");
    setVersions([]);
    setVersionsLoading(false);
    setVersionsError("");
    setSelectedVersions([]);
    setVersionDetails({});
    setVehicleSegment("");
    setVehicleSegmentError("");
    setVehicleLinkStatus({
      checking: false,
      linked: false,
      make_count: 0,
      model_count: 0,
      message: "",
    });
    setOrderPreview({ checking: false, available: true, message: "", conflict: null, suggested_next_sort_order: null });
    setCategoryImageUploading(false);
    setCategoryImageError("");
    setCategoryImageCacheBuster(Date.now());
    setLastSavedAt("");
    setAutosaveStatus("idle");
    lastSavedSnapshotRef.current = "";
  };

  const handleEdit = (item) => {
    const itemVehicleSegment = item.vehicle_segment || item.form_schema?.category_meta?.vehicle_segment || "";
    const itemVehicleLinked = Boolean(item.vehicle_master_linked ?? item.form_schema?.category_meta?.master_data_linked);
    setEditing(item);
    setForm({
      name: item.name || "",
      slug: item.slug || "",
      parent_id: item.parent_id || "",
      country_code: item.country_code || "",
      module: item.module || "",
      active_flag: item.active_flag ?? true,
      sort_order: item.sort_order || 1,
      image_url: item.image_url || "",
    });
    setSchema(applySchemaDefaults(item.form_schema));
    setWizardStep("hierarchy");
    setWizardProgress(normalizeWizardProgress(item.wizard_progress));
    setEditModeStep(null);
    setHierarchyComplete(Boolean(item.hierarchy_complete));
    setHierarchyError("");
    setHierarchyFieldErrors({});
    const relatedSubs = buildSubcategoryTree(item.id);
    const nextSubcategories = mapTreeToGroupRows(relatedSubs);
    setSubcategories(nextSubcategories);
    setLevelSelections([]);
    setLevelCompletion({});
    setDynamicDraft({
      label: "",
      key: "",
      type: "select",
      required: false,
      sort_order: 0,
      optionInput: "",
      options: [],
      messages: { required: "", invalid: "" },
    });
    setDynamicEditIndex(null);
    setDynamicError("");
    setDetailDraft({
      id: "",
      title: "",
      required: false,
      sort_order: 0,
      options: [],
      messages: { required: "", invalid: "" },
    });
    setDetailOptionInput("");
    setDetailEditIndex(null);
    setDetailError("");
    setPreviewComplete(false);
    setJsonCopyStatus("");
    setVersions([]);
    setVersionsLoading(false);
    setVersionsError("");
    setSelectedVersions([]);
    setVersionDetails({});
    setVehicleSegment(itemVehicleSegment);
    setVehicleSegmentError("");
    setVehicleLinkStatus({
      checking: false,
      linked: itemVehicleLinked,
      make_count: 0,
      model_count: 0,
      message: itemVehicleSegment
        ? (itemVehicleLinked ? "Master data bağlantısı hazır." : "Master data bağlantısı doğrulanmadı.")
        : "",
    });
    setOrderPreview({ checking: false, available: true, message: "", conflict: null });
    setCategoryImageUploading(false);
    setCategoryImageError("");
    setCategoryImageCacheBuster(Date.now());
    setLastSavedAt("");
    setAutosaveStatus("idle");
    lastSavedSnapshotRef.current = "";
    setIsModalFullscreen(false);
    setModalSize({ width: 1280, height: 820 });
    setModalOpen(true);
  };

  const handleCreate = () => {
    resetForm();
    setWizardStep("hierarchy");
    setHierarchyComplete(false);
    setIsModalFullscreen(false);
    setModalSize({ width: 1280, height: 820 });
    setModalOpen(true);
  };

  const handleCategoryImageUpload = async (event) => {
    const selectedFile = event.target.files?.[0];
    event.target.value = "";
    if (!selectedFile) return;
    if (!isRootCategory) {
      setCategoryImageError("Görsel yükleme sadece ana kategori için kullanılabilir.");
      return;
    }

    const extension = (selectedFile.name || "").split(".").pop()?.toLowerCase() || "";
    if (!CATEGORY_IMAGE_ALLOWED_EXTENSIONS.includes(extension)) {
      setCategoryImageError("Sadece png, jpg ve webp dosyaları yüklenebilir.");
      return;
    }
    if (selectedFile.size > CATEGORY_IMAGE_MAX_BYTES) {
      setCategoryImageError("Görsel boyutu 2MB sınırını aşamaz.");
      return;
    }

    setCategoryImageUploading(true);
    setCategoryImageError("");
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/image-upload`, {
        method: "POST",
        headers: {
          ...authHeader,
        },
        body: formData,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const parsed = parseApiError(data, "Kategori görseli yüklenemedi.");
        throw new Error(parsed.message);
      }

      const uploadedUrl = data?.image_url || "";
      if (!uploadedUrl) {
        throw new Error("Kategori görseli yüklenemedi.");
      }

      setForm((prev) => ({ ...prev, image_url: uploadedUrl }));
      setHierarchyFieldErrors((prev) => {
        const next = { ...prev };
        delete next.main_image_url;
        return next;
      });
      setCategoryImageCacheBuster(Date.now());
      setCategoryImageError("");
    } catch (error) {
      setCategoryImageError(error?.message || "Kategori görseli yüklenemedi.");
    } finally {
      setCategoryImageUploading(false);
    }
  };

  const handleCategoryImageRemove = () => {
    if (isHierarchyLocked) return;
    setForm((prev) => ({ ...prev, image_url: "" }));
    setCategoryImageCacheBuster(Date.now());
    setCategoryImageError("");
  };

  const handleModuleToggle = (key, enabled) => {
    setSchema((prev) => {
      const updated = {
        ...prev,
        modules: {
          ...prev.modules,
          [key]: { ...prev.modules[key], enabled },
        },
      };
      if (key === "payment" && !enabled) {
        return { ...updated, payment_options: { package: false, doping: false } };
      }
      return updated;
    });
  };

  const handleCopySchema = () => {
    try {
      const text = JSON.stringify(schema, null, 2);
      if (navigator?.clipboard?.writeText) {
        navigator.clipboard.writeText(text);
        setJsonCopyStatus("Kopyalandı");
        setTimeout(() => setJsonCopyStatus(""), 2000);
      } else {
        setJsonCopyStatus("Kopyalanamadı");
      }
    } catch (error) {
      setJsonCopyStatus("Kopyalanamadı");
    }
  };

  const parseExportFilename = (contentDisposition, fallback) => {
    if (!contentDisposition) return fallback;
    const match = contentDisposition.match(/filename="?([^";]+)"?/i);
    return match ? match[1] : fallback;
  };

  const handleExport = async (format) => {
    if (!editing?.id) {
      toast({ title: "Export başarısız", description: "Önce taslak kaydedin.", variant: "destructive" });
      return;
    }
    try {
      const res = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${editing.id}/export/${format}`,
        { headers: authHeader }
      );
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        toast({ title: "Export başarısız", description: data?.detail || "Dosya indirilemedi.", variant: "destructive" });
        return;
      }
      const blob = await res.blob();
      const filename = parseExportFilename(
        res.headers.get("content-disposition"),
        `schema-${editing.id}.${format}`
      );
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      toast({ title: "Export başarısız", description: "Dosya indirilemedi.", variant: "destructive" });
    }
  };

  const handleSave = async (status = "draft", overrideEditing = null, closeOnSuccess = true, options = {}) => {
    const { autosave = false, progressState } = options;
    setHierarchyError("");
    setPublishError("");
    const activeEditing = overrideEditing ?? editing;
    const hierarchyOk = effectiveHierarchyComplete;
    if (!hierarchyOk && status !== "draft") {
      setHierarchyError("Önce hiyerarşiyi tamamlayın.");
      if (status === "draft") {
        showDraftToast({
          title: "Kaydetme başarısız",
          description: "Kategori tamamlanmadan kaydedilemez.",
          variant: "destructive",
        });
        dismissDraftToast(4000);
      }
      return { success: false };
    }
    if (status === "published" && !publishValidation.canPublish) {
      setPublishError("Yayınlama için zorunlu şartlar tamamlanmalı.");
      return { success: false };
    }

    const nextDirtySteps = progressState ? dirtySteps.filter((step) => step !== wizardStep) : dirtySteps;
    let wizardEditEvent = null;
    if (editModeStep === wizardStep && progressState) {
      let previousSnapshot = {};
      try {
        previousSnapshot = lastSavedSnapshotRef.current ? JSON.parse(lastSavedSnapshotRef.current) : {};
      } catch (error) {
        previousSnapshot = {};
      }
      const changedFields = diffObjects(previousSnapshot, autosaveSnapshot);
      wizardEditEvent = {
        action: "save",
        step_id: wizardStep,
        dirty_chain: buildDirtyChain(wizardStep),
        changed_fields: changedFields,
        event_timestamp: new Date().toISOString(),
      };
    }

    const payload = buildSavePayload(status, activeEditing, progressState, {
      dirtySteps: nextDirtySteps,
      wizardEditEvent,
    });
    if (!payload.name || !payload.slug) {
      setHierarchyError("Kategori adı ve slug zorunludur.");
      return { success: false };
    }
    const url = activeEditing
      ? `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${activeEditing.id}`
      : `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories`;
    const method = activeEditing ? "PATCH" : "POST";

    if (status === "draft") {
      setAutosaveStatus("saving");
      showDraftToast({
        title: "Kaydediliyor...",
        description: "Taslak otomatik kaydediliyor.",
      });
    }

    const res = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        ...authHeader,
      },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const parsed = parseApiError(data, "Kaydetme sırasında hata oluştu.");
      if (res.status === 409) {
        if (String(parsed.message || "").toLowerCase().includes("hiyerar")) {
          showDraftToast({
            title: "Kaydetme başarısız",
            description: "Kategori tamamlanmadan kaydedilemez.",
            variant: "destructive",
          });
        } else {
          showDraftToast({
            title: "Kaydetme başarısız",
            description: "Başka bir sekmede güncellendi.",
            variant: "destructive",
          });
        }
        dismissDraftToast(4000);
      } else if (status === "draft") {
        showDraftToast({
          title: "Kaydetme başarısız",
          description: "Taslak kaydedilemedi.",
          variant: "destructive",
        });
        dismissDraftToast(4000);
      }
      if (parsed.errorCode === "ORDER_INDEX_ALREADY_USED") {
        setHierarchyFieldErrors((prev) => ({ ...prev, main_sort_order: parsed.message }));
      }
      if (parsed.errorCode === "VEHICLE_SEGMENT_NOT_FOUND" || parsed.errorCode === "VEHICLE_SEGMENT_ALREADY_DEFINED") {
        setVehicleSegmentError(parsed.message);
      }
      if (!autosave) {
        setHierarchyError(parsed.message);
        restoreSnapshot();
      }
      setAutosaveStatus("idle");
      return { success: false };
    }
    if (!data?.category) {
      if (!autosave) {
        setHierarchyError("Sunucu yanıtı eksik. Lütfen tekrar deneyin.");
        restoreSnapshot();
      }
      setAutosaveStatus("idle");
      return { success: false };
    }
    const savedCategory = data.category;
    if (savedCategory) {
      applyCategoryFromServer(savedCategory, {
        clearEditMode: Boolean(progressState && editModeStep === wizardStep),
      });
    }
    if (status === "draft") {
      showDraftToast({
        title: "Taslak kaydedildi",
        description: "Değişiklikler kaydedildi.",
      });
      dismissDraftToast(4000);
    }
    setAutosaveStatus("idle");
    fetchItems();
    if (closeOnSuccess) {
      setModalOpen(false);
      resetForm();
    }
    return { success: true, category: savedCategory };
  };

  const handleStepComplete = async () => {
    if (stepSaving) return;
    setHierarchyError("");
    const progressState = STEP_PROGRESS_STATE[wizardStep];
    if (!progressState) return;

    if (wizardStep === "core") {
      const titleRangeValid = schema.core_fields.title.min <= schema.core_fields.title.max;
      const descriptionRangeValid = schema.core_fields.description.min <= schema.core_fields.description.max;
      const priceRange = schema.core_fields.price.range || { min: 0, max: null };
      const priceRangeValid = priceRange.max === null || priceRange.max === undefined || priceRange.min <= priceRange.max;
      const coreRequiredValid = schema.core_fields.title.required && schema.core_fields.description.required && schema.core_fields.price.required;
      if (!coreRequiredValid || !titleRangeValid || !descriptionRangeValid || !priceRangeValid) {
        setHierarchyError("Çekirdek alanlarda zorunlu ve aralık kontrolleri tamamlanmalı.");
        return;
      }
    }

    if (wizardStep === "dynamic") {
      const dynamicValid = (schema.dynamic_fields || []).every((field) => {
        if (!field.label || !field.key) return false;
        if (field.type === "select" || field.type === "radio") {
          return Array.isArray(field.options) && field.options.length > 0;
        }
        return true;
      });
      if (!dynamicValid) {
        setHierarchyError("Parametre alanlarında type-driven kurallar geçerli olmalı.");
        return;
      }
    }

    if (wizardStep === "detail") {
      const detailValid = (schema.detail_groups || []).length > 0 && (schema.detail_groups || []).every((group) => (
        group.title && group.id && Array.isArray(group.options) && group.options.length > 0
      ));
      if (!detailValid) {
        setHierarchyError("Detay gruplarında en az 1 seçenekli grup bulunmalı.");
        return;
      }
    }

    if (wizardStep === "preview" && !previewComplete) {
      setHierarchyError("Önizleme adımı tamamlanmalı.");
      return;
    }

    if (wizardStep !== "hierarchy" && !editing?.id) {
      setHierarchyError("Önce kategori kaydedilmeli.");
      return;
    }

    const nextDirtySteps = dirtySteps.filter((step) => step !== wizardStep);

    setStepSaving(true);
    try {
      if (wizardStep === "hierarchy") {
        const result = await handleHierarchyComplete(progressState, nextDirtySteps);
        if (!result?.success) return;
      } else {
        const result = await handleSave("draft", null, false, { progressState, dirtySteps: nextDirtySteps });
        if (!result?.success) return;
      }
    } finally {
      setStepSaving(false);
    }
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

  const getItemSelectionState = (itemId) => {
    const descendantIds = descendantsByItem.get(itemId) || [itemId];
    const selectedCount = descendantIds.filter((id) => selectedIdSet.has(id)).length;
    return {
      checked: descendantIds.length > 0 && selectedCount === descendantIds.length,
      indeterminate: selectedCount > 0 && selectedCount < descendantIds.length,
    };
  };

  const toggleItemSelection = (item, checked) => {
    const descendantIds = descendantsByItem.get(item.id) || [item.id];
    setSelectedIds((prev) => {
      const nextSet = new Set(prev);
      if (checked) {
        descendantIds.forEach((id) => nextSet.add(id));
      } else {
        descendantIds.forEach((id) => nextSet.delete(id));
      }
      return Array.from(nextSet);
    });
  };

  const toggleAllVisibleSelection = (checked) => {
    if (checked) {
      setSelectedIds(visibleItemIds);
      return;
    }
    setSelectedIds([]);
  };

  const executeBulkAction = async (action) => {
    if (!selectedIds.length) return;
    setBulkRunning(true);
    try {
      const payload = {
        action,
        scope: "ids",
        ids: selectedIds,
        filter: {
          country: selectedCountry,
          module: listFilters.module !== "all" ? listFilters.module : null,
          active_flag: listFilters.status === "all" ? null : listFilters.status === "active",
        },
      };
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/bulk-actions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeader,
        },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const parsed = parseApiError(data, "Toplu işlem başarısız.");
        toast({ title: "Toplu işlem başarısız", description: parsed.message, variant: "destructive" });
        return;
      }

      if (res.status === 202 || data?.mode === "async") {
        const nextJob = data?.job || null;
        if (nextJob?.job_id) {
          setBulkJob(nextJob);
          setBulkJobPolling(true);
          toast({
            title: "Toplu işlem kuyruğa alındı",
            description: `Job ID: ${nextJob.job_id}`,
          });
          setBulkConfirmOpen(false);
          setBulkConfirmValue("");
          setPendingBulkAction("");
        }
        return;
      }

      toast({
        title: "Toplu işlem tamamlandı",
        description: `Etkilenen: ${data?.changed || 0}, değişmeden kalan: ${data?.unchanged || 0}`,
      });
      setBulkJob(null);
      setBulkJobPolling(false);
      setSelectedIds([]);
      setBulkConfirmOpen(false);
      setBulkConfirmValue("");
      setPendingBulkAction("");
      await fetchItems();
    } finally {
      setBulkRunning(false);
    }
  };

  const openBulkDeleteConfirm = () => {
    setPendingBulkAction("delete");
    setBulkConfirmValue("");
    setBulkConfirmOpen(true);
  };

  const confirmBulkDelete = async () => {
    if (bulkConfirmValue.trim().toUpperCase() !== "ONAYLA") {
      toast({
        title: "Onay gerekli",
        description: "Silme işlemi için ONAYLA yazın.",
        variant: "destructive",
      });
      return;
    }
    await executeBulkAction("delete");
  };

  const canAccessStep = (stepId) => {
    if (stepId === "hierarchy") return true;
    if (stepId === wizardStep) return true;
    if (isStepDirty(stepId)) return true;
    return isStepCompleted(stepId);
  };

  const completeSubcategory = (path) => {
    setHierarchyError("");
    const target = getNodeByPath(subcategories, path);
    if (!target) return;
    const label = getSubcategoryLabel(path);
    if (path.length === 1) {
      if (!Array.isArray(target.children) || target.children.length === 0) {
        setHierarchyError(`${label} için en az 1 alt kategori eklenmelidir.`);
        return;
      }
      const invalidChild = target.children.find(
        (child) => !child?.name?.trim() || !child?.slug?.trim() || !Number.isFinite(Number(child.sort_order)) || Number(child.sort_order) <= 0
      );
      if (invalidChild) {
        setHierarchyError(`${label} içindeki alt kategorilerde ad/slug/sıra alanları zorunludur.`);
        return;
      }
      const incompleteChild = target.children.find((child) => !child.is_complete);
      if (incompleteChild) {
        setHierarchyError(`${label} içindeki alt kategoriler tamamlanmadan devam edilemez.`);
        return;
      }

      setSubcategories((prev) => updateNodeByPath(prev, path, (node) => ({
        ...node,
        is_complete: true,
      })));

      const completedIndex = path[0];
      setSubcategories((prev) => {
        if (!Array.isArray(prev)) return prev;
        const hasOpenDraftAfterCurrent = prev.slice(completedIndex + 1).some((item) => !item?.is_complete);
        if (hasOpenDraftAfterCurrent) return prev;
        return [...prev, createSubcategoryGroupDraft()];
      });
      setLevelSelections((prev) => {
        const next = prev.slice(0, 1);
        next[0] = completedIndex + 1;
        return next;
      });
      resetLevelCompletionFrom(0);
      return;
    }

    if (!target?.name?.trim() || !target?.slug?.trim()) {
      setHierarchyError(`${label} için ad ve slug zorunludur.`);
      return;
    }
    if (!Number.isFinite(Number(target.sort_order)) || Number(target.sort_order) <= 0) {
      setHierarchyError(`${label} için sıra 1 veya daha büyük olmalıdır.`);
      return;
    }

    setSubcategories((prev) => updateNodeByPath(prev, path, (node) => ({
      ...node,
      name: node.name.trim(),
      slug: node.slug.trim().toLowerCase(),
      is_complete: true,
    })));
  };

  const updateSubcategory = (path, patch) => {
    setSubcategories((prev) => updateNodeByPath(prev, path, patch));
  };

  const removeSubcategory = (path) => {
    setSubcategories((prev) => removeNodeByPath(prev, path));
  };

  const handleHierarchyComplete = async (
    progressState = STEP_PROGRESS_STATE.hierarchy,
    dirtyStepsOverride = dirtySteps
  ) => {
    setHierarchyError("");
    setHierarchyFieldErrors({});

    const name = form.name.trim();
    const slug = form.slug.trim().toLowerCase();
    const country = (form.country_code || "").trim().toUpperCase();
    const moduleValue = (form.module || "").trim().toLowerCase();
    const isVehicleModule = moduleValue === "vehicle";
    const rootSortOrder = Number(form.sort_order || 0);

    const fieldErrors = {};
    if (!name) {
      fieldErrors.main_name = "Ana kategori adı zorunludur.";
    }
    if (!slug) {
      fieldErrors.main_slug = "Slug zorunludur.";
    }
    if (!country) {
      fieldErrors.main_country = "Ülke zorunludur.";
    }
    if (!moduleValue) {
      fieldErrors.main_module = "Modül zorunludur.";
    }
    if (!Number.isFinite(rootSortOrder) || rootSortOrder <= 0) {
      fieldErrors.main_sort_order = "Sıra 1 veya daha büyük olmalıdır.";
    }
    if (isRootCategory && !form.image_url?.trim()) {
      fieldErrors.main_image_url = "Ana kategori görseli zorunludur.";
    }
    if (!orderPreview.available) {
      fieldErrors.main_sort_order = orderPreview.message || "Bu modül ve seviye içinde bu sıra numarası zaten kullanılıyor.";
    }

    if (Object.keys(fieldErrors).length > 0) {
      setHierarchyFieldErrors(fieldErrors);
      setHierarchyError("Lütfen işaretli alanları doldurun.");
      return { success: false };
    }

    if (isVehicleModule && !vehicleSegment) {
      setVehicleSegmentError("Vasıta modülü için segment adı zorunludur.");
      setHierarchyError("Vasıta modülü için segment adı zorunludur.");
      return { success: false };
    }

    if (isVehicleModule && !vehicleLinkStatus.linked) {
      setVehicleSegmentError(vehicleLinkStatus.message || "Girilen segment master data’da bulunamadı.");
      setHierarchyError(vehicleLinkStatus.message || "Seçilen segment master data ile bağlı değil.");
      return { success: false };
    }

    const hasCompletedSubcategory = subcategories.some((group) =>
      Array.isArray(group.children) && group.children.some((child) => child.name?.trim() && child.slug?.trim())
    );
    if (!isVehicleModule && !hasCompletedSubcategory) {
      setHierarchyError("En az 1 alt kategori tamamlanmalıdır.");
      return { success: false };
    }

    let wizardEditEvent = null;
    if (editModeStep === "hierarchy") {
      let previousSnapshot = {};
      try {
        previousSnapshot = lastSavedSnapshotRef.current ? JSON.parse(lastSavedSnapshotRef.current) : {};
      } catch (error) {
        previousSnapshot = {};
      }
      const changedFields = diffObjects(previousSnapshot, autosaveSnapshot);
      wizardEditEvent = {
        action: "save",
        step_id: "hierarchy",
        dirty_chain: buildDirtyChain("hierarchy"),
        changed_fields: changedFields,
        event_timestamp: new Date().toISOString(),
      };
    }

    const normalizeTree = (nodes) => (nodes || [])
      .map((node, index) => ({
        ...node,
        name: node.name ? node.name.trim() : "",
        slug: node.slug ? node.slug.trim().toLowerCase() : "",
        sort_order: Number(node.sort_order || index + 1),
        is_complete: true,
        children: (node.children || []).map((child) => ({
          ...child,
          name: child.name ? child.name.trim() : "",
          slug: child.slug ? child.slug.trim().toLowerCase() : "",
          sort_order: Number(child.sort_order || 0),
          is_complete: true,
          children: [],
        })),
      }))
      .filter((node) => (node.children || []).some((child) => child.name || child.slug));

    const validateTree = (nodes) => {
      if (nodes.length === 0) {
        return "En az 1 alt kategori eklenmelidir.";
      }
      for (let groupIndex = 0; groupIndex < nodes.length; groupIndex += 1) {
        const group = nodes[groupIndex];
        const children = group.children || [];
        if (children.length === 0) {
          fieldErrors[`level-${groupIndex}-children`] = "En az 1 alt kategori gereklidir.";
          return `${groupIndex + 1}. grup için en az 1 alt kategori eklenmelidir.`;
        }
        for (let childIndex = 0; childIndex < children.length; childIndex += 1) {
          const child = children[childIndex];
          const pathKey = `${groupIndex}-${childIndex}`;
          const label = `${groupIndex + 1}.${childIndex + 1}`;
          if (!child.name) fieldErrors[`level-${pathKey}-name`] = "Ad zorunludur.";
          if (!child.slug) fieldErrors[`level-${pathKey}-slug`] = "Slug zorunludur.";
          if (!Number.isFinite(Number(child.sort_order)) || Number(child.sort_order) <= 0) {
            fieldErrors[`level-${pathKey}-sort`] = "Sıra 1 veya daha büyük olmalıdır.";
          }
          if (!child.name || !child.slug) {
            return `${label} için ad ve slug zorunludur.`;
          }
          if (!Number.isFinite(Number(child.sort_order)) || Number(child.sort_order) <= 0) {
            return `${label} için sıra 1 veya daha büyük olmalıdır.`;
          }
        }
      }
      return "";
    };

    const cleanedSubs = isVehicleModule ? [] : normalizeTree(subcategories);
    if (!isVehicleModule) {
      const validationError = validateTree(cleanedSubs);
      if (validationError) {
        if (Object.keys(fieldErrors).length > 0) {
          setHierarchyFieldErrors(fieldErrors);
        }
        setHierarchyError(validationError);
        return { success: false };
      }
    }

    const persistSubcategories = async (nodes, parentId) => {
      const savedGroups = [];
      for (const group of nodes) {
        const children = [];
        for (const child of group.children || []) {
          const basePayload = {
            name: child.name,
            slug: child.slug,
            parent_id: parentId,
            country_code: country,
            module: moduleValue,
            active_flag: child.active_flag,
            sort_order: Number(child.sort_order || 0),
            hierarchy_complete: true,
          };
          if (child.transaction_type) {
            basePayload.form_schema = {
              status: "draft",
              category_meta: { transaction_type: child.transaction_type },
            };
          }
          const url = child.id
            ? `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${child.id}`
            : `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories`;
          const method = child.id ? "PATCH" : "POST";
          let data = {};
          if (method === "POST") {
            const created = await createCategoryWithSortFallback(basePayload, "Alt kategori kaydedilemedi.");
            if (!created.ok) {
              throw new Error(created.parsed.message);
            }
            data = created.data;
          } else {
            const res = await fetch(url, {
              method,
              headers: {
                "Content-Type": "application/json",
                ...authHeader,
              },
              body: JSON.stringify(basePayload),
            });
            data = await res.json().catch(() => ({}));
            if (!res.ok) {
              const parsed = parseApiError(data, "Alt kategori kaydedilemedi.");
              throw new Error(parsed.message);
            }
          }
          const saved = data?.category || child;
          children.push({
            ...child,
            id: saved.id || child.id,
            is_complete: true,
            children: [],
          });
        }
        savedGroups.push({
          ...group,
          is_complete: true,
          children,
        });
      }
      return savedGroups;
    };

    try {
      let updatedParent = editing;

      if (editing) {
        const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${editing.id}`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            ...authHeader,
          },
          body: JSON.stringify({
            name,
            slug,
            country_code: country,
            module: moduleValue,
            image_url: isRootCategory ? (form.image_url || "") : "",
            vehicle_segment: isVehicleModule ? vehicleSegment : undefined,
            active_flag: form.active_flag,
            sort_order: rootSortOrder,
            hierarchy_complete: true,
            wizard_progress: { state: progressState, dirty_steps: dirtyStepsOverride },
            wizard_edit_event: wizardEditEvent || undefined,
            expected_updated_at: editing.updated_at,
          }),
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          const parsed = parseApiError(data, "Kategori güncellenemedi.");
          if (parsed.errorCode === "ORDER_INDEX_ALREADY_USED") {
            setHierarchyFieldErrors((prev) => ({ ...prev, main_sort_order: parsed.message }));
          }
          if (parsed.errorCode === "VEHICLE_SEGMENT_NOT_FOUND" || parsed.errorCode === "VEHICLE_SEGMENT_ALREADY_DEFINED") {
            setVehicleSegmentError(parsed.message);
          }
          setHierarchyError(parsed.message);
          return { success: false };
        }
        updatedParent = data?.category || editing;
      } else {
        const parentPayload = {
          name,
          slug,
          country_code: country,
          module: moduleValue,
          image_url: isRootCategory ? (form.image_url || "") : "",
          vehicle_segment: isVehicleModule ? vehicleSegment : undefined,
          active_flag: form.active_flag,
          sort_order: rootSortOrder,
          hierarchy_complete: isVehicleModule,
          wizard_progress: { state: progressState, dirty_steps: dirtyStepsOverride },
        };
        const createdParent = await createCategoryWithSortFallback(parentPayload, "Ana kategori oluşturulamadı.");
        if (!createdParent.ok) {
          const parsed = createdParent.parsed;
          if (parsed.errorCode === "ORDER_INDEX_ALREADY_USED") {
            setHierarchyFieldErrors((prev) => ({ ...prev, main_sort_order: parsed.message }));
          }
          if (parsed.errorCode === "VEHICLE_SEGMENT_NOT_FOUND" || parsed.errorCode === "VEHICLE_SEGMENT_ALREADY_DEFINED") {
            setVehicleSegmentError(parsed.message);
          }
          setHierarchyError(parsed.message);
          return { success: false };
        }
        if (createdParent.autoAdjusted && createdParent.payload?.sort_order) {
          setForm((prev) => ({ ...prev, sort_order: String(createdParent.payload.sort_order) }));
          toast({
            title: "Sıra otomatik düzeltildi",
            description: `Ana kategori için sıra ${createdParent.payload.sort_order} olarak güncellendi.`,
          });
        }
        if (createdParent.payload?.slug && createdParent.payload.slug !== slug) {
          setForm((prev) => ({ ...prev, slug: createdParent.payload.slug }));
          toast({
            title: "Slug otomatik düzeltildi",
            description: `Ana kategori slug değeri ${createdParent.payload.slug} olarak güncellendi.`,
          });
        }
        updatedParent = createdParent.data?.category;
      }

      const savedSubs = isVehicleModule ? [] : await persistSubcategories(cleanedSubs, updatedParent.id);

      if (!editing && updatedParent?.id && !isVehicleModule) {
        const patchRes = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${updatedParent.id}`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            ...authHeader,
          },
          body: JSON.stringify({ hierarchy_complete: true, wizard_progress: { state: progressState, dirty_steps: dirtyStepsOverride } }),
        });
        const patchData = await patchRes.json().catch(() => ({}));
        if (!patchRes.ok) {
          const parsed = parseApiError(patchData, "Kategori güncellenemedi.");
          setHierarchyError(parsed.message);
          return { success: false };
        }
        updatedParent = patchData?.category || updatedParent;
      }

      applyCategoryFromServer(updatedParent, { clearEditMode: editModeStep === "hierarchy" });
      const nextSubcategories = savedSubs.length ? savedSubs : [createSubcategoryGroupDraft()];
      setSubcategories(nextSubcategories);
      setHierarchyFieldErrors({});
      fetchItems();
      return { success: true, category: updatedParent };
    } catch (error) {
      setHierarchyError(error?.message || "Kategori güncellenemedi.");
      return { success: false };
    }
  };

  const normalizeDynamicOptions = () => {
    const base = Array.isArray(dynamicDraft.options) ? dynamicDraft.options : [];
    const pending = (dynamicDraft.optionInput || "").trim();
    const merged = pending ? [...base, pending] : [...base];
    const cleaned = merged.map((opt) => opt.trim()).filter(Boolean);
    return Array.from(new Set(cleaned));
  };

  const handleDynamicOptionAdd = () => {
    const value = (dynamicDraft.optionInput || "").trim();
    if (!value) return;
    setDynamicDraft((prev) => {
      const existing = Array.isArray(prev.options) ? prev.options : [];
      if (existing.includes(value)) {
        return { ...prev, optionInput: "" };
      }
      return { ...prev, optionInput: "", options: [...existing, value] };
    });
  };

  const handleDynamicOptionRemove = (index) => {
    setDynamicDraft((prev) => ({
      ...prev,
      options: (prev.options || []).filter((_, i) => i !== index),
    }));
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
    const options = (type === "select" || type === "radio") ? normalizeDynamicOptions() : [];
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
      options,
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
      optionInput: "",
      options: [],
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
      optionInput: "",
      options: Array.isArray(field.options) ? field.options : [],
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
    setDetailDraft((prev) => ({
      ...prev,
      options: [...(prev.options || []), value],
    }));
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
    if ((detailDraft.options || []).length === 0) {
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
      options: detailDraft.options || [],
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
      options: [],
      messages: { required: "", invalid: "" },
    });
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
      options: group.options || [],
      messages: { required: group.messages?.required || "", invalid: group.messages?.invalid || "" },
    });
    setDetailOptionInput("");
    setDetailError("");
  };

  const handleDetailRemove = (index) => {
    setSchema((prev) => ({
      ...prev,
      detail_groups: prev.detail_groups.filter((_, i) => i !== index),
    }));
  };

  const moveGroup = (fromIndex, toIndex) => {
    if (fromIndex === toIndex || fromIndex === null || toIndex === null) return;
    setSubcategories((prev) => reorderArray(prev, fromIndex, toIndex));
  };

  const moveChild = (groupIndex, fromIndex, toIndex) => {
    if (fromIndex === toIndex || fromIndex === null || toIndex === null) return;
    setSubcategories((prev) => updateNodeByPath(prev, [groupIndex], (node) => {
      const reordered = reorderArray(node.children || [], fromIndex, toIndex).map((child, idx) => ({
        ...child,
        sort_order: Number(child.sort_order || idx + 1),
      }));
      return { ...node, children: reordered };
    }));
  };

  const renderLevelColumns = () => (
    <div className="space-y-3" data-testid="categories-level-group-builder">
      <div className="text-sm font-semibold text-slate-900" data-testid="categories-level-group-builder-title">
        Alt Kategoriler
      </div>
      <div className="space-y-3" data-testid="categories-level-items-0">
        {subcategories.length === 0 ? (
          <div className="text-xs text-slate-500" data-testid="categories-level-empty-0">
            Alt kategori grubu yok.
          </div>
        ) : subcategories.map((group, groupIndex) => {
          const groupPath = [groupIndex];
          const groupChildrenError = hierarchyFieldErrors[`level-${groupIndex}-children`];
          const children = Array.isArray(group.children) && group.children.length > 0 ? group.children : [createSubcategoryDraft()];
          const isGroupLocked = isHierarchyLocked || Boolean(group.is_complete);

          return (
            <div
              key={`group-${groupIndex}`}
              className="rounded-md border border-slate-200 bg-white p-3 space-y-2"
              data-testid={`categories-level-item-0-${groupIndex}`}
              draggable={!isHierarchyLocked}
              onDragStart={() => setDraggingGroupIndex(groupIndex)}
              onDragOver={(event) => event.preventDefault()}
              onDrop={() => {
                moveGroup(draggingGroupIndex, groupIndex);
                setDraggingGroupIndex(null);
              }}
              onDragEnd={() => setDraggingGroupIndex(null)}
            >
              <div className="text-xs font-semibold text-slate-700" data-testid={`categories-level-item-label-0-${groupIndex}`}>
                {`${groupIndex + 1}. Grup`} <span className="text-slate-400">↕</span>
              </div>

              <div className="flex gap-3 overflow-x-auto pb-2" data-testid={`categories-level-items-1-group-${groupIndex}`}>
                {children.map((child, childIndex) => {
                  const childPath = [groupIndex, childIndex];
                  const childErrorKey = `level-${groupIndex}-${childIndex}`;
                  const childNameError = hierarchyFieldErrors[`${childErrorKey}-name`];
                  const childSlugError = hierarchyFieldErrors[`${childErrorKey}-slug`];
                  const childSortError = hierarchyFieldErrors[`${childErrorKey}-sort`];
                  const childInputsDisabled = isGroupLocked || child.is_complete;

                  return (
                    <div
                      key={`group-${groupIndex}-child-${childIndex}`}
                      className="min-w-[300px] rounded-md border border-slate-200 bg-slate-50 p-3 space-y-2"
                      data-testid={`categories-level-item-1-${childIndex}`}
                      draggable={!isGroupLocked}
                      onDragStart={() => setDraggingChild({ groupIndex, childIndex })}
                      onDragOver={(event) => event.preventDefault()}
                      onDrop={() => {
                        if (draggingChild && draggingChild.groupIndex === groupIndex) {
                          moveChild(groupIndex, draggingChild.childIndex, childIndex);
                        }
                        setDraggingChild(null);
                      }}
                      onDragEnd={() => setDraggingChild(null)}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="text-xs font-semibold text-slate-700" data-testid={`categories-level-item-label-1-${childIndex}`}>
                          {`${groupIndex + 1}.${childIndex + 1} Kategori`} <span className="text-slate-400">↕</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {child.is_complete ? (
                            <span className="text-[11px] font-semibold text-emerald-600">Tamamlandı</span>
                          ) : (
                            <span className="text-[11px] font-semibold text-amber-600">Taslak</span>
                          )}
                        </div>
                      </div>

                      <input
                        className={inputClassName}
                        placeholder={`${groupIndex + 1}.${childIndex + 1} Ad`}
                        value={child.name}
                        disabled={childInputsDisabled}
                        onChange={(e) => setSubcategories((prev) => updateNodeByPath(prev, childPath, (node) => ({ ...node, name: e.target.value })))}
                        data-testid={`categories-level-item-name-1-${childIndex}`}
                      />
                      {childNameError ? <div className="text-[11px] text-rose-600">{childNameError}</div> : null}

                      <input
                        className={inputClassName}
                        placeholder={`${groupIndex + 1}.${childIndex + 1} Slug`}
                        value={child.slug}
                        disabled={childInputsDisabled}
                        onChange={(e) => setSubcategories((prev) => updateNodeByPath(prev, childPath, (node) => ({ ...node, slug: e.target.value })))}
                        data-testid={`categories-level-item-slug-1-${childIndex}`}
                      />
                      {childSlugError ? <div className="text-[11px] text-rose-600">{childSlugError}</div> : null}

                      <input
                        type="number"
                        min={1}
                        className={inputClassName}
                        placeholder="Sıra"
                        value={child.sort_order || ""}
                        disabled={childInputsDisabled}
                        onChange={(e) => setSubcategories((prev) => updateNodeByPath(prev, childPath, (node) => ({ ...node, sort_order: e.target.value })))}
                        data-testid={`categories-level-item-sort-1-${childIndex}`}
                      />
                      {childSortError ? <div className="text-[11px] text-rose-600">{childSortError}</div> : null}

                      <label className="flex items-center gap-2 text-xs text-slate-700" data-testid={`categories-level-item-active-1-${childIndex}`}>
                        <input
                          type="checkbox"
                          checked={child.active_flag}
                          disabled={childInputsDisabled}
                          onChange={(e) => setSubcategories((prev) => updateNodeByPath(prev, childPath, (node) => ({ ...node, active_flag: e.target.checked })))}
                          data-testid={`categories-level-item-active-input-1-${childIndex}`}
                        />
                        Aktif
                      </label>

                      <div className="flex flex-wrap items-center gap-2">
                        {!child.is_complete ? (
                          <button
                            type="button"
                            className="text-xs text-white bg-[var(--brand-navy-deep)] rounded px-3 py-1 disabled:opacity-60"
                            onClick={() => completeSubcategory(childPath)}
                            disabled={isGroupLocked}
                            data-testid={`categories-level-item-complete-1-${childIndex}`}
                          >
                            Tamam
                          </button>
                        ) : (
                          <button
                            type="button"
                            className="text-xs border rounded px-2 py-1"
                            onClick={() => setSubcategories((prev) => updateNodeByPath(prev, childPath, (node) => ({ ...node, is_complete: false })))}
                            data-testid={`categories-level-item-edit-1-${childIndex}`}
                          >
                            Düzenle
                          </button>
                        )}
                        {!child.is_complete ? (
                          <button
                            type="button"
                            className="text-xs text-rose-600 border rounded px-2 py-1 disabled:opacity-60"
                            onClick={() => setSubcategories((prev) => updateNodeByPath(prev, groupPath, (node) => ({
                              ...node,
                              children: (node.children || []).filter((_, idx) => idx !== childIndex),
                            })))}
                            disabled={isGroupLocked}
                            data-testid={`categories-level-item-remove-1-${childIndex}`}
                          >
                            Sil
                          </button>
                        ) : null}
                      </div>
                    </div>
                  );
                })}
              </div>

              <button
                type="button"
                className="w-full text-sm border rounded px-3 py-2 disabled:opacity-60"
                onClick={() => setSubcategories((prev) => updateNodeByPath(prev, groupPath, (node) => ({
                  ...node,
                  children: [...(node.children || []), createSubcategoryDraft()],
                })))}
                disabled={isGroupLocked}
                data-testid={`categories-level-add-1-${groupIndex}`}
              >
                Alt Kategori Ekle
              </button>

              {groupChildrenError ? <div className="text-[11px] text-rose-600">{groupChildrenError}</div> : null}

              <div className="flex flex-wrap items-center gap-2">
                {!group.is_complete ? (
                  <button
                    type="button"
                    className="text-xs text-white bg-[var(--brand-navy-deep)] rounded px-3 py-1 disabled:opacity-60"
                    onClick={() => completeSubcategory(groupPath)}
                    disabled={isHierarchyLocked}
                    data-testid={`categories-level-item-complete-0-${groupIndex}`}
                  >
                    {`${groupIndex + 1}. Grubu Tamamla`}
                  </button>
                ) : (
                  <button
                    type="button"
                    className="text-xs border rounded px-2 py-1"
                    onClick={() => setSubcategories((prev) => updateNodeByPath(prev, groupPath, (node) => ({ ...node, is_complete: false })))}
                    data-testid={`categories-level-item-edit-0-${groupIndex}`}
                  >
                    Düzenle
                  </button>
                )}
                {!group.is_complete ? (
                  <button
                    type="button"
                    className="text-xs text-rose-600 border rounded px-2 py-1 disabled:opacity-60"
                    onClick={() => setSubcategories((prev) => prev.filter((_, idx) => idx !== groupIndex))}
                    disabled={isHierarchyLocked}
                    data-testid={`categories-level-item-remove-0-${groupIndex}`}
                  >
                    Grubu Sil
                  </button>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>

      <button
        type="button"
        className="w-full text-sm border rounded px-3 py-2 disabled:opacity-60"
        onClick={() => setSubcategories((prev) => [...prev, createSubcategoryGroupDraft()])}
        disabled={isHierarchyLocked}
        data-testid="categories-level-add-0"
      >
        Yeni Grup Ekle
      </button>
    </div>
  );

  const hierarchyPreviewNodes = subcategories
    .map((group, groupIndex) => ({
      key: `group-${groupIndex}`,
      label: `${groupIndex + 1}`,
      children: (group.children || []).map((child, childIndex) => {
        const missing = !child?.name?.trim() || !child?.slug?.trim() || !Number.isFinite(Number(child?.sort_order)) || Number(child?.sort_order) <= 0;
        return {
          key: `${groupIndex}-${childIndex}`,
          label: `${groupIndex + 1}.${childIndex + 1} ${child?.name?.trim() || "(eksik ad)"}`,
          missing,
        };
      }),
    }))
    .filter((group) => group.children.length > 0);

  const modalPanelStyle = isModalFullscreen
    ? { width: "100vw", height: "100vh", maxWidth: "100vw", maxHeight: "100vh" }
    : {
      width: `${modalSize.width}px`,
      height: `${modalSize.height}px`,
      maxWidth: "95vw",
      maxHeight: "92vh",
      resize: "both",
      overflow: "auto",
    };



  return (
    <div className="p-6" data-testid="admin-categories-page">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Kategoriler</h1>
          <p className="text-sm text-slate-700">İlan form şablonlarını yönetin.</p>
        </div>
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded"
          onClick={handleCreate}
          data-testid="categories-create-open"
        >
          Yeni Kategori
        </button>
      </div>

      <div className="bg-white border rounded-lg text-slate-900">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3 bg-gray-50" data-testid="categories-list-filters-wrap">
          <div className="flex flex-wrap items-center gap-2" data-testid="categories-list-filters">
            <div className="flex flex-wrap items-center gap-1" data-testid="categories-list-filter-module">
              {[{ value: "all", label: "Tüm Modüller" }, ...CATEGORY_MODULE_OPTIONS].map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setListFilters((prev) => ({ ...prev, module: option.value }))}
                  className={`h-9 rounded-md border px-3 text-sm ${listFilters.module === option.value ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
                  data-testid={`categories-list-filter-module-${option.value}`}
                >
                  {option.label}
                </button>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-1" data-testid="categories-list-filter-status">
              {[
                { value: 'all', label: 'Tüm Durumlar' },
                { value: 'active', label: 'Aktif' },
                { value: 'passive', label: 'Pasif' },
              ].map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setListFilters((prev) => ({ ...prev, status: option.value }))}
                  className={`h-9 rounded-md border px-3 text-sm ${listFilters.status === option.value ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
                  data-testid={`categories-list-filter-status-${option.value}`}
                >
                  {option.label}
                </button>
              ))}
            </div>

            <div className="flex flex-wrap items-center gap-1" data-testid="categories-list-filter-image-presence">
              {[
                { value: 'all', label: 'Tüm Görsel Durumları' },
                { value: 'with_image', label: 'Görselli' },
                { value: 'without_image', label: 'Görselsiz' },
              ].map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setListFilters((prev) => ({ ...prev, image_presence: option.value }))}
                  className={`h-9 rounded-md border px-3 text-sm ${listFilters.image_presence === option.value ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
                  data-testid={`categories-list-filter-image-presence-${option.value}`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <div className="text-xs text-slate-600" data-testid="categories-list-selection-meta">
            Seçili: <span className="font-semibold" data-testid="categories-list-selection-count">{selectedIds.length}</span> •
            Görünen: <span className="font-semibold" data-testid="categories-list-visible-count">{visibleItems.length}</span>
          </div>
        </div>

        {bulkJob && (
          <div className="border-b px-4 py-2 text-xs bg-slate-50" data-testid="categories-bulk-job-panel">
            <div className="font-semibold text-slate-700" data-testid="categories-bulk-job-id">Job: {bulkJob.job_id}</div>
            <div className="text-slate-600" data-testid="categories-bulk-job-status">
              Durum: {bulkJob.status} • İşlenen: {bulkJob.processed_records || 0}/{bulkJob.total_records || 0}
            </div>
            {bulkJob.error_code && (
              <div className="text-rose-600" data-testid="categories-bulk-job-error">
                {bulkJob.error_code}: {bulkJob.error_message || '-'}
              </div>
            )}
          </div>
        )}

        {selectedIds.length > 0 && (
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-amber-200 bg-amber-50 px-4 py-3" data-testid="categories-bulk-actions-bar">
            <div className="text-sm font-medium text-amber-800" data-testid="categories-bulk-actions-summary">
              {selectedIds.length} kayıt seçildi (aktif filtre kapsamı)
            </div>
            <div className="flex flex-wrap items-center gap-2" data-testid="categories-bulk-actions-buttons">
              <button
                type="button"
                className="rounded border px-3 py-1.5 text-sm"
                disabled={bulkRunning}
                onClick={() => executeBulkAction("activate")}
                data-testid="categories-bulk-activate"
              >
                Seçilenleri Aktif Et
              </button>
              <button
                type="button"
                className="rounded border px-3 py-1.5 text-sm"
                disabled={bulkRunning}
                onClick={() => executeBulkAction("deactivate")}
                data-testid="categories-bulk-deactivate"
              >
                Seçilenleri Pasif Et
              </button>
              <button
                type="button"
                className="rounded border border-rose-300 px-3 py-1.5 text-sm text-rose-700"
                disabled={bulkRunning}
                onClick={openBulkDeleteConfirm}
                data-testid="categories-bulk-delete"
              >
                Seçilenleri Sil
              </button>
            </div>
          </div>
        )}

        <div className="grid grid-cols-[40px_72px_1.2fr_1fr_0.7fr_0.8fr_0.6fr_0.7fr_1.5fr] text-xs font-semibold uppercase px-4 py-2 border-b bg-gray-50 text-slate-800" data-testid="categories-list-header-row">
          <div>
            <TriStateCheckbox
              checked={allVisibleSelected}
              indeterminate={someVisibleSelected && !allVisibleSelected}
              onChange={(event) => toggleAllVisibleSelection(event.target.checked)}
              disabled={visibleItems.length === 0}
              testId="categories-select-all-checkbox"
            />
          </div>
          <div data-testid="categories-list-col-image">Görsel</div>
          <div>Ad</div>
          <div>Slug</div>
          <div>Ülke</div>
          <div>Modül</div>
          <div>Sıra</div>
          <div>Durum</div>
          <div className="text-right">Aksiyon</div>
        </div>
        {loading ? (
          <div className="p-4 text-sm text-slate-800" data-testid="categories-loading">Yükleniyor...</div>
        ) : visibleItems.length === 0 ? (
          <div className="p-4 text-sm text-slate-800" data-testid="categories-empty">Kayıt yok.</div>
        ) : (
          visibleItems.map((item) => {
            const rowSelection = getItemSelectionState(item.id);
            return (
              <div key={item.id} className="grid grid-cols-[40px_72px_1.2fr_1fr_0.7fr_0.8fr_0.6fr_0.7fr_1.5fr] px-4 py-3 border-b text-sm items-center text-slate-900" data-testid={`categories-row-${item.id}`}>
                <div>
                  <TriStateCheckbox
                    checked={rowSelection.checked}
                    indeterminate={rowSelection.indeterminate}
                    onChange={(event) => toggleItemSelection(item, event.target.checked)}
                    testId={`categories-row-select-${item.id}`}
                  />
                </div>
                <div className="pr-2" data-testid={`categories-row-image-cell-${item.id}`}>
                  <div className="h-10 w-10 overflow-hidden rounded border border-slate-200 bg-slate-100" data-testid={`categories-row-image-box-${item.id}`}>
                    {item.image_url ? (
                      <img
                        src={resolveCategoryImagePreviewUrl(item.image_url, item.updated_at ? Date.parse(item.updated_at) : item.id)}
                        alt={`${item.name || 'Kategori'} görseli`}
                        className="h-full w-full object-cover"
                        data-testid={`categories-row-image-preview-${item.id}`}
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-[10px] font-semibold text-slate-500" data-testid={`categories-row-image-placeholder-${item.id}`}>
                        —
                      </div>
                    )}
                  </div>
                </div>
                <div className="font-semibold text-slate-900" style={{ paddingLeft: `${Math.min(Number(item.depth || 0), 5) * 12}px` }} data-testid={`categories-row-name-${item.id}`}>{item.name}</div>
                <div className="text-slate-800" data-testid={`categories-row-slug-${item.id}`}>{item.slug}</div>
                <div className="text-slate-800" data-testid={`categories-row-country-${item.id}`}>{item.country_code || "global"}</div>
                <div className="text-slate-800" data-testid={`categories-row-module-${item.id}`}>{item.module || '-'}</div>
                <div className="text-slate-800" data-testid={`categories-row-sort-${item.id}`}>{item.sort_order}</div>
                <div>
                  <span className={`px-2 py-1 rounded text-xs ${item.active_flag ? "bg-green-100 text-green-700" : "bg-gray-100 text-slate-800"}`} data-testid={`categories-row-status-${item.id}`}>
                    {item.active_flag ? "Aktif" : "Pasif"}
                  </span>
                </div>
                <div className="flex justify-end gap-2 text-slate-900" data-testid={`categories-row-actions-${item.id}`}>
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
            );
          })
        )}
      </div>

      {modalOpen && (
        <div className={`fixed inset-0 bg-black/40 z-50 ${isModalFullscreen ? '' : 'flex items-center justify-center'}`} data-testid="categories-modal">
          <div className={`bg-white p-6 text-slate-900 ${isModalFullscreen ? '' : 'rounded-lg shadow-xl'}`} style={modalPanelStyle} data-testid="categories-modal-panel">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">{editing ? "Kategori Düzenle" : "Yeni Kategori"}</h2>
              <div className="flex items-center gap-2">
                {!isModalFullscreen ? (
                  <button
                    type="button"
                    onClick={() => setModalSize({ width: 1280, height: 820 })}
                    className="rounded border px-2 py-1 text-xs"
                    data-testid="categories-modal-size-reset"
                  >
                    Boyutu Sıfırla
                  </button>
                ) : null}
                <button
                  type="button"
                  onClick={() => setIsModalFullscreen((prev) => !prev)}
                  className="rounded border px-2 py-1 text-xs"
                  data-testid="categories-modal-toggle-fullscreen"
                >
                  {isModalFullscreen ? 'Normal' : 'Tam Ekran'}
                </button>
                <button onClick={() => setModalOpen(false)} data-testid="categories-modal-close">✕</button>
              </div>
            </div>

            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex flex-wrap gap-2" data-testid="category-wizard-steps">
                  {WIZARD_STEPS.map((step) => {
                    const active = wizardStep === step.id;
                    const disabled = !canAccessStep(step.id);
                    const tooltip = disabled ? "Önce bu adımı tamamlayın." : "";
                    const dirty = isStepDirty(step.id);
                    const completed = isStepCompleted(step.id);
                    return (
                      <div key={step.id} className="flex items-center gap-1" data-testid={`category-step-wrap-${step.id}`}>
                        <button
                          type="button"
                          onClick={() => {
                            if (disabled) {
                              setHierarchyError("Önce bu adımı tamamlayın.");
                              return;
                            }
                            setHierarchyError("");
                            setWizardStep(step.id);
                          }}
                          aria-disabled={disabled}
                          className={`px-3 py-1 rounded text-xs border ${active ? 'bg-slate-900 text-white' : 'bg-white text-slate-700'} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
                          title={dirty ? "Bu adım yeniden tamamlanmalı." : tooltip}
                          data-testid={`category-step-${step.id}`}
                        >
                          {step.label}
                          {dirty && (
                            <span className="ml-1 text-rose-300" data-testid={`category-step-dirty-${step.id}`}>●</span>
                          )}
                        </button>
                        {canEditUnlock && editing && completed && !dirty && (
                          <button
                            type="button"
                            className="px-2 py-1 text-[11px] border rounded text-slate-600"
                            onClick={() => handleUnlockStep(step.id)}
                            data-testid={`category-step-edit-${step.id}`}
                          >
                            Edit
                          </button>
                        )}
                      </div>
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

              {editModeActive && dirtySteps.length > 0 && (
                <div className="p-3 rounded border border-amber-200 bg-amber-50 text-amber-700 text-sm flex flex-wrap items-center justify-between gap-3" data-testid="categories-step-dirty-warning">
                  <span data-testid="categories-step-dirty-message">
                    Bu adım yeniden tamamlanmalı. Değişiklikler downstream adımları da etkiledi.
                  </span>
                  {firstDirtyStep && (
                    <button
                      type="button"
                      onClick={handleDirtyCta}
                      className="text-xs font-semibold text-amber-800 border border-amber-300 rounded px-3 py-1 bg-amber-100"
                      data-testid="categories-step-dirty-cta"
                    >
                      Sıradaki eksik adımı tamamla
                    </button>
                  )}
                </div>
              )}

              {wizardStep === "hierarchy" && (
                <div className="space-y-4" data-testid="category-hierarchy-step">
                  <div className="rounded-lg border p-4 space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-md font-semibold">Ana Kategori</h3>
                      {isHierarchyLocked && (
                        <button
                          type="button"
                          className="text-xs border rounded px-2 py-1"
                          onClick={handleHierarchyEdit}
                          data-testid="categories-hierarchy-edit"
                        >
                          Düzenle
                        </button>
                      )}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <label className={labelClassName}>Ana kategori adı</label>
                        <input
                          className={inputClassName}
                          value={form.name}
                          disabled={isHierarchyLocked}
                          onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                          data-testid="categories-name-input"
                        />
                        {hierarchyFieldErrors.main_name && (
                          <div className="text-xs text-rose-600" data-testid="categories-name-error">
                            {hierarchyFieldErrors.main_name}
                          </div>
                        )}
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Slug</label>
                        <input
                          className={inputClassName}
                          value={form.slug}
                          disabled={isHierarchyLocked}
                          onChange={(e) => setForm((prev) => ({ ...prev, slug: e.target.value }))}
                          data-testid="categories-slug-input"
                        />
                        {hierarchyFieldErrors.main_slug && (
                          <div className="text-xs text-rose-600" data-testid="categories-slug-error">
                            {hierarchyFieldErrors.main_slug}
                          </div>
                        )}
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Ülke</label>
                        <input
                          className={inputClassName}
                          value={form.country_code}
                          disabled={isHierarchyLocked}
                          onChange={(e) => setForm((prev) => ({ ...prev, country_code: e.target.value.toUpperCase() }))}
                          data-testid="categories-country-input"
                        />
                        {hierarchyFieldErrors.main_country && (
                          <div className="text-xs text-rose-600" data-testid="categories-country-error">
                            {hierarchyFieldErrors.main_country}
                          </div>
                        )}
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Modül</label>
                        <select
                          className={selectClassName}
                          value={form.module}
                          disabled={isHierarchyLocked}
                          onChange={(e) => {
                            const nextModule = e.target.value;
                            setForm((prev) => ({ ...prev, module: nextModule }));
                            setHierarchyFieldErrors((prev) => {
                              const next = { ...prev };
                              delete next.main_module;
                              delete next.main_sort_order;
                              return next;
                            });
                            if (nextModule !== "vehicle") {
                              setVehicleSegment("");
                              setVehicleSegmentError("");
                            }
                          }}
                          data-testid="categories-module-select"
                        >
                          <option value="">Seçiniz</option>
                          <option value="real_estate">Emlak</option>
                          <option value="vehicle">Vasıta</option>
                          <option value="other">Diğer</option>
                        </select>
                        {hierarchyFieldErrors.main_module && (
                          <div className="text-xs text-rose-600" data-testid="categories-module-error">
                            {hierarchyFieldErrors.main_module}
                          </div>
                        )}
                        {form.module === 'vehicle' && (
                          <div className="rounded-md border border-amber-200 bg-amber-50 p-2 text-xs text-amber-700" data-testid="categories-vehicle-note">
                            Vasıta akışında kategori yerine segment seçilir ve master data bağlantısı zorunludur.
                          </div>
                        )}
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Sıra</label>
                        <input
                          type="number"
                          min={1}
                          className={inputClassName}
                          value={form.sort_order || ''}
                          disabled={isHierarchyLocked}
                          onChange={(e) => {
                            setForm((prev) => ({ ...prev, sort_order: e.target.value }));
                            setHierarchyFieldErrors((prev) => {
                              const next = { ...prev };
                              delete next.main_sort_order;
                              return next;
                            });
                          }}
                          data-testid="categories-sort-input"
                        />
                        {hierarchyFieldErrors.main_sort_order && (
                          <div className="text-xs text-rose-600" data-testid="categories-sort-error">
                            {hierarchyFieldErrors.main_sort_order}
                          </div>
                        )}
                        {!hierarchyFieldErrors.main_sort_order && !orderPreview.available && (
                          <div className="text-xs text-rose-600" data-testid="categories-sort-conflict-inline">
                            {orderPreview.message || "Bu modül ve seviye içinde bu sıra numarası zaten kullanılıyor."}
                          </div>
                        )}
                        {!hierarchyFieldErrors.main_sort_order && !orderPreview.available && orderPreview.suggested_next_sort_order && (
                          <div className="flex items-center gap-2 text-[11px] text-emerald-700" data-testid="categories-sort-suggested-next">
                            <span>Önerilen boş sıra: {orderPreview.suggested_next_sort_order}</span>
                            <button
                              type="button"
                              className="rounded border border-emerald-300 px-2 py-0.5 text-[11px] font-semibold"
                              onClick={() => setForm((prev) => ({ ...prev, sort_order: String(orderPreview.suggested_next_sort_order) }))}
                              data-testid="categories-sort-apply-suggestion"
                            >
                              Uygula
                            </button>
                          </div>
                        )}
                        {orderPreview.checking && (
                          <div className="text-[11px] text-slate-500" data-testid="categories-sort-preview-loading">
                            Sıra çakışma önizlemesi kontrol ediliyor...
                          </div>
                        )}
                      </div>
                      <div className="space-y-2 md:col-span-2" data-testid="categories-image-section">
                        <label className={labelClassName}>Ana kategori görseli</label>
                        {isRootCategory ? (
                          <div className="rounded-md border border-dashed border-slate-300 p-3 space-y-3" data-testid="categories-image-root-uploader">
                            <div className="flex flex-wrap items-center gap-3" data-testid="categories-image-preview-wrap">
                              <div className="h-20 w-20 overflow-hidden rounded-md border border-slate-200 bg-slate-100" data-testid="categories-image-preview-container">
                                {categoryImagePreviewUrl ? (
                                  <img
                                    src={categoryImagePreviewUrl}
                                    alt="Kategori görseli önizleme"
                                    className="h-full w-full object-cover"
                                    data-testid="categories-image-preview"
                                  />
                                ) : (
                                  <div className="flex h-full w-full items-center justify-center text-[11px] font-semibold text-slate-600" data-testid="categories-image-placeholder">
                                    Varsayılan ikon
                                  </div>
                                )}
                              </div>
                              <div className="text-xs text-slate-700" data-testid="categories-image-hint">
                                Dosya tipleri: png/jpg/webp • Maks: 2MB • 1:1 oranı center-crop uygulanır.
                              </div>
                            </div>
                            <div className="flex flex-wrap items-center gap-2" data-testid="categories-image-actions">
                              <label
                                className={`inline-flex h-9 cursor-pointer items-center rounded-md border border-slate-300 px-3 text-sm font-medium text-slate-900 ${isHierarchyLocked ? "cursor-not-allowed opacity-60" : ""}`}
                                data-testid="categories-image-upload-trigger"
                              >
                                <input
                                  type="file"
                                  accept="image/png,image/jpeg,image/webp"
                                  className="hidden"
                                  disabled={isHierarchyLocked || categoryImageUploading}
                                  onChange={handleCategoryImageUpload}
                                  data-testid="categories-image-upload-input"
                                />
                                {categoryImagePreviewUrl ? "Değiştir" : "Görsel Yükle"}
                              </label>
                              <button
                                type="button"
                                className="h-9 rounded-md border border-slate-300 px-3 text-sm font-medium text-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
                                onClick={handleCategoryImageRemove}
                                disabled={isHierarchyLocked || !form.image_url}
                                data-testid="categories-image-remove-button"
                              >
                                Kaldır
                              </button>
                            </div>
                            {form.image_url && (
                              <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700" data-testid="categories-image-meta">
                                <div data-testid="categories-image-meta-format">
                                  Format: {String(form.image_url).split(".").pop()?.split("?")[0]?.toUpperCase() || "WEBP"}
                                </div>
                                <div data-testid="categories-image-meta-updated">
                                  Son Güncelleme: {editing?.updated_at ? new Date(editing.updated_at).toLocaleString("tr-TR") : (lastSavedAt || "-")}
                                </div>
                              </div>
                            )}
                            {categoryImageUploading && (
                              <div className="text-xs text-slate-600" data-testid="categories-image-uploading">
                                Görsel yükleniyor...
                              </div>
                            )}
                            {categoryImageError && (
                              <div className="text-xs text-rose-600" data-testid="categories-image-error">
                                {categoryImageError}
                              </div>
                            )}
                            {hierarchyFieldErrors.main_image_url && (
                              <div className="text-xs text-rose-600" data-testid="categories-image-required-error">
                                {hierarchyFieldErrors.main_image_url}
                              </div>
                            )}
                          </div>
                        ) : (
                          <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700" data-testid="categories-image-root-only-note">
                            Alt kategorilerde görsel alanı kapalıdır.
                          </div>
                        )}
                      </div>

                      <label className="flex items-center gap-2 text-sm text-slate-800" data-testid="categories-active-wrapper">
                        <input
                          type="checkbox"
                          checked={form.active_flag}
                          disabled={isHierarchyLocked}
                          onChange={(e) => setForm((prev) => ({ ...prev, active_flag: e.target.checked }))}
                          data-testid="categories-active-checkbox"
                        />
                        Aktif
                      </label>
                    </div>
                  </div>

                  {form.module === 'vehicle' ? (
                    <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 space-y-3" data-testid="categories-vehicle-subcategory-lock">
                      <div className="text-xs text-amber-700" data-testid="categories-vehicle-segment-hint">
                        Vasıta modülünde alt kategori ağacı açılmaz. Segment seçimi master data sistemine bağlanır.
                      </div>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3" data-testid="categories-vehicle-segment-grid">
                        <div className="space-y-1">
                          <label className={labelClassName}>Segment (Serbest Metin)</label>
                          <input
                            className={inputClassName}
                            value={vehicleSegment}
                            disabled={isHierarchyLocked}
                            onChange={(e) => {
                              setVehicleSegment(e.target.value);
                              setVehicleSegmentError("");
                            }}
                            placeholder="Örn: Otomobil"
                            data-testid="categories-vehicle-segment-select"
                          />
                          {vehicleSegmentError && (
                            <div className="text-xs text-rose-600" data-testid="categories-vehicle-segment-error">
                              {vehicleSegmentError}
                            </div>
                          )}
                        </div>
                        <div className="rounded-md border border-amber-300 bg-white/70 px-3 py-2 text-xs" data-testid="categories-vehicle-link-status">
                          <div className="flex items-center justify-between gap-2" data-testid="categories-vehicle-link-status-title-row">
                            <div className="font-semibold text-amber-900" data-testid="categories-vehicle-link-status-title">
                              Master Data Linked
                            </div>
                            {vehicleLinkStatus.linked && (
                              <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-700" data-testid="categories-vehicle-linked-badge">
                                Master Data Linked
                              </span>
                            )}
                          </div>
                          <div
                            className={`mt-1 ${vehicleLinkStatus.linked ? 'text-emerald-700' : 'text-amber-800'}`}
                            data-testid="categories-vehicle-link-status-message"
                          >
                            {vehicleLinkStatus.checking ? 'Kontrol ediliyor...' : (vehicleLinkStatus.message || 'Segment adı giriniz.')}
                          </div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-lg border p-4 space-y-3" data-testid="categories-subcategory-section">
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h3 className="text-md font-semibold">Alt Kategoriler</h3>
                          <p className="text-xs text-slate-600" data-testid="categories-subcategory-hint">
                            1.1 ile başlayın; 1. grup bitince otomatik 2. grup açılır. Her grupta 1.x / 2.x / 3.x alt kategorileri sınırsız ekleyebilirsiniz.
                          </p>
                        </div>
                      </div>
                      {subcategories.length === 0 ? (
                        <div className="text-sm text-slate-700" data-testid="categories-subcategory-empty">Henüz alt kategori başlatılmadı.</div>
                      ) : (
                        <div className="flex gap-4 overflow-x-auto pb-2" data-testid="categories-subcategory-levels">
                          {renderLevelColumns()}
                        </div>
                      )}
                      <div className="rounded-md border border-dashed border-slate-300 bg-white p-3" data-testid="categories-hierarchy-live-preview">
                        <div className="mb-2 text-xs font-semibold text-slate-700">Canlı Hiyerarşi Önizleme</div>
                        {hierarchyPreviewNodes.length === 0 ? (
                          <div className="text-xs text-slate-500" data-testid="categories-hierarchy-live-preview-empty">
                            Önizleme için grup ve alt kategori ekleyin.
                          </div>
                        ) : (
                          <div className="space-y-2" data-testid="categories-hierarchy-live-preview-tree">
                            {hierarchyPreviewNodes.map((group) => (
                              <div key={group.key} className="rounded-md border border-slate-200 bg-slate-50 px-2 py-1" data-testid={`categories-hierarchy-live-preview-group-${group.key}`}>
                                <div className="flex items-center gap-2 text-xs font-semibold text-slate-900">
                                  <span>{group.label}</span>
                                  {group.children.some((child) => child.missing) ? (
                                    <span className="rounded-full bg-rose-100 px-2 py-0.5 text-[10px] text-rose-700" data-testid={`categories-hierarchy-live-preview-group-missing-${group.key}`}>
                                      Eksik alan var
                                    </span>
                                  ) : (
                                    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] text-emerald-700" data-testid={`categories-hierarchy-live-preview-group-ok-${group.key}`}>
                                      Tamam
                                    </span>
                                  )}
                                </div>
                                {group.children.length > 0 ? (
                                  <ul className="mt-1 space-y-1 pl-4 text-xs text-slate-700" data-testid={`categories-hierarchy-live-preview-children-${group.key}`}>
                                    {group.children.map((child) => (
                                      <li key={child.key} className={child.missing ? "text-rose-600" : ""}>{child.label}</li>
                                    ))}
                                  </ul>
                                ) : (
                                  <div className="mt-1 text-[11px] text-amber-600">Bu grup için alt kategori bekleniyor.</div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {editing && (
                    <div className="rounded-lg border border-dashed p-4 text-sm text-slate-700" data-testid="categories-hierarchy-locked">
                      Mevcut kategori üzerinde kategori düzenleme devre dışı. Devam ederek form şemasını güncelleyebilirsiniz.
                    </div>
                  )}

                  <div className="text-xs text-slate-700" data-testid="categories-hierarchy-warning">
                    Kategori tamamlanmadan çekirdek alanlara geçilemez.
                  </div>
                </div>
              )}

              {wizardStep !== "hierarchy" && (
                <div className="space-y-4" data-testid="categories-step-content">
                  <div className="rounded-lg border p-4 text-sm" data-testid="categories-summary">
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                      <div>
                        <div className="text-xs text-slate-700">Ana Kategori</div>
                        <div className="font-medium">{form.name || '-'}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-700">Slug</div>
                        <div className="font-medium">{form.slug || '-'}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-700">Ülke</div>
                        <div className="font-medium">{form.country_code || '-'}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-700">Durum</div>
                        <div className="font-medium">{form.active_flag ? 'Aktif' : 'Pasif'}</div>
                      </div>
                    </div>
                    <div className="mt-2 text-xs text-slate-700" data-testid="categories-summary-sort-order">
                      Sıra: {form.sort_order || '-'}
                    </div>
                    <div className="mt-1 text-xs text-slate-700" data-testid="categories-summary-image-status">
                      Görsel: {form.image_url ? 'Yüklendi' : 'Varsayılan ikon'}
                    </div>
                    {form.module === 'vehicle' && (
                      <div className="mt-1 text-xs text-slate-700" data-testid="categories-summary-vehicle-segment">
                        Segment: {vehicleSegment || '-'}
                      </div>
                    )}
                  </div>

              {wizardStep === "core" && (
                <div className="border-t pt-4 space-y-6" data-testid="categories-core-step">
                  <h3 className="text-md font-semibold">Çekirdek Alanlar</h3>

                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-slate-700">Başlık</h4>
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
                          checked={schema.title_uniqueness.enabled}
                          onChange={(e) => setSchema((prev) => ({
                            ...prev,
                            title_uniqueness: { ...prev.title_uniqueness, enabled: e.target.checked },
                          }))}
                          data-testid="categories-title-unique-toggle"
                        />
                        Başlık benzersizliği
                      </label>
                    </div>

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

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div className="space-y-1">
                        <label className={labelClassName}>Başlık min</label>
                        <input
                          type="number"
                          min={0}
                          max={200}
                          aria-label="Başlık min"
                          className={inputClassName}
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
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Başlık max</label>
                        <input
                          type="number"
                          min={0}
                          max={200}
                          aria-label="Başlık max"
                          className={inputClassName}
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
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Başlık custom rule (regex)</label>
                        <input
                          type="text"
                          className={inputClassName}
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
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
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
                        placeholder="Başlık custom mesaj"
                        value={schema.core_fields.title.messages.custom}
                        onChange={(e) => setSchema((prev) => ({
                          ...prev,
                          core_fields: {
                            ...prev.core_fields,
                            title: {
                              ...prev.core_fields.title,
                              messages: { ...prev.core_fields.title.messages, custom: e.target.value },
                            },
                          },
                        }))}
                        data-testid="categories-title-custom-message"
                      />
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-slate-700">Açıklama</h4>
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

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div className="space-y-1">
                        <label className={labelClassName}>Açıklama min</label>
                        <input
                          type="number"
                          min={0}
                          max={10000}
                          aria-label="Açıklama min"
                          className={inputClassName}
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
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Açıklama max</label>
                        <input
                          type="number"
                          min={0}
                          max={20000}
                          aria-label="Açıklama max"
                          className={inputClassName}
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
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Açıklama custom rule (regex)</label>
                        <input
                          type="text"
                          className={inputClassName}
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
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
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
                        placeholder="Açıklama custom mesaj"
                        value={schema.core_fields.description.messages.custom}
                        onChange={(e) => setSchema((prev) => ({
                          ...prev,
                          core_fields: {
                            ...prev.core_fields,
                            description: {
                              ...prev.core_fields.description,
                              messages: { ...prev.core_fields.description.messages, custom: e.target.value },
                            },
                          },
                        }))}
                        data-testid="categories-description-custom-message"
                      />
                    </div>
                  </div>

                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-slate-700">Fiyat</h4>
                    <label className="flex items-center gap-2 text-sm text-slate-800">
                      <input
                        type="checkbox"
                        checked={schema.core_fields.price.required}
                        onChange={(e) => setSchema((prev) => ({
                          ...prev,
                          core_fields: {
                            ...prev.core_fields,
                            price: { ...prev.core_fields.price, required: e.target.checked },
                          },
                        }))}
                        data-testid="categories-price-required"
                      />
                      Fiyat zorunlu
                    </label>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div className="space-y-1">
                        <label className={labelClassName}>Birincil para</label>
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
                      </div>
                      {schema.core_fields.price.secondary_enabled && (
                        <div className="space-y-1">
                          <label className={labelClassName}>İkincil para</label>
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
                        </div>
                      )}
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
                        İkincil para
                      </label>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <div className="space-y-1">
                        <label className={labelClassName}>Ondalık basamak</label>
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
                          <option value={1}>1 basamak</option>
                          <option value={2}>2 basamak</option>
                        </select>
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Min fiyat</label>
                        <input
                          type="number"
                          min={0}
                          aria-label="Min fiyat"
                          className={inputClassName}
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
                      </div>
                      <div className="space-y-1">
                        <label className={labelClassName}>Max fiyat</label>
                        <input
                          type="number"
                          min={0}
                          aria-label="Max fiyat"
                          className={inputClassName}
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
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
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
                  </div>
                </div>
              )}

              {wizardStep === "dynamic" && (
                <div className="border-t pt-4 space-y-4" data-testid="categories-dynamic-step">
                  <div className="flex items-center justify-between">
                    <h3 className="text-md font-semibold">Parametre Alanları (2a)</h3>
                    <span className="text-xs text-slate-700">Tek tek ekleme + Next</span>
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
                          onChange={(e) => setDynamicDraft((prev) => {
                            const nextType = e.target.value;
                            const isTextLike = ['text', 'number'].includes(nextType);
                            return {
                              ...prev,
                              type: nextType,
                              optionInput: isTextLike ? "" : prev.optionInput,
                              options: isTextLike ? [] : prev.options,
                            };
                          })}
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
                      <div className="space-y-2" data-testid="categories-dynamic-options-section">
                        <label className={labelClassName}>Seçenekler</label>
                        <div className="flex flex-wrap gap-2">
                          <input
                            className={`${inputClassName} flex-1 min-w-[200px]`}
                            value={dynamicDraft.optionInput}
                            onChange={(e) => setDynamicDraft((prev) => ({ ...prev, optionInput: e.target.value }))}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                e.preventDefault();
                                handleDynamicOptionAdd();
                              }
                            }}
                            placeholder="Yeni seçenek ekle"
                            data-testid="categories-dynamic-option-input"
                          />
                          <button
                            type="button"
                            className="px-3 py-2 border rounded text-sm"
                            onClick={handleDynamicOptionAdd}
                            data-testid="categories-dynamic-option-add"
                          >
                            Ekle
                          </button>
                        </div>
                        {dynamicDraft.options.length === 0 ? (
                          <div className="text-xs text-slate-600" data-testid="categories-dynamic-option-empty">Henüz seçenek eklenmedi.</div>
                        ) : (
                          <div className="flex flex-wrap gap-2" data-testid="categories-dynamic-option-list">
                            {dynamicDraft.options.map((opt, index) => (
                              <div
                                key={`${opt}-${index}`}
                                className="flex items-center gap-2 px-2 py-1 rounded bg-slate-100 text-xs text-slate-700"
                                data-testid={`categories-dynamic-option-${index}`}
                              >
                                <span>{opt}</span>
                                <button
                                  type="button"
                                  className="text-slate-600 hover:text-rose-600"
                                  onClick={() => handleDynamicOptionRemove(index)}
                                  data-testid={`categories-dynamic-option-remove-${index}`}
                                >
                                  ✕
                                </button>
                              </div>
                            ))}
                          </div>
                        )}
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
                          data-testid="categories-dynamic-draft-required-input"
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
                      <div className="text-sm text-slate-700" data-testid="categories-dynamic-empty">Henüz parametre alanı eklenmedi.</div>
                    ) : (
                      schema.dynamic_fields.map((field, index) => (
                        <div
                          key={field.id || field.key}
                          className="border rounded p-3 flex flex-wrap items-center gap-3"
                          data-testid={`categories-dynamic-item-${index}`}
                        >
                          <div className="flex-1 space-y-1">
                            <div className="font-medium" data-testid={`categories-dynamic-label-${index}`}>
                              {field.label} ({field.key})
                            </div>
                            <div className="text-xs text-slate-700" data-testid={`categories-dynamic-meta-${index}`}>
                              Tip: {field.type} · Sıra: {field.sort_order || 0} · {field.required ? 'Zorunlu' : 'Opsiyonel'}
                            </div>
                            {(field.options || []).length > 0 && (
                              <div className="text-xs text-slate-600" data-testid={`categories-dynamic-options-${index}`}>
                                Seçenekler: {(field.options || []).join(', ')}
                              </div>
                            )}
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
                    <span className="text-xs text-slate-700">Önce grup tanımı → checkbox listesi</span>
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
                        data-testid="categories-detail-draft-required-input"
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

                    {(detailDraft.options || []).length > 0 && (
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2" data-testid="categories-detail-options">
                        {(detailDraft.options || []).map((opt, index) => (
                          <div key={`${opt}-${index}`} className="flex items-center justify-between gap-2 border rounded px-2 py-1 text-xs" data-testid={`categories-detail-option-${index}`}>
                            <span className="truncate">{opt}</span>
                            <button
                              type="button"
                              className="text-rose-600"
                              onClick={() => setDetailDraft((prev) => ({
                                ...prev,
                                options: (prev.options || []).filter((_, i) => i !== index),
                              }))}
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
                      <div className="text-sm text-slate-700">Henüz detay grubu eklenmedi.</div>
                    ) : (
                      schema.detail_groups.map((group, index) => (
                        <div key={group.id || group.title} className="border rounded p-3 flex flex-wrap items-center gap-3">
                          <div className="flex-1">
                            <div className="font-medium">{group.title} ({group.id})</div>
                            <div className="text-xs text-slate-700">Seçenek: {group.options?.length || 0} · Sıra: {group.sort_order || 0}</div>
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
                        <div className="space-y-1">
                          <div className="font-medium" data-testid={`categories-module-label-${key}`}>{MODULE_LABELS[key] || key}</div>
                          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-700">
                            <span className="px-2 py-0.5 rounded-full bg-slate-100 text-slate-700" data-testid={`categories-module-key-${key}`}>{key}</span>
                            <span data-testid={`categories-module-source-${key}`}>Kaynak: schema.modules</span>
                          </div>
                        </div>
                        <input
                          type="checkbox"
                          checked={schema.modules[key].enabled}
                          onChange={(e) => handleModuleToggle(key, e.target.checked)}
                          data-testid={`categories-module-${key}`}
                        />
                      </div>
                    ))}
                  </div>

                  {isPhotosEnabled && (
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
                      <div className="text-xs text-slate-700">Önerilen aralık: 1–50</div>
                    </div>
                  )}

                  {isPaymentEnabled ? (
                    <div className="flex flex-wrap gap-4 text-sm" data-testid="categories-payment-options">
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
                  ) : (
                    <div className="text-xs text-slate-700" data-testid="categories-payment-options-collapsed">
                      Ödeme modülü kapalı. Paket/doping seçenekleri pasif.
                    </div>
                  )}

                </div>
              )}

              {wizardStep === "preview" && (
                <div className="border-t pt-4 space-y-4" data-testid="categories-preview-step">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h3 className="text-md font-semibold">Önizleme</h3>
                      <div className="text-xs text-slate-700" data-testid="categories-last-saved">
                        Son kaydetme: {lastSavedAt || "-"}
                      </div>
                    </div>
                    <span
                      className={`text-xs px-2 py-1 rounded ${previewComplete ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'}`}
                      data-testid="categories-preview-status"
                    >
                      {previewComplete ? 'Onaylandı' : 'Onay bekliyor'}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-2" data-testid="categories-export-actions">
                    <button
                      type="button"
                      className="px-3 py-2 border rounded text-sm text-slate-900"
                      onClick={() => handleExport('pdf')}
                      disabled={!editing?.id}
                      data-testid="categories-export-pdf"
                    >
                      PDF indir
                    </button>
                    <button
                      type="button"
                      className="px-3 py-2 border rounded text-sm text-slate-900"
                      onClick={() => handleExport('csv')}
                      disabled={!editing?.id}
                      data-testid="categories-export-csv"
                    >
                      CSV indir
                    </button>
                  </div>

                  <div className="rounded-lg border p-4 space-y-3" data-testid="categories-preview-summary">
                    <div className="grid grid-cols-1 md:grid-cols-5 gap-3 text-sm">
                      <div>
                        <div className="text-xs text-slate-700">Kategori</div>
                        <div className="font-medium" data-testid="categories-preview-name">{form.name || '-'}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-700">Slug</div>
                        <div className="font-medium" data-testid="categories-preview-slug">{form.slug || '-'}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-700">Ülke</div>
                        <div className="font-medium" data-testid="categories-preview-country">{form.country_code || '-'}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-700">Modül</div>
                        <div className="font-medium" data-testid="categories-preview-module">{form.module || '-'}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-700">Durum</div>
                        <div className="font-medium" data-testid="categories-preview-active">{form.active_flag ? 'Aktif' : 'Pasif'}</div>
                      </div>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                      <div>
                        <div className="text-xs text-slate-700">Parametre Alanı</div>
                        <div className="font-medium" data-testid="categories-preview-dynamic-count">{schema.dynamic_fields.length}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-700">Detay Grubu</div>
                        <div className="font-medium" data-testid="categories-preview-detail-count">{schema.detail_groups.length}</div>
                      </div>
                      <div>
                        <div className="text-xs text-slate-700">Aktif Modül</div>
                        <div className="font-medium" data-testid="categories-preview-module-count">
                          {Object.values(schema.modules || {}).filter((mod) => mod.enabled).length}
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="rounded-lg border p-4 space-y-2" data-testid="categories-preview-modules">
                    <div className="text-sm font-semibold">Modül Listesi</div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                      {Object.keys(schema.modules).map((key) => (
                        <div key={`preview-${key}`} className="flex items-center justify-between border rounded px-3 py-2" data-testid={`categories-preview-module-${key}`}>
                          <span>{MODULE_LABELS[key] || key}</span>
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full ${schema.modules[key].enabled ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-700'}`}
                            data-testid={`categories-preview-module-status-${key}`}
                          >
                            {schema.modules[key].enabled ? 'Aktif' : 'Kapalı'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="rounded-lg border p-4 space-y-2" data-testid="categories-preview-warnings">
                    <div className="text-sm font-semibold">Validation Uyarıları</div>
                    {publishValidation.errors.length > 0 ? (
                      <ul className="list-disc pl-5 space-y-1 text-sm text-amber-700">
                        {publishValidation.errors.map((err, index) => (
                          <li key={`preview-warning-${index}`} data-testid={`categories-preview-warning-${index}`}>
                            {err}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="text-sm text-emerald-700" data-testid="categories-preview-ready">Tüm kontroller tamam.</div>
                    )}
                  </div>

                  {publishError && (
                    <div className="p-2 rounded border border-rose-200 bg-rose-50 text-rose-700 text-sm" data-testid="categories-publish-error">
                      {publishError}
                    </div>
                  )}

                  <div className="flex flex-wrap items-center gap-3">
                    <button
                      type="button"
                      className={`px-4 py-2 rounded text-sm ${previewComplete ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-900 text-white'}`}
                      onClick={() => setPreviewComplete(true)}
                      disabled={previewComplete}
                      data-testid="categories-preview-confirm"
                    >
                      {previewComplete ? 'Önizleme Onaylandı' : 'Önizlemeyi Onayla'}
                    </button>
                    {previewComplete && (
                      <span className="text-xs text-emerald-700" data-testid="categories-preview-confirmed">Onay tamamlandı.</span>
                    )}
                  </div>

                  <details className="rounded-lg border p-4" data-testid="categories-preview-json">
                    <summary className="cursor-pointer text-sm font-semibold" data-testid="categories-preview-json-toggle">JSON şema (salt okunur / debug)</summary>
                    <div className="mt-3 space-y-2">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="text-xs text-slate-700" data-testid="categories-preview-json-hint">Salt okunur / debug amaçlı</span>
                        <button
                          type="button"
                          className="px-3 py-1 border rounded text-xs"
                          onClick={handleCopySchema}
                          data-testid="categories-preview-json-copy"
                        >
                          Kopyala
                        </button>
                      </div>
                      {jsonCopyStatus && (
                        <div className="text-xs text-emerald-700" data-testid="categories-preview-json-status">{jsonCopyStatus}</div>
                      )}
                      <pre className="text-xs bg-slate-900 text-slate-100 p-3 rounded overflow-auto max-h-64" data-testid="categories-preview-json-content">
                        {JSON.stringify(schema, null, 2)}
                      </pre>
                    </div>
                  </details>

                  <div className="rounded-lg border p-4 space-y-3" data-testid="categories-version-history">
                    <div className="flex items-center justify-between">
                      <div className="text-sm font-semibold">Versiyon Geçmişi</div>
                      <span className="text-xs text-slate-700">Snapshot bazlı</span>
                    </div>
                    {versionsLoading ? (
                      <div className="text-sm text-slate-700" data-testid="categories-version-loading">Yükleniyor...</div>
                    ) : versionsError ? (
                      <div className="text-sm text-rose-600" data-testid="categories-version-error">{versionsError}</div>
                    ) : versions.length === 0 ? (
                      <div className="text-sm text-slate-700" data-testid="categories-version-empty">Henüz versiyon yok.</div>
                    ) : (
                      <div className="space-y-2" data-testid="categories-version-list">
                        {versions.map((version) => (
                          <div key={version.id} className="flex flex-wrap items-center justify-between gap-3 border rounded px-3 py-2 text-sm" data-testid={`categories-version-row-${version.id}`}>
                            <div className="space-y-1">
                              <div className="font-medium" data-testid={`categories-version-label-${version.id}`}>v{version.version} · {version.status === 'published' ? 'Yayınlandı' : 'Taslak'}</div>
                              <div className="text-xs text-slate-700" data-testid={`categories-version-meta-${version.id}`}>
                                {version.created_at || '-'} · {version.created_by_email || '-'}
                              </div>
                            </div>
                            <label className="flex items-center gap-2 text-xs text-slate-700" data-testid={`categories-version-select-wrapper-${version.id}`}>
                              <input
                                type="checkbox"
                                checked={selectedVersions.includes(version.id)}
                                onChange={() => handleVersionSelect(version.id)}
                                data-testid={`categories-version-select-${version.id}`}
                              />
                              Karşılaştır
                            </label>
                          </div>
                        ))}
                      </div>
                    )}
                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-700" data-testid="categories-version-selection-hint">
                      2 versiyon seçildiğinde diff görünür.
                      {selectedVersions.length > 0 && (
                        <button
                          type="button"
                          className="px-2 py-1 border rounded text-xs"
                          onClick={() => setSelectedVersions([])}
                          data-testid="categories-version-clear"
                        >
                          Seçimi temizle
                        </button>
                      )}
                    </div>
                  </div>

                  {selectedVersions.length === 2 && versionCompare.left && versionCompare.right && (
                    <div className="rounded-lg border p-4 space-y-3" data-testid="categories-version-compare">
                      <div className="text-sm font-semibold">Versiyon Karşılaştırma</div>
                      {versionCompare.diffPaths.length > 0 ? (
                        <div className="text-xs text-amber-700" data-testid="categories-version-diff-count">
                          {versionCompare.diffPaths.length} farklı alan bulundu.
                        </div>
                      ) : (
                        <div className="text-xs text-emerald-700" data-testid="categories-version-diff-empty">Fark bulunamadı.</div>
                      )}
                      {versionCompare.diffPaths.length > 0 && (
                        <ul className="list-disc pl-5 space-y-1 text-xs text-slate-700 max-h-32 overflow-auto" data-testid="categories-version-diff-list">
                          {versionCompare.diffPaths.slice(0, 20).map((path, index) => (
                            <li key={`diff-${index}`} data-testid={`categories-version-diff-${index}`}>{path}</li>
                          ))}
                        </ul>
                      )}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="space-y-2">
                          <div className="text-xs font-semibold text-slate-700" data-testid="categories-version-left-label">v{versionCompare.left.version}</div>
                          <pre className="text-xs bg-slate-900 text-slate-100 p-3 rounded overflow-auto max-h-64" data-testid="categories-version-left-json">
                            {JSON.stringify(versionCompare.left.schema_snapshot, null, 2)}
                          </pre>
                        </div>
                        <div className="space-y-2">
                          <div className="text-xs font-semibold text-slate-700" data-testid="categories-version-right-label">v{versionCompare.right.version}</div>
                          <pre className="text-xs bg-slate-900 text-slate-100 p-3 rounded overflow-auto max-h-64" data-testid="categories-version-right-json">
                            {JSON.stringify(versionCompare.right.schema_snapshot, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
                </div>
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
                {nextStep && (
                  <div title={nextTooltip} data-testid="categories-next-tooltip">
                    <button
                      className={`px-4 py-2 border rounded text-sm flex items-center gap-1 ${isNextEnabled ? 'text-slate-700' : 'text-slate-400 cursor-not-allowed'}`}
                      onClick={() => {
                        if (!isNextEnabled) {
                          setHierarchyError("Önce bu adımı tamamlayın.");
                          return;
                        }
                        setHierarchyError("");
                        setWizardStep(nextStep);
                      }}
                      disabled={!isNextEnabled}
                      data-testid="categories-step-next"
                    >
                      <span>Next</span>
                      <span aria-hidden>→</span>
                    </button>
                  </div>
                )}
                <button
                  className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-60"
                  onClick={handleStepComplete}
                  disabled={stepSaving}
                  data-testid="categories-step-complete"
                >
                  {stepSaving ? "Kaydediliyor..." : "Tamam"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      )}

      {bulkConfirmOpen && pendingBulkAction === "delete" && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45" data-testid="categories-bulk-delete-modal">
          <div className="w-full max-w-md rounded-xl bg-white p-5 shadow-xl" data-testid="categories-bulk-delete-modal-content">
            <h3 className="text-lg font-semibold text-slate-900" data-testid="categories-bulk-delete-title">Toplu Silme Onayı</h3>
            <p className="mt-2 text-sm text-slate-700" data-testid="categories-bulk-delete-description">
              <strong>{selectedIds.length}</strong> kayıt soft-delete edilecek. Devam etmek için <strong>ONAYLA</strong> yazın.
            </p>
            <input
              value={bulkConfirmValue}
              onChange={(event) => setBulkConfirmValue(event.target.value)}
              className="mt-3 h-10 w-full rounded-md border px-3 text-sm"
              placeholder="ONAYLA"
              data-testid="categories-bulk-delete-confirm-input"
            />
            <div className="mt-4 flex items-center justify-end gap-2" data-testid="categories-bulk-delete-actions">
              <button
                type="button"
                className="rounded border px-3 py-1.5 text-sm"
                onClick={() => {
                  setBulkConfirmOpen(false);
                  setBulkConfirmValue("");
                  setPendingBulkAction("");
                }}
                data-testid="categories-bulk-delete-cancel"
              >
                Vazgeç
              </button>
              <button
                type="button"
                className="rounded border border-rose-300 bg-rose-600 px-3 py-1.5 text-sm text-white disabled:opacity-60"
                onClick={confirmBulkDelete}
                disabled={bulkRunning}
                data-testid="categories-bulk-delete-confirm"
              >
                {bulkRunning ? 'İşleniyor...' : 'Silmeyi Onayla'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminCategories;
