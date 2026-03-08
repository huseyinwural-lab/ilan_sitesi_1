import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import * as XLSX from "xlsx";
import { useCountry } from "../../contexts/CountryContext";
import { useAuth } from "../../contexts/AuthContext";
import { useToast } from "@/components/ui/toaster";
import { CategoryIconSvg } from "@/components/categories/CategoryIconSvg";
import { APPROVED_CATEGORY_ICON_LIBRARY } from "@/constants/categoryIconLibrary";

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

const CATEGORY_ICON_SVG_MAX_LENGTH = 20000;

const isCategoryIconSvgUnsafe = (raw) => {
  const lowered = String(raw || "").toLowerCase();
  if (/<\s*\/?\s*script/.test(lowered)) return true;
  if (/on[a-z]+\s*=/.test(lowered)) return true;
  if (lowered.includes("javascript:")) return true;
  if (lowered.includes("<foreignobject")) return true;
  return false;
};

const TRANSACTION_TYPE_OPTIONS = [
  { value: "satilik", label: "Satılık" },
  { value: "kiralik", label: "Kiralık" },
  { value: "gunluk", label: "Günlük Kiralık" },
];

const VEHICLE_LEVEL0_TEMPLATES = [
  "Otomobil",
  "SUV",
  "Pickup",
  "Motosiklet",
  "Minibüs & Midibüs",
  "Otobüs",
  "Kamyon & Kamyonet",
  "Çekici",
  "Dorse Römork",
  "Oto Kurtarıcı & Taşıyıcı",
];

const INHERITANCE_START_LEVEL = 1;

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
  is_leaf: false,
  inherit_children: false,
  inherit_group_key: "",
  children: [],
});
const createSubcategoryGroupDraft = () => ({
  ...createSubcategoryDraft(),
});

const buildInheritanceGroupKey = (parentPath, levelIndex) => {
  const parentKey = parentPath.length ? parentPath.join(".") : "root";
  return `${parentKey}::${levelIndex}`;
};

const cloneHierarchyTemplate = (nodes = []) => nodes.map((node, index) => ({
  ...createSubcategoryDraft(),
  name: node?.name || "",
  slug: node?.slug || "",
  active_flag: node?.active_flag ?? true,
  sort_order: Number(node?.sort_order || index + 1),
  transaction_type: node?.transaction_type || "",
  is_complete: true,
  is_leaf: Boolean(node?.is_leaf),
  inherit_children: false,
  inherit_group_key: "",
  children: node?.is_leaf ? [] : cloneHierarchyTemplate(node?.children || []),
}));

const normalizeSlugValue = (value) => {
  if (!value) return "";
  return String(value)
    .replace(/\s+/g, " ")
    .trim();
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
    const locationParts = Array.isArray(firstError.loc) ? firstError.loc.map((item) => String(item || "")).filter(Boolean) : [];
    const location = locationParts.join(".");
    const fieldName = locationParts.length > 0 ? locationParts[locationParts.length - 1] : "";
    const baseMessage = firstError.msg || firstError.message || fallbackMessage;
    return {
      errorCode: payload?.error_code || "",
      message: location ? `${location}: ${baseMessage}` : baseMessage,
      fieldName,
      conflict: null,
      sourcePath: location,
    };
  }
  if (typeof detail === "string") {
    return {
      errorCode: payload?.error_code || "",
      message: detail || fallbackMessage,
      fieldName: "",
      conflict: null,
      sourcePath: "",
    };
  }
  if (detail && typeof detail === "object") {
    const sourcePathRaw = detail.source_path || detail.source || detail.path || (Array.isArray(detail.loc) ? detail.loc.join(".") : "");
    const sourcePath = String(sourcePathRaw || "").trim();
    const fieldName = detail.field_name || detail.field || (sourcePath ? sourcePath.split(".").pop() : "");
    const rawMessage = detail.message || payload?.message || fallbackMessage;
    const conflict = detail.conflict || null;
    let humanMessage = fieldName ? `Alan: ${fieldName} • ${rawMessage}` : rawMessage;

    if (fieldName === "sort_order" && conflict && (conflict.sort_order || conflict.slug || conflict.name)) {
      const conflictBits = [
        conflict.sort_order ? `sıra: ${conflict.sort_order}` : "",
        conflict.slug ? `slug: ${conflict.slug}` : "",
      ].filter(Boolean);
      if (conflictBits.length > 0) {
        humanMessage = `${humanMessage} (Çakışan kayıt: ${conflictBits.join(", ")})`;
      }
    }

    if (fieldName === "slug" && conflict?.slug) {
      humanMessage = `${humanMessage} (Çakışan slug: ${conflict.slug})`;
    }

    return {
      errorCode: detail.error_code || payload?.error_code || "",
      message: humanMessage,
      fieldName,
      conflict,
      sourcePath,
    };
  }
  return {
    errorCode: payload?.error_code || "",
    message: payload?.message || fallbackMessage,
    fieldName: "",
    conflict: null,
    sourcePath: "",
  };
};

const waitMs = (duration) => new Promise((resolve) => setTimeout(resolve, duration));

const isTransientCategorySaveError = (httpStatus, parsed) => {
  const status = Number(httpStatus || 0);
  const message = String(parsed?.message || "").toLowerCase();
  const code = String(parsed?.errorCode || "").toUpperCase();
  if ([429, 500, 502, 503, 504].includes(status)) return true;
  if (code.startsWith("DB_")) return true;
  if (message.includes("database") || message.includes("timeout") || message.includes("service unavailable")) return true;
  return false;
};

const safeParseJson = async (response) => {
  try {
    const text = await response.text();
    if (!text) return {};
    try {
      return JSON.parse(text);
    } catch (error) {
      return { message: text, detail: text };
    }
  } catch (error) {
    return {};
  }
};

const buildHttpStatusFallbackMessage = (status) => {
  const code = Number(status || 0);
  if (code === 404) return "Kayıt bulunamadı (404). Sistem mevcut kayıtla yeniden bağlanmayı deneyecek.";
  if (code === 409) return "Kayıt çakışması (409). Sistem mevcut kayıtla yeniden bağlanmayı deneyecek.";
  if (code === 401 || code === 403) return `Yetki hatası (${code}). Lütfen oturum/yetki durumunu kontrol edin.`;
  if (code >= 500) return `Sunucu geçici olarak erişilemez (${code}).`;
  return `İşlem başarısız (${code || "unknown"}).`;
};

const CATEGORY_FIELD_ERROR_KEY_MAP = {
  name: "main_name",
  slug: "main_slug",
  country_code: "main_country",
  module: "main_module",
  sort_order: "main_sort_order",
  icon_svg: "main_icon_svg",
};

const buildCategoryErrorMessage = (parsed, fallbackMessage = "İşlem başarısız.") => {
  const baseMessage = String(parsed?.message || fallbackMessage || "İşlem başarısız.").trim();
  const code = String(parsed?.errorCode || "").trim();
  const sourcePath = String(parsed?.sourcePath || "").trim();
  const withCode = code ? `[${code}] ${baseMessage}` : baseMessage;
  if (!sourcePath) return withCode;
  return `${withCode} • Kaynak: ${sourcePath}`;
};

const formatDateTimeShort = (value) => {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "-";
  return parsed.toLocaleString("tr-TR");
};

const getCategoryListIssueBadges = (item) => {
  const badges = [];
  if (!item?.hierarchy_complete) {
    badges.push({ key: "hierarchy", label: "Hierarchy" });
  }

  const formSchema = item?.form_schema;
  const hasFormSchema = Boolean(formSchema) && typeof formSchema === "object" && Object.keys(formSchema || {}).length > 0;
  if (!hasFormSchema) {
    badges.push({ key: "forms", label: "Forms" });
  }

  if (!Number.isFinite(Number(item?.sort_order)) || Number(item?.sort_order) <= 0) {
    badges.push({ key: "rules", label: "Rules" });
  }
  return badges;
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
    issue_state: "all",
    sort_by: "name_asc",
    search_query: "",
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
    icon_svg: "",
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
  const [vehicleImportMode, setVehicleImportMode] = useState("");
  const [vehicleImportPayload, setVehicleImportPayload] = useState("{\n  \"dry_run\": true\n}");
  const [vehicleImportFile, setVehicleImportFile] = useState(null);
  const [vehicleImportDryRun, setVehicleImportDryRun] = useState(true);
  const [vehicleImportStatus, setVehicleImportStatus] = useState("");
  const [vehicleImportError, setVehicleImportError] = useState("");
  const [vehicleImportLoading, setVehicleImportLoading] = useState(false);
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
  const [categoryIconSvgError, setCategoryIconSvgError] = useState("");
  const [iconPickerTab, setIconPickerTab] = useState("library");
  const [iconLibraryQuery, setIconLibraryQuery] = useState("");
  const [iconLibraryTag, setIconLibraryTag] = useState("all");
  const [schema, setSchema] = useState(createDefaultSchema());
  const [wizardStep, setWizardStep] = useState("hierarchy");
  const [wizardProgress, setWizardProgress] = useState({ state: "draft", dirty_steps: [] });
  const [editModeStep, setEditModeStep] = useState(null);
  const [hierarchyComplete, setHierarchyComplete] = useState(false);
  const [hierarchyError, setHierarchyError] = useState("");
  const [hierarchyFieldErrors, setHierarchyFieldErrors] = useState({});
  const [subcategories, setSubcategories] = useState([createSubcategoryDraft()]);
  const [inheritanceGroups, setInheritanceGroups] = useState({});
  const [levelSelections, setLevelSelections] = useState([]);
  const [levelCompletion, setLevelCompletion] = useState({});
  const [draggingLevelIndex, setDraggingLevelIndex] = useState(null);
  const [draggingItemIndex, setDraggingItemIndex] = useState(null);
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
  const [lastDeleteUndo, setLastDeleteUndo] = useState(null);
  const [undoSecondsLeft, setUndoSecondsLeft] = useState(0);
  const [undoOperations, setUndoOperations] = useState([]);
  const [undoOperationsLoading, setUndoOperationsLoading] = useState(false);
  const [seedLoading, setSeedLoading] = useState(false);
  const [level0OrderMovingId, setLevel0OrderMovingId] = useState("");
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

  const applyParsedCategoryError = useCallback((parsed, { setGeneral = true } = {}) => {
    const finalMessage = buildCategoryErrorMessage(parsed, "İşlem başarısız.");
    const normalizedField = String(parsed?.fieldName || "").trim();
    const mappedKey = CATEGORY_FIELD_ERROR_KEY_MAP[normalizedField];

    if (mappedKey) {
      setHierarchyFieldErrors((prev) => ({ ...prev, [mappedKey]: finalMessage }));
    }
    if (normalizedField === "vehicle_segment") {
      setVehicleSegmentError(finalMessage);
    }
    if (normalizedField === "image_url") {
      setCategoryImageError(finalMessage);
    }
    if (normalizedField === "icon_svg") {
      setCategoryIconSvgError(finalMessage);
    }
    if (setGeneral) {
      setHierarchyError(finalMessage);
    }
    return finalMessage;
  }, []);

  const resolveCategoryForSelfHeal = useCallback(async ({
    categoryId,
    slug,
    name,
    moduleValue,
    countryCode,
    parentId,
    parentIsRoot,
  }) => {
    try {
      const params = new URLSearchParams();
      if (categoryId) params.set("category_id", String(categoryId));
      if (slug) params.set("slug", normalizeSlugValue(slug));
      if (name) params.set("name", String(name));
      if (moduleValue) params.set("module", String(moduleValue));
      if (countryCode) params.set("country", String(countryCode).toUpperCase());
      if (parentId) {
        params.set("parent_id", String(parentId));
      } else if (parentIsRoot) {
        params.set("parent_is_root", "true");
      }

      const response = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/resolve?${params.toString()}`,
        { headers: authHeader }
      );
      const data = await safeParseJson(response);
      if (!response.ok) return null;
      return data?.category || null;
    } catch (_error) {
      return null;
    }
  }, [authHeader]);

  const selectedIdSet = useMemo(() => new Set(selectedIds), [selectedIds]);
  const hierarchyPreviewRows = useMemo(() => {
    if (!Array.isArray(items) || items.length === 0) return [];

    const normalizeNameKey = (value) => String(value || '').trim().toLowerCase();
    const realEstateSchema = {
      1: new Set(['emlak']),
      2: new Set(['konut', 'ticari alan', 'arsa']),
      3: new Set(['satılık', 'kiralık', 'günlük kiralık']),
      4: new Set(['daire', 'müstakil ev', 'köşk & konak', 'bina', 'çiftlik evi']),
    };

    const byParent = new Map();
    items.forEach((item) => {
      const parentKey = item.parent_id || "__root__";
      if (!byParent.has(parentKey)) byParent.set(parentKey, []);
      byParent.get(parentKey).push(item);
    });

    const sortItems = (arr) => [...arr].sort((a, b) => {
      const depthCmp = Number(a.depth || 0) - Number(b.depth || 0);
      if (depthCmp !== 0) return depthCmp;
      const sortCmp = Number(a.sort_order || 0) - Number(b.sort_order || 0);
      if (sortCmp !== 0) return sortCmp;
      return String(a.name || "").localeCompare(String(b.name || ""), 'tr');
    });

    const rows = [];
    const walk = (node, level) => {
      if (node.module === 'real_estate' && level <= 4) {
        const allowed = realEstateSchema[level];
        if (allowed && !allowed.has(normalizeNameKey(node.name))) {
          return;
        }
      }

      rows.push({
        id: node.id,
        name: node.name,
        level,
        listing_count: Number(node.listing_count || 0),
        module: node.module,
      });
      const children = sortItems(byParent.get(node.id) || []);
      children.forEach((child) => walk(child, level + 1));
    };

    const roots = sortItems(byParent.get("__root__") || []);
    roots.forEach((root) => walk(root, 1));
    return rows;
  }, [items]);
  const visibleItems = useMemo(() => {
    const rootOnlyItems = items.filter((item) => !item.parent_id);
    const normalizedQuery = String(listFilters.search_query || "").trim().toLocaleLowerCase("tr");

    let filtered = rootOnlyItems.filter((item) => {
      if (listFilters.image_presence === "with_image" && !Boolean((item.image_url || "").trim())) return false;
      if (listFilters.image_presence === "without_image" && Boolean((item.image_url || "").trim())) return false;

      if (listFilters.issue_state === "with_issues") {
        if (getCategoryListIssueBadges(item).length === 0) return false;
      }

      if (normalizedQuery) {
        const haystack = [item?.name, item?.slug, item?.country_code, item?.module]
          .map((value) => String(value || "").toLocaleLowerCase("tr"))
          .join(" ");
        if (!haystack.includes(normalizedQuery)) return false;
      }
      return true;
    });

    const sortMode = String(listFilters.sort_by || "name_asc");
    filtered = [...filtered].sort((a, b) => {
      if (sortMode === "name_desc") {
        return String(b.name || "").localeCompare(String(a.name || ""), "tr");
      }
      if (sortMode === "sort_asc") {
        return Number(a.sort_order || 0) - Number(b.sort_order || 0);
      }
      if (sortMode === "sort_desc") {
        return Number(b.sort_order || 0) - Number(a.sort_order || 0);
      }
      return String(a.name || "").localeCompare(String(b.name || ""), "tr");
    });

    return filtered;
  }, [items, listFilters.image_presence, listFilters.issue_state, listFilters.search_query, listFilters.sort_by]);

  const modalIssueBadges = useMemo(() => {
    const hierarchyHasIssue = Boolean(hierarchyError) || Object.keys(hierarchyFieldErrors || {}).some((key) => key.startsWith("main_") || key.startsWith("level-"));
    const formsHasIssue = Boolean(dynamicError) || Boolean(detailError) || Boolean(categoryImageError) || Boolean(categoryIconSvgError) || Boolean(vehicleImportError);
    const rulesHasIssue = Boolean(vehicleSegmentError) || Boolean(publishError) || Boolean(versionsError);

    return [
      { id: "hierarchy", label: "Hierarchy", hasIssue: hierarchyHasIssue },
      { id: "forms", label: "Forms", hasIssue: formsHasIssue },
      { id: "rules", label: "Rules", hasIssue: rulesHasIssue },
    ];
  }, [hierarchyError, hierarchyFieldErrors, dynamicError, detailError, categoryImageError, categoryIconSvgError, vehicleImportError, vehicleSegmentError, publishError, versionsError]);

  useEffect(() => {
    if (!lastDeleteUndo?.expiresAt) {
      setUndoSecondsLeft(0);
      return undefined;
    }

    const getRemainingSeconds = () => {
      const expiresAtMs = new Date(lastDeleteUndo.expiresAt).getTime();
      if (Number.isNaN(expiresAtMs)) return 0;
      return Math.max(0, Math.floor((expiresAtMs - Date.now()) / 1000));
    };

    setUndoSecondsLeft(getRemainingSeconds());
    const timer = window.setInterval(() => {
      const remaining = getRemainingSeconds();
      setUndoSecondsLeft(remaining);
      if (remaining <= 0) {
        setLastDeleteUndo(null);
      }
    }, 1000);

    return () => window.clearInterval(timer);
  }, [lastDeleteUndo]);

  const activeFilterChips = useMemo(() => {
    const chips = [];
    if (listFilters.module !== "all") chips.push({ key: "module", label: `Modül: ${listFilters.module}` });
    if (listFilters.status !== "all") chips.push({ key: "status", label: `Durum: ${listFilters.status}` });
    if (listFilters.image_presence !== "all") chips.push({ key: "image_presence", label: `Görsel: ${listFilters.image_presence}` });
    if (listFilters.issue_state !== "all") chips.push({ key: "issue_state", label: `Sorun: ${listFilters.issue_state}` });
    if (String(listFilters.search_query || "").trim()) chips.push({ key: "search_query", label: `Ara: ${String(listFilters.search_query).trim()}` });
    if (listFilters.sort_by !== "name_asc") chips.push({ key: "sort_by", label: `Sıralama: ${listFilters.sort_by}` });
    return chips;
  }, [listFilters]);

  const fetchUndoOperations = useCallback(async ({ silent = false } = {}) => {
    if (!silent) setUndoOperationsLoading(true);
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/delete-operations?hours=24&limit=20`, {
        headers: authHeader,
      });
      const data = await safeParseJson(response);
      if (!response.ok) {
        if (!silent) {
          const parsed = parseApiError(data, "Undo geçmişi alınamadı.");
          const message = buildCategoryErrorMessage(parsed, "Undo geçmişi alınamadı.");
          toast({ title: "Undo geçmişi alınamadı", description: message, variant: "destructive" });
        }
        setUndoOperations([]);
        return;
      }
      setUndoOperations(Array.isArray(data?.items) ? data.items : []);
    } catch (error) {
      if (!silent) {
        toast({
          title: "Undo geçmişi alınamadı",
          description: "Bağlantı hatası oluştu.",
          variant: "destructive",
        });
      }
      setUndoOperations([]);
    } finally {
      if (!silent) setUndoOperationsLoading(false);
    }
  }, [authHeader]);
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
  const categoryIconSvgLength = useMemo(() => String(form.icon_svg || "").trim().length, [form.icon_svg]);
  const iconLibraryTags = useMemo(
    () => [
      "all",
      ...Array.from(
        new Set(
          APPROVED_CATEGORY_ICON_LIBRARY.flatMap((item) => item.tags || [])
            .map((tag) => String(tag || "").trim().toLowerCase())
            .filter(Boolean)
        )
      ).sort((a, b) => a.localeCompare(b, "tr")),
    ],
    []
  );
  const filteredApprovedIcons = useMemo(() => {
    const query = String(iconLibraryQuery || "").trim().toLowerCase();
    return APPROVED_CATEGORY_ICON_LIBRARY.filter((item) => {
      const tags = Array.isArray(item.tags) ? item.tags : [];
      const tagMatch = iconLibraryTag === "all" || tags.includes(iconLibraryTag);
      if (!tagMatch) return false;
      if (!query) return true;
      const text = `${item.label} ${item.key} ${tags.join(" ")}`.toLowerCase();
      return text.includes(query);
    });
  }, [iconLibraryQuery, iconLibraryTag]);
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
      icon_svg: category.icon_svg || "",
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
    setCategoryIconSvgError("");
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
      const data = await safeParseJson(res);
      if (!res.ok) {
        const parsed = parseApiError(data, "Kategori listesi alınamadı.");
        const message = buildCategoryErrorMessage(parsed, "Kategori listesi alınamadı.");
        toast({
          title: "Kategori listesi alınamadı",
          description: message,
          variant: "destructive",
        });
        setItems([]);
        return;
      }
      setItems(data.items || []);
      setSelectedIds([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSeedRealEstateStandard = async () => {
    if (seedLoading) return;
    setSeedLoading(true);
    try {
      const country = selectedCountry || 'DE';
      const res = await fetch(
        `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/seed/real-estate-standard?country=${encodeURIComponent(country)}`,
        {
          method: 'POST',
          headers: authHeader,
        }
      );
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail?.message || data?.detail || 'Standart şema uygulanamadı.');
      }
      toast({
        title: 'Standart Emlak Şeması Uygulandı',
        description: `Oluşturulan: ${data?.created_count || 0}, mevcut: ${data?.reused_count || 0}`,
      });
      setListFilters((prev) => ({ ...prev, module: 'real_estate' }));
      await fetchItems();
    } catch (error) {
      toast({
        title: 'Şema uygulama hatası',
        description: error.message || 'Bilinmeyen hata.',
        variant: 'destructive',
      });
    } finally {
      setSeedLoading(false);
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

  const requestCategoryMutationWithRetry = useCallback(async ({
    url,
    method,
    payload,
    fallbackMessage,
    retries = 3,
    selfHealContext = null,
  }) => {
    let lastParsed = { errorCode: "", message: fallbackMessage, fieldName: "", conflict: null };
    let lastStatus = 0;
    let workingUrl = url;
    let workingPayload = { ...(payload || {}) };

    for (let attempt = 0; attempt < retries; attempt += 1) {
      const res = await fetch(workingUrl, {
        method,
        headers: {
          "Content-Type": "application/json",
          ...authHeader,
        },
        body: JSON.stringify(workingPayload),
      });

      let data = await safeParseJson(res);
      if (!res.ok && (!data || Object.keys(data).length === 0)) {
        data = { message: buildHttpStatusFallbackMessage(res.status) };
      }

      if (res.ok) {
        return { ok: true, data, status: res.status, selfHealed: false };
      }

      const parsed = parseApiError(data, fallbackMessage);
      lastParsed = parsed;
      lastStatus = res.status;

      const staleVersionCurrent = String(parsed?.conflict?.current_updated_at || "").trim();
      if (method === "PATCH" && parsed?.errorCode === "CATEGORY_STALE_VERSION" && staleVersionCurrent) {
        workingPayload = {
          ...workingPayload,
          expected_updated_at: staleVersionCurrent,
        };
        if (attempt < retries - 1) {
          continue;
        }
      }

      if ([404, 409].includes(res.status) && selfHealContext) {
        const resolvedCategory = await resolveCategoryForSelfHeal({
          categoryId:
            parsed?.conflict?.existing_category_id
            || selfHealContext.categoryId
            || "",
          slug:
            selfHealContext.slug
            || workingPayload.slug
            || "",
          name:
            selfHealContext.name
            || workingPayload.name
            || "",
          moduleValue:
            selfHealContext.moduleValue
            || workingPayload.module
            || "",
          countryCode:
            selfHealContext.countryCode
            || workingPayload.country_code
            || selectedCountry
            || "",
          parentId:
            selfHealContext.parentId
            ?? workingPayload.parent_id
            ?? "",
          parentIsRoot: Boolean(
            selfHealContext.parentIsRoot
            ?? (workingPayload.parent_id === "" || workingPayload.parent_id === null || workingPayload.parent_id === undefined)
          ),
        });

        if (resolvedCategory?.id) {
          if (method === "POST") {
            return {
              ok: true,
              status: 200,
              selfHealed: true,
              data: {
                category: resolvedCategory,
                reused: true,
                category_id: resolvedCategory.id,
                self_healed: true,
              },
            };
          }

          const reboundUrl = `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${resolvedCategory.id}`;
          workingUrl = reboundUrl;
          workingPayload = {
            ...workingPayload,
            expected_updated_at: resolvedCategory.updated_at || workingPayload.expected_updated_at,
          };
          if (attempt < retries - 1) {
            continue;
          }
        }
      }

      if (isTransientCategorySaveError(res.status, parsed) && attempt < retries - 1) {
        await waitMs(250 * (attempt + 1));
        continue;
      }

      return { ok: false, parsed, status: res.status, data, selfHealed: false };
    }

    return { ok: false, parsed: lastParsed, status: lastStatus, data: {}, selfHealed: false };
  }, [authHeader, resolveCategoryForSelfHeal, selectedCountry]);

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
      const mutation = await requestCategoryMutationWithRetry({
        url: `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories`,
        method: "POST",
        payload,
        fallbackMessage,
        retries: 3,
        selfHealContext: {
          slug: payload.slug,
          name: payload.name,
          moduleValue,
          countryCode,
          parentId,
          parentIsRoot: !parentId,
        },
      });
      if (mutation.ok) {
        return {
          ok: true,
          data: mutation.data,
          payload,
          autoAdjusted: attempt > 0,
          selfHealed: Boolean(mutation.selfHealed),
        };
      }

      const parsed = mutation.parsed;

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
  }, [findNextAvailableSortOrder, requestCategoryMutationWithRetry]);

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
    fetchUndoOperations({ silent: true });
  }, [selectedCountry, listFilters.module, listFilters.status, fetchUndoOperations]);

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
    return children.map((child) => {
      const nestedChildren = buildSubcategoryTree(child.id);
      return {
        id: child.id,
        name: child.name || "",
        slug: child.slug || "",
        active_flag: child.active_flag ?? true,
        sort_order: child.sort_order || 0,
        transaction_type: child.form_schema?.category_meta?.transaction_type || "",
        is_complete: true,
        is_leaf: nestedChildren.length === 0,
        children: nestedChildren,
      };
    });
  };

  const mapTreeToGroupRows = (treeNodes = []) => {
    const normalizeNode = (node) => ({
      id: node.id,
      name: node.name || "",
      slug: node.slug || "",
      active_flag: node.active_flag ?? true,
      sort_order: node.sort_order || 1,
      transaction_type: node.transaction_type || "",
      is_complete: true,
      is_leaf: node.is_leaf ?? ((node.children || []).length === 0),
      inherit_children: false,
      inherit_group_key: "",
      children: (node.children || []).map(normalizeNode),
    });

    if (!Array.isArray(treeNodes) || treeNodes.length === 0) {
      return [createSubcategoryDraft()];
    }
    return treeNodes.map(normalizeNode);
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

  const getInheritanceGroupKeyForLevel = (levelIndex) => (
    buildInheritanceGroupKey(getParentPathForLevel(levelIndex), levelIndex)
  );

  const levelBreadcrumbs = useMemo(() => {
    const crumbs = [];
    let currentNodes = subcategories;
    for (let levelIndex = 0; levelIndex < levelSelections.length; levelIndex += 1) {
      const selectedIndex = levelSelections[levelIndex];
      if (selectedIndex === undefined) break;
      const node = currentNodes[selectedIndex];
      if (!node) break;
      crumbs.push({ levelIndex, label: node.name?.trim() || `Seviye ${levelIndex + 1}` });
      currentNodes = node.children || [];
    }
    return crumbs;
  }, [subcategories, levelSelections]);

  const handleLevelBack = () => {
    setLevelSelections((prev) => {
      const next = prev.slice(0, Math.max(prev.length - 1, 0));
      resetLevelCompletionFrom(next.length);
      return next;
    });
  };

  const handleLevelJump = (targetLevel) => {
    setLevelSelections((prev) => {
      const next = prev.slice(0, targetLevel + 1);
      resetLevelCompletionFrom(targetLevel + 1);
      return next;
    });
  };

  const handleCreateNextLevel = () => {
    if (levelSelections.length === 0) {
      setHierarchyError("Önce seviye 1 kategorisi seçin.");
      return;
    }
    const currentLevel = levelSelections.length - 1;
    if (!levelCompletion[currentLevel]) {
      setHierarchyError("Önce bu seviyeyi onaylayın.");
      return;
    }
    const selectedPath = levelSelections.slice(0, currentLevel + 1);
    const selectedNode = getNodeByPath(subcategories, selectedPath);
    if (!selectedNode) return;
    if (selectedNode.is_leaf) {
      setHierarchyError("Leaf işaretli kategorinin altı açılamaz.");
      return;
    }

    const groupKey = currentLevel >= INHERITANCE_START_LEVEL
      ? buildInheritanceGroupKey(getParentPathForLevel(currentLevel), currentLevel)
      : "";
    const template = groupKey ? (inheritanceGroups[groupKey]?.template || []) : [];
    const shouldCloneTemplate = currentLevel >= INHERITANCE_START_LEVEL && template.length > 0;

    if (!Array.isArray(selectedNode.children) || selectedNode.children.length === 0) {
      setSubcategories((prev) => updateNodeByPath(prev, selectedPath, (node) => ({
        ...node,
        is_leaf: false,
        inherit_children: shouldCloneTemplate ? true : node.inherit_children,
        inherit_group_key: shouldCloneTemplate ? groupKey : node.inherit_group_key,
        children: shouldCloneTemplate ? cloneHierarchyTemplate(template) : [...(node.children || []), createSubcategoryDraft()],
      })));
    }
    setLevelSelections((prev) => {
      const next = prev.slice(0, currentLevel + 1);
      next[currentLevel + 1] = 0;
      return next;
    });
    setHierarchyError("");
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

  const clearHierarchyFieldErrorsByPrefix = (prefixes = []) => {
    if (!Array.isArray(prefixes) || prefixes.length === 0) return;
    setHierarchyFieldErrors((prev) => {
      const next = { ...prev };
      Object.keys(next).forEach((key) => {
        if (prefixes.some((prefix) => key.startsWith(prefix))) {
          delete next[key];
        }
      });
      return next;
    });
  };

  const handleLevelSelect = (levelIndex, itemIndex) => {
    if (levelIndex >= INHERITANCE_START_LEVEL) {
      const parentPath = getParentPathForLevel(levelIndex);
      const groupKey = getInheritanceGroupKeyForLevel(levelIndex);
      const template = inheritanceGroups[groupKey]?.template || [];
      const selectedItem = getLevelItems(levelIndex)[itemIndex];
      if (selectedItem && selectedItem.inherit_children && template.length > 0 && (!Array.isArray(selectedItem.children) || selectedItem.children.length === 0)) {
        setSubcategories((prev) => updateNodeByPath(prev, [...parentPath, itemIndex], (node) => ({
          ...node,
          is_leaf: false,
          children: cloneHierarchyTemplate(template),
        })));
      }
    }
    setLevelSelections((prev) => {
      const next = prev.slice(0, levelIndex);
      next[levelIndex] = itemIndex;
      return next;
    });
    resetLevelCompletionFrom(levelIndex + 1);
  };

  const addLevelItem = (levelIndex) => {
    resetLevelCompletionFrom(levelIndex);
    const parentPath = getParentPathForLevel(levelIndex);
    const groupKey = levelIndex >= INHERITANCE_START_LEVEL ? getInheritanceGroupKeyForLevel(levelIndex) : "";
    const template = groupKey ? (inheritanceGroups[groupKey]?.template || []) : [];
    const shouldCloneTemplate = levelIndex >= INHERITANCE_START_LEVEL && template.length > 0;
    const newItem = shouldCloneTemplate
      ? {
          ...createSubcategoryDraft(),
          inherit_children: true,
          inherit_group_key: groupKey,
          is_leaf: false,
          children: cloneHierarchyTemplate(template),
        }
      : createSubcategoryDraft();

    if (levelIndex === 0) {
      setSubcategories((prev) => [...prev, newItem]);
      return;
    }
    if (parentPath.length === 0) return;
    setSubcategories((prev) => updateNodeByPath(prev, parentPath, (node) => ({
      ...node,
      is_leaf: false,
      children: [...(node.children || []), newItem],
    })));
  };

  const updateLevelItem = (levelIndex, itemIndex, patch) => {
    resetLevelCompletionFrom(levelIndex);
    const path = [...getParentPathForLevel(levelIndex), itemIndex];
    const normalizedPatch = { ...patch };
    const errorPrefix = `level-${levelIndex}-${itemIndex}-`;
    if (Object.prototype.hasOwnProperty.call(patch, "is_leaf")) {
      normalizedPatch.is_leaf = Boolean(patch.is_leaf);
      if (normalizedPatch.is_leaf) {
        normalizedPatch.children = [];
      }
    }
    updateSubcategory(path, normalizedPatch);
    clearHierarchyFieldErrorsByPrefix([errorPrefix]);
    setHierarchyError("");
  };

  const handleBreakInheritance = (levelIndex, itemIndex) => {
    const path = [...getParentPathForLevel(levelIndex), itemIndex];
    updateSubcategory(path, { inherit_children: false, inherit_group_key: "" });
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
      setHierarchyError(`Seviye ${levelIndex + 1} için en az bir kategori gerekir.`);
      return;
    }

    const nextFieldErrors = {};
    const slugs = new Set();

    items.forEach((item, itemIndex) => {
      const pathKey = `${levelIndex}-${itemIndex}`;
      if (!item?.name?.trim()) {
        nextFieldErrors[`level-${pathKey}-name`] = "Ad zorunludur.";
      }
      if (!item?.slug?.trim()) {
        nextFieldErrors[`level-${pathKey}-slug`] = "Slug zorunludur.";
      }
      const rawSort = item?.sort_order;
      const hasSort = rawSort !== "" && rawSort !== null && rawSort !== undefined;
      if (hasSort) {
        const sortValue = Number(rawSort);
        if (!Number.isFinite(sortValue) || sortValue <= 0) {
          nextFieldErrors[`level-${pathKey}-sort`] = "Sıra 1 veya daha büyük olmalıdır.";
        }
      }

      const slugKey = (item?.slug || "").trim().toLowerCase();
      if (slugKey) {
        if (slugs.has(slugKey)) {
          nextFieldErrors[`level-${pathKey}-slug`] = "Bu seviyede slug tekrar edemez.";
        }
        slugs.add(slugKey);
      }
    });

    const levelPrefix = `level-${levelIndex}-`;

    if (Object.keys(nextFieldErrors).length > 0) {
      setHierarchyFieldErrors((prev) => {
        const next = { ...prev };
        Object.keys(next).forEach((key) => {
          if (key.startsWith(levelPrefix)) {
            delete next[key];
          }
        });
        return { ...next, ...nextFieldErrors };
      });
      setHierarchyError(`Seviye ${levelIndex + 1} için alanları tamamlayın.`);
      return;
    }

    clearHierarchyFieldErrorsByPrefix([levelPrefix]);
    setHierarchyError("");

    const normalizedItems = items.map((item, index) => {
      const parsedSort = Number(item.sort_order);
      const resolvedSort = Number.isFinite(parsedSort) && parsedSort > 0 ? parsedSort : index + 1;
      return {
        ...item,
        name: item.name.trim(),
        slug: item.slug.trim(),
        sort_order: resolvedSort,
        is_complete: true,
        is_leaf: Boolean(item.is_leaf),
        children: item.is_leaf ? [] : (item.children || []),
      };
    });

    const parentLevel = levelIndex - 1;
    const parentPath = getParentPathForLevel(levelIndex);
    const inheritanceEnabled = parentLevel >= INHERITANCE_START_LEVEL;
    let shouldSetTemplate = false;
    let groupKey = "";
    let template = [];
    let siblingParentPath = [];
    let currentParentIndex = null;

    if (inheritanceEnabled) {
      siblingParentPath = getParentPathForLevel(parentLevel);
      groupKey = buildInheritanceGroupKey(siblingParentPath, parentLevel);
      currentParentIndex = parentPath[parentPath.length - 1];
      const existingGroup = inheritanceGroups[groupKey];
      const siblings = parentLevel === 0
        ? subcategories
        : (getNodeByPath(subcategories, siblingParentPath)?.children || []);
      const currentParent = siblings[currentParentIndex];
      const currentInherits = Boolean(currentParent?.inherit_children)
        && currentParent?.inherit_group_key === groupKey;

      if (!existingGroup || currentInherits) {
        shouldSetTemplate = true;
        template = cloneHierarchyTemplate(normalizedItems);
      }
    }

    if (levelIndex === 0) {
      setSubcategories(normalizedItems);
    } else if (!inheritanceEnabled) {
      const parentPathLocal = getParentPathForLevel(levelIndex);
      if (parentPathLocal.length === 0) {
        setHierarchyError("Önce üst seviyeden bir kategori seçin.");
        return;
      }
      setSubcategories((prev) => updateNodeByPath(prev, parentPathLocal, (node) => ({
        ...node,
        is_leaf: false,
        children: normalizedItems,
      })));
    } else {
      const parentPathLocal = parentPath;
      if (parentPathLocal.length === 0) {
        setHierarchyError("Önce üst seviyeden bir kategori seçin.");
        return;
      }

      setSubcategories((prev) => updateNodeByPath(prev, parentPathLocal, (node) => {
        const shouldInherit = inheritanceGroups[groupKey]
          ? (node.inherit_children && node.inherit_group_key === groupKey)
          : true;
        return {
          ...node,
          is_leaf: false,
          inherit_children: shouldInherit,
          inherit_group_key: shouldInherit ? groupKey : "",
          children: normalizedItems,
        };
      }));
    }

    if (inheritanceEnabled && shouldSetTemplate) {
      setInheritanceGroups((prev) => ({
        ...prev,
        [groupKey]: {
          template,
          sourcePath: parentPath,
        },
      }));
    }

    setHierarchyError("");
    setHierarchyFieldErrors((prev) => {
      const next = { ...prev };
      Object.keys(next).forEach((key) => {
        if (key.startsWith(`level-${levelIndex}-`)) {
          delete next[key];
        }
      });
      return next;
    });
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
    }));
    if (levelIndex === 0) {
      setSubcategories(resetItems);
    } else {
      const parentPath = getParentPathForLevel(levelIndex);
      if (parentPath.length === 0) return;
      setSubcategories((prev) => updateNodeByPath(prev, parentPath, (node) => ({
        ...node,
        is_leaf: false,
        children: resetItems,
      })));
    }
    resetLevelCompletionFrom(levelIndex);
    setLevelSelections((prev) => prev.slice(0, levelIndex + 1));
    setHierarchyError("");
    setHierarchyFieldErrors({});
  };

  const handleLevelEditItem = async (levelIndex, itemIndex) => {
    await handleUnlockStep("hierarchy");
    const path = [...getParentPathForLevel(levelIndex), itemIndex];
    updateSubcategory(path, { is_complete: false });
    resetLevelCompletionFrom(levelIndex);
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
      icon_svg: "",
    });
    setSchema(createDefaultSchema());
    setEditing(null);
    setWizardStep("hierarchy");
    setWizardProgress({ state: "draft", dirty_steps: [] });
    setHierarchyComplete(false);
    setHierarchyError("");
    setHierarchyFieldErrors({});
    const initialSubcategories = [createSubcategoryDraft()];
    setSubcategories(initialSubcategories);
    setLevelSelections([]);
    setLevelCompletion({});
    setInheritanceGroups({});
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
    setVehicleImportMode("");
    setVehicleImportPayload("{\n  \"dry_run\": true\n}");
    setVehicleImportFile(null);
    setVehicleImportDryRun(true);
    setVehicleImportStatus("");
    setVehicleImportError("");
    setVehicleImportLoading(false);
    setOrderPreview({ checking: false, available: true, message: "", conflict: null, suggested_next_sort_order: null });
    setCategoryImageUploading(false);
    setCategoryImageError("");
    setCategoryIconSvgError("");
    setIconPickerTab("library");
    setIconLibraryQuery("");
    setIconLibraryTag("all");
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
      icon_svg: item.icon_svg || "",
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
    setInheritanceGroups({});
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
    setVehicleImportMode("");
    setVehicleImportPayload("{\n  \"dry_run\": true\n}");
    setVehicleImportFile(null);
    setVehicleImportDryRun(true);
    setVehicleImportStatus("");
    setVehicleImportError("");
    setVehicleImportLoading(false);
    setOrderPreview({ checking: false, available: true, message: "", conflict: null });
    setCategoryImageUploading(false);
    setCategoryImageError("");
    setCategoryIconSvgError("");
    setIconPickerTab("library");
    setIconLibraryQuery("");
    setIconLibraryTag("all");
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

  const resetVehicleImportStatus = () => {
    setVehicleImportStatus("");
    setVehicleImportError("");
  };

  const handleApplyVehicleTemplate = () => {
    const templateItems = VEHICLE_LEVEL0_TEMPLATES.map((name, index) => ({
      ...createSubcategoryDraft(),
      name,
      slug: normalizeSlugValue(name),
      sort_order: index + 1,
      is_complete: false,
      is_leaf: false,
      children: [],
    }));
    setSubcategories(templateItems.length ? templateItems : [createSubcategoryDraft()]);
    setLevelSelections([]);
    setLevelCompletion({});
    setHierarchyError("");
  };

  const handleVehicleImportApi = async () => {
    resetVehicleImportStatus();
    setVehicleImportLoading(true);
    try {
      const parsedPayload = vehicleImportPayload ? JSON.parse(vehicleImportPayload) : {};
      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/vehicle-master-import/jobs/api`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeader,
        },
        body: JSON.stringify({
          ...parsedPayload,
          dry_run: vehicleImportDryRun,
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.detail || data?.message || "API import başlatılamadı.");
      }
      setVehicleImportStatus(`Job oluşturuldu: ${data?.job?.id || "-"}`);
    } catch (error) {
      setVehicleImportError(error?.message || "API import başlatılamadı.");
    } finally {
      setVehicleImportLoading(false);
    }
  };

  const handleVehicleImportUpload = async (mode) => {
    resetVehicleImportStatus();
    if (!vehicleImportFile) {
      setVehicleImportError("Dosya seçin.");
      return;
    }
    setVehicleImportLoading(true);
    try {
      let fileToUpload = vehicleImportFile;
      if (mode === "excel") {
        const buffer = await vehicleImportFile.arrayBuffer();
        const workbook = XLSX.read(buffer, { type: "array" });
        const sheetName = workbook.SheetNames[0];
        const sheet = workbook.Sheets[sheetName];
        const jsonRows = XLSX.utils.sheet_to_json(sheet, { defval: null });
        const blob = new Blob([JSON.stringify(jsonRows)], { type: "application/json" });
        fileToUpload = new File([blob], "vehicle_import.json", { type: "application/json" });
      }

      const formData = new FormData();
      formData.append("file", fileToUpload);
      formData.append("dry_run", vehicleImportDryRun ? "true" : "false");

      const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/vehicle-master-import/jobs/upload`, {
        method: "POST",
        headers: {
          ...authHeader,
        },
        body: formData,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data?.message || data?.detail || "Upload başarısız.");
      }
      setVehicleImportStatus(`Job oluşturuldu: ${data?.job?.id || "-"}`);
    } catch (error) {
      setVehicleImportError(error?.message || "Upload başarısız.");
    } finally {
      setVehicleImportLoading(false);
    }
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

    const mutation = await requestCategoryMutationWithRetry({
      url,
      method,
      payload,
      fallbackMessage: "Kaydetme sırasında hata oluştu.",
      retries: 3,
      selfHealContext: {
        categoryId: activeEditing?.id || "",
        slug: payload.slug,
        name: payload.name,
        moduleValue: payload.module,
        countryCode: payload.country_code,
        parentId: payload.parent_id,
        parentIsRoot: !payload.parent_id,
      },
    });
    if (!mutation.ok) {
      const parsed = mutation.parsed;
      const detailedMessage = buildCategoryErrorMessage(parsed, "Kaydetme sırasında hata oluştu.");
      if (mutation.status === 409) {
        if (String(parsed.message || "").toLowerCase().includes("hiyerar")) {
          showDraftToast({
            title: "Kaydetme başarısız",
            description: detailedMessage,
            variant: "destructive",
          });
        } else {
          showDraftToast({
            title: "Kaydetme başarısız",
            description: detailedMessage,
            variant: "destructive",
          });
        }
        dismissDraftToast(4000);
      } else if (status === "draft") {
        showDraftToast({
          title: "Kaydetme başarısız",
          description: detailedMessage,
          variant: "destructive",
        });
        dismissDraftToast(4000);
      }
      applyParsedCategoryError(parsed, { setGeneral: !autosave });
      if (!autosave) {
        restoreSnapshot();
      }
      setAutosaveStatus("idle");
      return { success: false };
    }
    const data = mutation.data;
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
    if (mutation.selfHealed) {
      toast({
        title: "Kayıt yeniden bağlandı",
        description: "Sunucu çakışması algılandı; sistem mevcut kayıtla akışı otomatik sürdürdü.",
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
    if (!item?.id) return;
    const confirmed = window.confirm(`"${item.name || item.slug || 'Kategori'}" ve tüm alt kategorileri tek seferde silmek istiyor musunuz?`);
    if (!confirmed) return;

    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${item.id}?cascade=true`, {
      method: "DELETE",
      headers: {
        ...authHeader,
      },
    });
    const data = await safeParseJson(response);
    if (!response.ok) {
      const parsed = parseApiError(data, "Kategori silinemedi.");
      const message = applyParsedCategoryError(parsed, { setGeneral: true });
      toast({
        title: "Silme başarısız",
        description: message,
        variant: "destructive",
      });
      return;
    }

    const deletedCount = Number(data?.deleted_count || 1);
    const deletedDescendantCount = Number(data?.deleted_descendant_count || Math.max(0, deletedCount - 1));
    const undoOperationId = String(data?.undo_operation_id || "").trim();
    const undoExpiresAt = String(data?.undo_expires_at || "").trim();
    toast({
      title: "Kategori silindi",
      description: `${deletedCount} kayıt silindi (alt kategori: ${deletedDescendantCount}).`,
    });

    if (undoOperationId && undoExpiresAt) {
      setLastDeleteUndo({
        operationId: undoOperationId,
        expiresAt: undoExpiresAt,
        deletedCount,
      });
    }

    const deletedIds = Array.isArray(data?.deleted_ids) ? data.deleted_ids.map((idValue) => String(idValue)) : [];
    if (editing?.id && deletedIds.includes(String(editing.id))) {
      setModalOpen(false);
      setEditing(null);
    }
    fetchItems();
    fetchUndoOperations({ silent: true });
  };

  const handleUndoDelete = async () => {
    if (!lastDeleteUndo?.operationId || undoSecondsLeft <= 0) return;
    const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/delete-operations/${lastDeleteUndo.operationId}/undo`, {
      method: "POST",
      headers: {
        ...authHeader,
      },
    });
    const data = await safeParseJson(response);
    if (!response.ok) {
      const parsed = parseApiError(data, "Geri alma işlemi başarısız.");
      const message = applyParsedCategoryError(parsed, { setGeneral: true });
      toast({
        title: "Geri alma başarısız",
        description: message,
        variant: "destructive",
      });
      return;
    }

    const restoredCount = Number(data?.restored_count || 0);
    toast({
      title: "Silme geri alındı",
      description: `${restoredCount} kayıt geri yüklendi.`,
    });
    setLastDeleteUndo(null);
    fetchItems();
    fetchUndoOperations({ silent: true });
  };

  const handleMoveLevel0Order = async (item, direction) => {
    if (!item || item.parent_id || level0OrderMovingId) return;

    const siblingRows = items
      .filter(
        (row) => !row.parent_id
          && row.module === item.module
          && String(row.country_code || "") === String(item.country_code || "")
      )
      .sort((a, b) => {
        const sortCmp = Number(a.sort_order || 0) - Number(b.sort_order || 0);
        if (sortCmp !== 0) return sortCmp;
        return String(a.name || "").localeCompare(String(b.name || ""), "tr");
      });

    const currentIndex = siblingRows.findIndex((row) => row.id === item.id);
    if (currentIndex === -1) return;

    const targetIndex = direction === "up" ? currentIndex - 1 : currentIndex + 1;
    if (targetIndex < 0 || targetIndex >= siblingRows.length) return;

    const target = siblingRows[targetIndex];
    const currentSort = Number(item.sort_order || 0);
    const targetSort = Number(target.sort_order || 0);
    const tempSort = Math.max(
      ...siblingRows.map((row) => Number(row.sort_order || 0)),
      currentSort,
      targetSort,
      0,
    ) + 1000;

    const patchSortOrder = async (categoryId, sortOrder) => {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${categoryId}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...authHeader,
        },
        body: JSON.stringify({ sort_order: sortOrder }),
      });
      const payload = await safeParseJson(response);
      if (!response.ok) {
        const parsed = parseApiError(payload, "Sıra güncellemesi başarısız.");
        throw new Error(parsed.message);
      }
    };

    setLevel0OrderMovingId(item.id);
    try {
      await patchSortOrder(item.id, tempSort);
      await patchSortOrder(target.id, currentSort);
      await patchSortOrder(item.id, targetSort);
      toast({
        title: "Ana sayfa sırası güncellendi",
        description: `${item.name} yeni sıra: ${targetSort}`,
      });
      await fetchItems();
    } catch (error) {
      toast({
        title: "Sıralama güncellenemedi",
        description: error?.message || "Bilinmeyen hata",
        variant: "destructive",
      });
    } finally {
      setLevel0OrderMovingId("");
    }
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
        return [...prev, createSubcategoryDraft()];
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
      slug: node.slug.trim(),
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
    const slug = form.slug.trim();
    const country = (form.country_code || "").trim().toUpperCase();
    const moduleValue = (form.module || "").trim().toLowerCase();
    const isVehicleModule = moduleValue === "vehicle";
    const rootSortOrder = Number(form.sort_order || 0);

    const mainFieldErrors = {};
    if (!name) {
      mainFieldErrors.main_name = "Modül adı zorunludur.";
    }
    if (!slug) {
      mainFieldErrors.main_slug = "Slug zorunludur.";
    }
    if (!country) {
      mainFieldErrors.main_country = "Ülke zorunludur.";
    }
    if (!moduleValue) {
      mainFieldErrors.main_module = "Modül zorunludur.";
    }
    if (isRootCategory && !form.image_url?.trim()) {
      mainFieldErrors.main_image_url = "Modül görseli zorunludur.";
    }

    const iconSvgRaw = String(form.icon_svg || "").trim();
    if (iconSvgRaw) {
      const lowered = iconSvgRaw.toLowerCase();
      if (iconSvgRaw.length > CATEGORY_ICON_SVG_MAX_LENGTH) {
        mainFieldErrors.main_icon_svg = `İkon SVG en fazla ${CATEGORY_ICON_SVG_MAX_LENGTH} karakter olabilir.`;
      } else if (!lowered.includes("<svg") || !lowered.includes("</svg>")) {
        mainFieldErrors.main_icon_svg = "İkon SVG geçerli bir <svg>...</svg> içermelidir.";
      } else if (isCategoryIconSvgUnsafe(iconSvgRaw)) {
        mainFieldErrors.main_icon_svg = "İkon SVG güvenli olmayan içerik içeriyor.";
      }
    }

    if (Object.keys(mainFieldErrors).length > 0) {
      setHierarchyFieldErrors(mainFieldErrors);
      setHierarchyError("Lütfen işaretli alanları doldurun.");
      return { success: false };
    }

    setCategoryIconSvgError("");

    if (isVehicleModule) {
      setVehicleSegmentError("");
    }

    const hasCompletedSubcategory = subcategories.some((node) => node.name?.trim() && node.slug?.trim());
    if (!isVehicleModule && !hasCompletedSubcategory) {
      setHierarchyError("En az 1 seviye kategorisi tamamlanmalıdır.");
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

    const normalizeTree = (nodes = []) => (nodes || [])
      .map((node, index) => {
        const parsedSort = Number(node.sort_order);
        const resolvedSort = Number.isFinite(parsedSort) && parsedSort > 0 ? parsedSort : index + 1;
        return {
          ...node,
          name: node.name ? node.name.trim() : "",
          slug: node.slug ? node.slug.trim() : "",
          sort_order: resolvedSort,
          is_complete: true,
          is_leaf: Boolean(node.is_leaf),
          children: node.is_leaf ? [] : normalizeTree(node.children || []),
        };
      });

    const treeFieldErrors = {};
    const validateTree = (nodes, levelIndex = 0) => {
      if (levelIndex === 0 && nodes.length === 0) {
        return "Seviye 1 için en az bir kategori eklenmelidir.";
      }

      const slugKeys = new Set();

      for (let index = 0; index < nodes.length; index += 1) {
        const node = nodes[index];
        const pathKey = `${levelIndex}-${index}`;
        const label = `Seviye ${levelIndex + 1}.${index + 1}`;
        if (!node.name) treeFieldErrors[`level-${pathKey}-name`] = "Ad zorunludur.";
        if (!node.slug) treeFieldErrors[`level-${pathKey}-slug`] = "Slug zorunludur.";
        const rawSort = node.sort_order;
        const hasSort = rawSort !== "" && rawSort !== null && rawSort !== undefined;
        if (hasSort) {
          const sortValue = Number(rawSort);
          if (!Number.isFinite(sortValue) || sortValue <= 0) {
            treeFieldErrors[`level-${pathKey}-sort`] = "Sıra 1 veya daha büyük olmalıdır.";
          }
        }

        const slugValue = (node.slug || "").trim().toLowerCase();
        if (slugValue) {
          if (slugKeys.has(slugValue)) {
            treeFieldErrors[`level-${pathKey}-slug`] = "Bu seviyede slug tekrar edemez.";
          }
          slugKeys.add(slugValue);
        }

        if (!node.is_leaf) {
          const children = Array.isArray(node.children) ? node.children : [];
          if (children.length === 0) {
            node.is_leaf = true;
            node.children = [];
          } else {
            const nestedError = validateTree(children, levelIndex + 1);
            if (nestedError) return nestedError;
          }
        }
      }

      if (Object.keys(treeFieldErrors).length > 0) {
        return `Seviye ${levelIndex + 1} için alanları tamamlayın.`;
      }
      return "";
    };

    const cleanedSubs = isVehicleModule ? [] : normalizeTree(subcategories);
    if (!isVehicleModule) {
      const validationError = validateTree(cleanedSubs);
      if (validationError) {
        if (Object.keys(treeFieldErrors).length > 0) {
          setHierarchyFieldErrors(treeFieldErrors);
        }
        setHierarchyError(validationError);
        return { success: false };
      }
    }

    const persistSubcategories = async (nodes, parentId) => {
      const savedNodes = [];
      for (const node of nodes) {
        const basePayload = {
          name: node.name,
          slug: node.slug,
          parent_id: parentId,
          country_code: country,
          module: moduleValue,
          active_flag: node.active_flag,
          sort_order: Number(node.sort_order || 0),
          hierarchy_complete: true,
        };
        if (node.transaction_type) {
          basePayload.form_schema = {
            status: "draft",
            category_meta: { transaction_type: node.transaction_type },
          };
        }
        const url = node.id
          ? `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${node.id}`
          : `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories`;
        const method = node.id ? "PATCH" : "POST";
        let data = {};
        if (method === "POST") {
          const created = await createCategoryWithSortFallback(basePayload, "Kategori kaydedilemedi.");
          if (!created.ok) {
            throw new Error(created.parsed.message);
          }
          if (created.selfHealed) {
            toast({
              title: "Kayıt yeniden bağlandı",
              description: `${node.name || "Kategori"} mevcut kayıtla eşlendi ve akış devam etti.`,
            });
          }
          data = created.data;
        } else {
          const mutation = await requestCategoryMutationWithRetry({
            url,
            method,
            payload: basePayload,
            fallbackMessage: "Kategori kaydedilemedi.",
            retries: 3,
            selfHealContext: {
              categoryId: node.id || "",
              slug: basePayload.slug,
              name: basePayload.name,
              moduleValue: basePayload.module,
              countryCode: basePayload.country_code,
              parentId,
              parentIsRoot: !parentId,
            },
          });
          if (!mutation.ok) {
            throw new Error(mutation.parsed.message);
          }
          if (mutation.selfHealed) {
            toast({
              title: "Kayıt yeniden bağlandı",
              description: `${node.name || "Kategori"} güncel kayıtla eşlenerek kaydedildi.`,
            });
          }
          data = mutation.data;
        }
        const saved = data?.category || node;
        const childNodes = node.is_leaf ? [] : await persistSubcategories(node.children || [], saved.id || node.id);
        savedNodes.push({
          ...node,
          id: saved.id || node.id,
          is_complete: true,
          children: childNodes,
        });
      }
      return savedNodes;
    };

    try {
      let updatedParent = editing;

      if (editing) {
        const mutation = await requestCategoryMutationWithRetry({
          url: `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${editing.id}`,
          method: "PATCH",
          payload: {
            name,
            slug,
            country_code: country,
            module: moduleValue,
            image_url: isRootCategory ? (form.image_url || "") : "",
            icon_svg: isRootCategory ? (form.icon_svg || "") : "",
            vehicle_segment: isVehicleModule ? vehicleSegment : undefined,
            active_flag: form.active_flag,
            sort_order: rootSortOrder,
            hierarchy_complete: true,
            wizard_progress: { state: progressState, dirty_steps: dirtyStepsOverride },
            wizard_edit_event: wizardEditEvent || undefined,
            expected_updated_at: editing.updated_at,
          },
          fallbackMessage: "Kategori güncellenemedi.",
          retries: 3,
          selfHealContext: {
            categoryId: editing.id,
            slug,
            name,
            moduleValue,
            countryCode: country,
            parentId: form.parent_id,
            parentIsRoot: !form.parent_id,
          },
        });
        if (!mutation.ok) {
          const parsed = mutation.parsed;
          applyParsedCategoryError(parsed, { setGeneral: true });
          return { success: false };
        }
        if (mutation.selfHealed) {
          toast({
            title: "Kayıt yeniden bağlandı",
            description: "Stale kayıt tespit edildi, güncel kayıtla düzenleme akışı devam etti.",
          });
        }
        const data = mutation.data;
        updatedParent = data?.category || editing;
      } else {
        const parentPayload = {
          name,
          slug,
          country_code: country,
          module: moduleValue,
          image_url: isRootCategory ? (form.image_url || "") : "",
          icon_svg: isRootCategory ? (form.icon_svg || "") : "",
          vehicle_segment: isVehicleModule ? vehicleSegment : undefined,
          active_flag: form.active_flag,
          sort_order: rootSortOrder,
          hierarchy_complete: isVehicleModule,
          wizard_progress: { state: progressState, dirty_steps: dirtyStepsOverride },
        };
        const createdParent = await createCategoryWithSortFallback(parentPayload, "Modül oluşturulamadı.");
        if (!createdParent.ok) {
          const parsed = createdParent.parsed;
          applyParsedCategoryError(parsed, { setGeneral: true });
          return { success: false };
        }
        if (createdParent.selfHealed) {
          toast({
            title: "Mevcut kayıt kullanıldı",
            description: "Yeni kayıt yerine mevcut kategori bulundu; akış bu kayıtla devam ediyor.",
          });
        }
        if (createdParent.autoAdjusted && createdParent.payload?.sort_order) {
          setForm((prev) => ({ ...prev, sort_order: String(createdParent.payload.sort_order) }));
          toast({
            title: "Sıra otomatik düzeltildi",
            description: `Modül için sıra ${createdParent.payload.sort_order} olarak güncellendi.`,
          });
        }
        if (createdParent.payload?.slug && createdParent.payload.slug !== slug) {
          setForm((prev) => ({ ...prev, slug: createdParent.payload.slug }));
          toast({
            title: "Slug otomatik düzeltildi",
            description: `Modül slug değeri ${createdParent.payload.slug} olarak güncellendi.`,
          });
        }
        updatedParent = createdParent.data?.category;
      }

      const savedSubs = isVehicleModule ? [] : await persistSubcategories(cleanedSubs, updatedParent.id);

      if (!editing && updatedParent?.id && !isVehicleModule) {
        const patchMutation = await requestCategoryMutationWithRetry({
          url: `${process.env.REACT_APP_BACKEND_URL}/api/admin/categories/${updatedParent.id}`,
          method: "PATCH",
          payload: { hierarchy_complete: true, wizard_progress: { state: progressState, dirty_steps: dirtyStepsOverride } },
          fallbackMessage: "Kategori güncellenemedi.",
          retries: 3,
          selfHealContext: {
            categoryId: updatedParent.id,
            slug,
            name,
            moduleValue,
            countryCode: country,
            parentId: form.parent_id,
            parentIsRoot: !form.parent_id,
          },
        });
        if (!patchMutation.ok) {
          const parsed = patchMutation.parsed;
          applyParsedCategoryError(parsed, { setGeneral: true });
          return { success: false };
        }
        const patchData = patchMutation.data;
        updatedParent = patchData?.category || updatedParent;
      }

      applyCategoryFromServer(updatedParent, { clearEditMode: editModeStep === "hierarchy" });
      const nextSubcategories = savedSubs.length ? savedSubs : [createSubcategoryDraft()];
      setSubcategories(nextSubcategories);
      setLevelSelections([]);
      setLevelCompletion({});
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

  const moveLevelItem = (levelIndex, fromIndex, toIndex) => {
    if (fromIndex === toIndex || fromIndex === null || toIndex === null) return;
    if (levelIndex === 0) {
      setSubcategories((prev) => reorderArray(prev, fromIndex, toIndex).map((item, idx) => ({
        ...item,
        sort_order: Number(item.sort_order || idx + 1),
      })));
      return;
    }
    const parentPath = getParentPathForLevel(levelIndex);
    setSubcategories((prev) => updateNodeByPath(prev, parentPath, (node) => {
      const reordered = reorderArray(node.children || [], fromIndex, toIndex).map((child, idx) => ({
        ...child,
        sort_order: Number(child.sort_order || idx + 1),
      }));
      return { ...node, children: reordered };
    }));
  };

  const renderLevelColumns = () => {
    const columns = [];
    let levelIndex = 0;
    let itemsAtLevel = subcategories;
    let parentPath = [];

    while (true) {
      columns.push({
        levelIndex,
        items: itemsAtLevel,
        parentPath,
        selectedIndex: levelSelections[levelIndex],
      });

      const selectedIndex = levelSelections[levelIndex];
      const selectedItem = selectedIndex !== undefined ? itemsAtLevel[selectedIndex] : null;
      if (!selectedItem || selectedItem.is_leaf || !levelCompletion[levelIndex]) {
        break;
      }
      parentPath = [...parentPath, selectedIndex];
      itemsAtLevel = selectedItem.children || [];
      levelIndex += 1;
    }

    return (
      <div className="flex gap-4 overflow-x-auto pb-2" data-testid="categories-level-builder">
        {columns.map((column) => {
          const { levelIndex, items, parentPath, selectedIndex } = column;
          const levelLabel = `Level ${levelIndex + 1}`;
          const levelLocked = isHierarchyLocked || Boolean(levelCompletion[levelIndex]);

          return (
            <div
              key={`level-${levelIndex}`}
              className="min-w-[320px] max-w-[360px] rounded-lg border bg-white p-3 space-y-3"
              data-testid={`categories-level-column-${levelIndex}`}
            >
              <div className="flex items-center justify-between gap-2" data-testid={`categories-level-header-${levelIndex}`}>
                <div>
                  <div className="text-[11px] text-slate-500">Seviye {levelIndex + 1}</div>
                  <div className="text-sm font-semibold text-slate-900" data-testid={`categories-level-title-${levelIndex}`}>
                    {levelLabel}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {levelCompletion[levelIndex] ? (
                    <button
                      type="button"
                      className="text-xs border rounded px-2 py-1"
                      onClick={() => handleLevelEditColumn(levelIndex, items)}
                      data-testid={`categories-level-edit-${levelIndex}`}
                    >
                      Düzenle
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="text-xs text-white bg-[var(--brand-navy-deep)] rounded px-3 py-1 disabled:opacity-60"
                      onClick={() => handleLevelComplete(levelIndex, items)}
                      disabled={isHierarchyLocked}
                      data-testid={`categories-level-complete-${levelIndex}`}
                    >
                      Onayla
                    </button>
                  )}
                </div>
              </div>

              <div className="space-y-3" data-testid={`categories-level-items-${levelIndex}`}>
                {items.length === 0 ? (
                  <div className="text-xs text-slate-500" data-testid={`categories-level-empty-${levelIndex}`}>
                    Bu seviyede kategori yok.
                  </div>
                ) : items.map((item, itemIndex) => {
                  const itemPath = [...parentPath, itemIndex];
                  const nameError = hierarchyFieldErrors[`level-${levelIndex}-${itemIndex}-name`];
                  const slugError = hierarchyFieldErrors[`level-${levelIndex}-${itemIndex}-slug`];
                  const sortError = hierarchyFieldErrors[`level-${levelIndex}-${itemIndex}-sort`];
                  const isSelected = selectedIndex === itemIndex;
                  const canFill = levelCompletion[levelIndex] && !item.is_leaf && !isHierarchyLocked;
                  const dragDisabled = levelLocked;

                  return (
                    <div
                      key={`level-${levelIndex}-item-${itemIndex}`}
                      className={`rounded-md border p-2 space-y-2 ${isSelected ? 'border-slate-900 bg-slate-50' : 'border-slate-200'}`}
                      data-testid={`categories-level-item-${levelIndex}-${itemIndex}`}
                      draggable={!dragDisabled}
                      onDragStart={() => {
                        setDraggingLevelIndex(levelIndex);
                        setDraggingItemIndex(itemIndex);
                      }}
                      onDragOver={(event) => event.preventDefault()}
                      onDrop={() => {
                        if (draggingLevelIndex === levelIndex && draggingItemIndex !== null) {
                          moveLevelItem(levelIndex, draggingItemIndex, itemIndex);
                        }
                        setDraggingLevelIndex(null);
                        setDraggingItemIndex(null);
                      }}
                      onDragEnd={() => {
                        setDraggingLevelIndex(null);
                        setDraggingItemIndex(null);
                      }}
                    >
                      <div className="flex items-center justify-between gap-2">
                        <div className="text-xs font-semibold text-slate-700" data-testid={`categories-level-item-label-${levelIndex}-${itemIndex}`}>
                          {`Kategori ${levelIndex + 1}.${itemIndex + 1}`} <span className="text-slate-400">↕</span>
                        </div>
                        <div className="flex items-center gap-2">
                          {item.inherit_children ? (
                            <span className="text-[11px] font-semibold text-indigo-600" data-testid={`categories-level-item-inherit-badge-${levelIndex}-${itemIndex}`}>
                              Miraslı
                            </span>
                          ) : null}
                          <span className={`text-[11px] font-semibold ${item.is_leaf ? 'text-amber-600' : 'text-emerald-600'}`} data-testid={`categories-level-item-leaf-badge-${levelIndex}-${itemIndex}`}>
                            {item.is_leaf ? 'Leaf' : 'Dal Açık'}
                          </span>
                        </div>
                      </div>

                      <input
                        className={inputClassName}
                        placeholder={`Seviye ${levelIndex + 1} ad`}
                        value={item.name}
                        disabled={levelLocked}
                        onChange={(e) => updateLevelItem(levelIndex, itemIndex, { name: e.target.value })}
                        data-testid={`categories-level-item-name-${levelIndex}-${itemIndex}`}
                      />
                      {nameError ? <div className="text-[11px] text-rose-600">{nameError}</div> : null}

                      <input
                        className={inputClassName}
                        placeholder={`Seviye ${levelIndex + 1} slug`}
                        value={item.slug}
                        disabled={levelLocked}
                        onChange={(e) => updateLevelItem(levelIndex, itemIndex, { slug: e.target.value })}
                        data-testid={`categories-level-item-slug-${levelIndex}-${itemIndex}`}
                      />
                      {slugError ? <div className="text-[11px] text-rose-600">{slugError}</div> : null}

                      <input
                        type="number"
                        min={1}
                        className={inputClassName}
                        placeholder="Sıra"
                        value={item.sort_order || ''}
                        disabled={levelLocked}
                        onChange={(e) => updateLevelItem(levelIndex, itemIndex, { sort_order: e.target.value })}
                        data-testid={`categories-level-item-sort-${levelIndex}-${itemIndex}`}
                      />
                      {sortError ? <div className="text-[11px] text-rose-600">{sortError}</div> : null}

                      <label className="flex items-center gap-2 text-xs text-slate-700" data-testid={`categories-level-item-active-${levelIndex}-${itemIndex}`}>
                        <input
                          type="checkbox"
                          checked={item.active_flag}
                          disabled={levelLocked}
                          onChange={(e) => updateLevelItem(levelIndex, itemIndex, { active_flag: e.target.checked })}
                          data-testid={`categories-level-item-active-input-${levelIndex}-${itemIndex}`}
                        />
                        Aktif
                      </label>

                      <label className="flex items-center gap-2 text-xs text-slate-700" data-testid={`categories-level-item-leaf-${levelIndex}-${itemIndex}`}>
                        <input
                          type="checkbox"
                          checked={Boolean(item.is_leaf)}
                          disabled={levelLocked}
                          onChange={(e) => {
                            updateLevelItem(levelIndex, itemIndex, { is_leaf: e.target.checked });
                            if (e.target.checked && isSelected) {
                              setLevelSelections((prev) => prev.slice(0, levelIndex + 1));
                              resetLevelCompletionFrom(levelIndex + 1);
                            }
                          }}
                          data-testid={`categories-level-item-leaf-input-${levelIndex}-${itemIndex}`}
                        />
                        Bu dal burada bitti (leaf)
                      </label>
                      {hierarchyFieldErrors[`level-${levelIndex}-${itemIndex}-children`] ? (
                        <div className="text-[11px] text-rose-600">
                          {hierarchyFieldErrors[`level-${levelIndex}-${itemIndex}-children`]}
                        </div>
                      ) : null}

                      <div className="flex flex-wrap items-center gap-2">
                        {!item.is_leaf ? (
                          <button
                            type="button"
                            className="text-xs text-white bg-[var(--brand-navy-deep)] rounded px-3 py-1 disabled:opacity-60"
                            onClick={() => handleLevelSelect(levelIndex, itemIndex)}
                            disabled={!canFill}
                            data-testid={`categories-level-item-fill-${levelIndex}-${itemIndex}`}
                          >
                            Altını Doldur
                          </button>
                        ) : null}
                        {item.inherit_children ? (
                          <button
                            type="button"
                            className="text-xs border rounded px-2 py-1 disabled:opacity-60"
                            onClick={() => handleBreakInheritance(levelIndex, itemIndex)}
                            disabled={levelLocked}
                            data-testid={`categories-level-item-inherit-break-${levelIndex}-${itemIndex}`}
                          >
                            Mirası Kopar
                          </button>
                        ) : null}
                        <button
                          type="button"
                          className="text-xs text-rose-600 border rounded px-2 py-1 disabled:opacity-60"
                          onClick={() => removeLevelItem(levelIndex, itemIndex)}
                          disabled={levelLocked}
                          data-testid={`categories-level-item-remove-${levelIndex}-${itemIndex}`}
                        >
                          Sil
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>

              <button
                type="button"
                className="w-full text-sm border rounded px-3 py-2 disabled:opacity-60"
                onClick={() => addLevelItem(levelIndex)}
                disabled={levelLocked}
                data-testid={`categories-level-add-${levelIndex}`}
              >
                Kategori Ekle
              </button>
            </div>
          );
        })}
      </div>
    );
  };

  const hierarchyLiveRows = useMemo(() => {
    const rows = [];
    const walk = (nodes, level, path) => {
      nodes.forEach((node, index) => {
        const nextPath = [...path, index];
        const missing = !node?.name?.trim() || !node?.slug?.trim() || !Number.isFinite(Number(node?.sort_order)) || Number(node?.sort_order) <= 0;
        rows.push({
          key: nextPath.join("-"),
          label: node?.name?.trim() || "(eksik ad)",
          level,
          missing,
          is_leaf: Boolean(node?.is_leaf),
        });
        if (!node?.is_leaf && Array.isArray(node.children) && node.children.length > 0) {
          walk(node.children, level + 1, nextPath);
        }
      });
    };
    walk(subcategories, 1, []);
    return rows;
  }, [subcategories]);

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
        <div className="flex items-center gap-2" data-testid="categories-header-actions">
          <button
            type="button"
            className="px-4 py-2 border border-emerald-300 text-emerald-700 bg-emerald-50 rounded"
            onClick={handleSeedRealEstateStandard}
            disabled={seedLoading}
            data-testid="categories-seed-real-estate-standard"
          >
            {seedLoading ? 'Uygulanıyor...' : 'Standart Emlak Şeması'}
          </button>
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded"
            onClick={handleCreate}
            data-testid="categories-create-open"
          >
            Kayıt Yönetimi
          </button>
        </div>
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

            <div className="flex flex-wrap items-center gap-1" data-testid="categories-list-filter-issue-state">
              {[
                { value: 'all', label: 'Tüm Kayıtlar' },
                { value: 'with_issues', label: 'Sorunlu Kayıtlar' },
              ].map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setListFilters((prev) => ({ ...prev, issue_state: option.value }))}
                  className={`h-9 rounded-md border px-3 text-sm ${listFilters.issue_state === option.value ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-300 text-slate-800'}`}
                  data-testid={`categories-list-filter-issue-state-${option.value}`}
                >
                  {option.label}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2" data-testid="categories-list-filter-search-wrap">
              <input
                type="text"
                value={listFilters.search_query}
                onChange={(event) => setListFilters((prev) => ({ ...prev, search_query: event.target.value }))}
                placeholder="Ad / slug ara"
                className="h-9 w-48 rounded-md border border-slate-300 px-3 text-sm"
                data-testid="categories-list-filter-search-input"
              />
              <select
                className="h-9 rounded-md border border-slate-300 px-2 text-sm"
                value={listFilters.sort_by}
                onChange={(event) => setListFilters((prev) => ({ ...prev, sort_by: event.target.value }))}
                data-testid="categories-list-filter-sort-select"
              >
                <option value="name_asc">Ad (A-Z)</option>
                <option value="name_desc">Ad (Z-A)</option>
                <option value="sort_asc">Sıra (artan)</option>
                <option value="sort_desc">Sıra (azalan)</option>
              </select>
            </div>
          </div>

          <div className="flex flex-col items-end gap-2" data-testid="categories-list-selection-meta">
            <div className="text-xs text-slate-600">
              Seçili: <span className="font-semibold" data-testid="categories-list-selection-count">{selectedIds.length}</span> •
              Görünen: <span className="font-semibold" data-testid="categories-list-visible-count">{visibleItems.length}</span>
            </div>
            <div className="flex flex-wrap items-center justify-end gap-2" data-testid="categories-list-active-filter-chips-wrap">
              {activeFilterChips.map((chip) => (
                <span
                  key={`categories-filter-chip-${chip.key}`}
                  className="rounded border border-slate-300 bg-white px-2 py-1 text-[11px] text-slate-700"
                  data-testid={`categories-list-active-filter-chip-${chip.key}`}
                >
                  {chip.label}
                </span>
              ))}
              {activeFilterChips.length > 0 ? (
                <button
                  type="button"
                  onClick={() => setListFilters({
                    module: "all",
                    status: "all",
                    image_presence: "all",
                    issue_state: "all",
                    sort_by: "name_asc",
                    search_query: "",
                  })}
                  className="h-7 rounded border border-slate-300 px-2 text-[11px]"
                  data-testid="categories-list-clear-filters"
                >
                  Filtreleri Temizle
                </button>
              ) : null}
            </div>
          </div>
        </div>

        {lastDeleteUndo && undoSecondsLeft > 0 ? (
          <div className="border-b border-indigo-200 bg-indigo-50 px-4 py-3" data-testid="categories-delete-undo-bar">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-xs text-indigo-800" data-testid="categories-delete-undo-message">
                Son silme işlemini geri alabilirsiniz. Kalan süre: <span className="font-semibold" data-testid="categories-delete-undo-seconds">{undoSecondsLeft}s</span>
              </div>
              <button
                type="button"
                onClick={handleUndoDelete}
                className="h-8 rounded border border-indigo-300 bg-white px-3 text-xs text-indigo-800"
                data-testid="categories-delete-undo-button"
              >
                Silmeyi Geri Al
              </button>
            </div>
          </div>
        ) : null}

        <div className="border-b bg-slate-50 px-4 py-3" data-testid="categories-undo-history-panel">
          <div className="flex items-center justify-between gap-2" data-testid="categories-undo-history-header">
            <p className="text-xs font-semibold text-slate-700" data-testid="categories-undo-history-title">Son 24 Saat Silme/Undo Geçmişi</p>
            <button
              type="button"
              onClick={() => fetchUndoOperations()}
              className="h-8 rounded border border-slate-300 bg-white px-2 text-xs"
              data-testid="categories-undo-history-refresh"
            >
              Yenile
            </button>
          </div>
          <div className="mt-2 space-y-1" data-testid="categories-undo-history-list">
            {undoOperationsLoading ? (
              <p className="text-xs text-slate-500" data-testid="categories-undo-history-loading">Yükleniyor...</p>
            ) : undoOperations.length === 0 ? (
              <p className="text-xs text-slate-500" data-testid="categories-undo-history-empty">Kayıt bulunamadı.</p>
            ) : undoOperations.map((item, index) => (
              <div key={`undo-op-${item.operation_id}-${index}`} className="flex flex-wrap items-center justify-between gap-2 rounded border bg-white px-2 py-2 text-xs" data-testid={`categories-undo-history-item-${index}`}>
                <div className="min-w-0">
                  <p className="font-semibold text-slate-800" data-testid={`categories-undo-history-item-id-${index}`}>{item.operation_id}</p>
                  <p className="text-slate-600" data-testid={`categories-undo-history-item-meta-${index}`}>
                    deleted: {Number(item.deleted_count || 0)} • created: {item.created_at ? formatDateTimeShort(item.created_at) : '-'}
                  </p>
                </div>
                <span
                  className={`rounded border px-2 py-1 ${item.is_restored ? 'border-emerald-300 bg-emerald-50 text-emerald-700' : item.is_expired ? 'border-slate-300 bg-slate-100 text-slate-700' : 'border-amber-300 bg-amber-50 text-amber-700'}`}
                  data-testid={`categories-undo-history-item-status-${index}`}
                >
                  {item.is_restored ? 'Geri Alındı' : item.is_expired ? 'Süresi Doldu' : 'Aktif'}
                </span>
              </div>
            ))}
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

        <div className="border-b px-4 py-3 bg-slate-50" data-testid="categories-hierarchy-preview-wrap">
          <div className="flex items-center justify-between gap-2">
            <div className="text-sm font-semibold text-slate-900" data-testid="categories-hierarchy-preview-title">
              Hiyerarşi Önizleme (L1 → L6)
            </div>
            <div className="text-xs text-slate-500" data-testid="categories-hierarchy-preview-meta">
              Toplam düğüm: {hierarchyPreviewRows.length}
            </div>
          </div>

          <div className="mt-2 max-h-52 overflow-auto rounded border bg-white p-2" data-testid="categories-hierarchy-preview-list">
            {hierarchyPreviewRows.length === 0 ? (
              <div className="text-xs text-slate-500" data-testid="categories-hierarchy-preview-empty">Önizleme için kategori bulunamadı.</div>
            ) : hierarchyPreviewRows.map((row) => (
              <div
                key={row.id}
                className="flex items-center justify-between gap-2 py-1 text-xs"
                style={{ paddingLeft: `${Math.min(row.level - 1, 6) * 16}px` }}
                data-testid={`categories-hierarchy-preview-row-${row.id}`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-700" data-testid={`categories-hierarchy-preview-level-${row.id}`}>
                    L{row.level}
                  </span>
                  <span className="truncate text-slate-800" data-testid={`categories-hierarchy-preview-name-${row.id}`}>{row.name}</span>
                </div>
                <span className="text-slate-500 whitespace-nowrap" data-testid={`categories-hierarchy-preview-count-${row.id}`}>
                  ({row.listing_count})
                </span>
              </div>
            ))}
          </div>
        </div>

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
            const level0Siblings = visibleItems
              .filter(
                (row) => !row.parent_id
                  && row.module === item.module
                  && String(row.country_code || "") === String(item.country_code || "")
              )
              .sort((a, b) => {
                const sortCmp = Number(a.sort_order || 0) - Number(b.sort_order || 0);
                if (sortCmp !== 0) return sortCmp;
                return String(a.name || "").localeCompare(String(b.name || ""), "tr");
              });
            const currentSiblingIndex = level0Siblings.findIndex((row) => row.id === item.id);
            const canMoveUp = currentSiblingIndex > 0;
            const canMoveDown = currentSiblingIndex >= 0 && currentSiblingIndex < level0Siblings.length - 1;
            const isMovePending = level0OrderMovingId === item.id;
            const rowIssueBadges = getCategoryListIssueBadges(item);
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
                    ) : item.icon_svg ? (
                      <CategoryIconSvg
                        iconSvg={item.icon_svg}
                        wrapperClassName="h-full w-full rounded border-0 bg-white p-1"
                        fallbackClassName="h-full w-full rounded border-0 bg-slate-100 text-slate-500"
                        fallbackText="SVG"
                        testId={`categories-row-icon-svg-preview-${item.id}`}
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center text-[10px] font-semibold text-slate-500" data-testid={`categories-row-image-placeholder-${item.id}`}>
                        —
                      </div>
                    )}
                  </div>
                </div>
                <div className="font-semibold text-slate-900" style={{ paddingLeft: `${Math.min(Number(item.depth || 0), 5) * 12}px` }} data-testid={`categories-row-name-${item.id}`}>
                  <div className="truncate">{item.name}</div>
                  {rowIssueBadges.length > 0 ? (
                    <div className="mt-1 flex flex-wrap items-center gap-1" data-testid={`categories-row-issue-badges-${item.id}`}>
                      {rowIssueBadges.map((badge) => (
                        <span
                          key={`${item.id}-${badge.key}`}
                          className="rounded border border-amber-300 bg-amber-50 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700"
                          data-testid={`categories-row-issue-badge-${item.id}-${badge.key}`}
                        >
                          {badge.label}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
                <div className="text-slate-800" data-testid={`categories-row-slug-${item.id}`}>{item.slug}</div>
                <div className="text-slate-800" data-testid={`categories-row-country-${item.id}`}>{item.country_code || "global"}</div>
                <div className="text-slate-800" data-testid={`categories-row-module-${item.id}`}>
                  {CATEGORY_MODULE_OPTIONS.find((option) => option.value === item.module)?.label || item.module || '-'}
                </div>
                <div className="text-slate-800" data-testid={`categories-row-sort-${item.id}`}>{item.sort_order}</div>
                <div>
                  <span className={`px-2 py-1 rounded text-xs ${item.active_flag ? "bg-green-100 text-green-700" : "bg-gray-100 text-slate-800"}`} data-testid={`categories-row-status-${item.id}`}>
                    {item.active_flag ? "Aktif" : "Pasif"}
                  </span>
                </div>
                <div className="flex justify-end gap-2 text-slate-900" data-testid={`categories-row-actions-${item.id}`}>
                  <button
                    className="text-sm px-2 py-1 border rounded disabled:opacity-50"
                    onClick={() => handleMoveLevel0Order(item, "up")}
                    disabled={!canMoveUp || Boolean(level0OrderMovingId)}
                    data-testid={`categories-order-up-${item.id}`}
                    title="Level 0 ana sayfa sırasını yukarı al"
                  >
                    ↑
                  </button>
                  <button
                    className="text-sm px-2 py-1 border rounded disabled:opacity-50"
                    onClick={() => handleMoveLevel0Order(item, "down")}
                    disabled={!canMoveDown || Boolean(level0OrderMovingId)}
                    data-testid={`categories-order-down-${item.id}`}
                    title="Level 0 ana sayfa sırasını aşağı al"
                  >
                    ↓
                  </button>
                  <button className="text-sm px-3 py-1 border rounded" onClick={() => handleEdit(item)} data-testid={`categories-edit-${item.id}`}>
                    Düzenle
                  </button>
                  <button className="text-sm px-3 py-1 border rounded" onClick={() => handleToggle(item)} data-testid={`categories-toggle-${item.id}`}>
                    {item.active_flag ? "Pasif Et" : "Aktif Et"}
                  </button>
                  <button className="text-sm px-3 py-1 border rounded" onClick={() => handleDelete(item)} data-testid={`categories-delete-${item.id}`}>
                    Sil
                  </button>
                  {isMovePending ? (
                    <span className="text-xs text-slate-500" data-testid={`categories-order-pending-${item.id}`}>Sıra güncelleniyor...</span>
                  ) : null}
                </div>
              </div>
            );
          })
        )}
      </div>

      {modalOpen && (
        <div className={`fixed inset-0 bg-black/40 z-50 ${isModalFullscreen ? '' : 'flex items-center justify-center'}`} data-testid="categories-modal">
          <div className={`bg-white p-6 text-slate-900 ${isModalFullscreen ? '' : 'rounded-lg shadow-xl'}`} style={modalPanelStyle} data-testid="categories-modal-panel">
            <div className="flex items-start justify-between mb-4 gap-3" data-testid="categories-record-management-header">
              <div>
                <h2 className="text-lg font-semibold" data-testid="categories-modal-title">Kategori Kayıt Yönetimi</h2>
                <p className="text-xs text-slate-500" data-testid="categories-modal-title-subtext">
                  Yeni ve mevcut kayıtlar tek akışta yönetilir; 404/409 durumunda sistem otomatik yeniden bağlanmayı dener.
                </p>
              </div>
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

              <div className="flex flex-wrap items-center gap-2" data-testid="categories-modal-issue-mini-badges">
                {modalIssueBadges.map((badge) => (
                  <span
                    key={`modal-issue-${badge.id}`}
                    className={`rounded border px-2 py-1 text-[11px] font-semibold ${badge.hasIssue ? 'border-rose-300 bg-rose-50 text-rose-700' : 'border-emerald-300 bg-emerald-50 text-emerald-700'}`}
                    data-testid={`categories-modal-issue-badge-${badge.id}`}
                  >
                    {badge.label}: {badge.hasIssue ? 'Uyarı' : 'OK'}
                  </span>
                ))}
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
                      <h3 className="text-md font-semibold">Modül (Root Node)</h3>
                      {isHierarchyLocked ? (
                        canEditUnlock ? (
                          <button
                            type="button"
                            className="text-xs border rounded px-2 py-1"
                            onClick={handleHierarchyEdit}
                            data-testid="categories-hierarchy-edit"
                          >
                            Düzenle
                          </button>
                        ) : (
                          <span className="text-xs text-amber-700" data-testid="categories-hierarchy-edit-no-permission">
                            Hiyerarşi kilitli (düzenleme yetkisi gerekli)
                          </span>
                        )
                      ) : (
                        editing && (
                          <span className="text-xs text-emerald-700" data-testid="categories-hierarchy-edit-mode-open">
                            Düzenleme modu açık
                          </span>
                        )
                      )}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <div className="space-y-1">
                        <label className={labelClassName}>Modül adı</label>
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
                        <label className={labelClassName}>Modül görseli</label>
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

                      <div className="space-y-2 md:col-span-2" data-testid="categories-icon-svg-section">
                        <label className={labelClassName}>Kategori ikonu (SVG)</label>
                        {isRootCategory ? (
                          <div className="rounded-md border border-dashed border-slate-300 p-3 space-y-3" data-testid="categories-icon-svg-editor">
                            <div className="flex items-center gap-2" data-testid="categories-icon-svg-tabs">
                              <button
                                type="button"
                                className={`h-8 rounded-md border px-3 text-xs font-semibold ${iconPickerTab === 'library' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-700 border-slate-300'}`}
                                onClick={() => setIconPickerTab('library')}
                                disabled={isHierarchyLocked}
                                data-testid="categories-icon-tab-library"
                              >
                                Kütüphane
                              </button>
                              <button
                                type="button"
                                className={`h-8 rounded-md border px-3 text-xs font-semibold ${iconPickerTab === 'custom' ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-700 border-slate-300'}`}
                                onClick={() => setIconPickerTab('custom')}
                                disabled={isHierarchyLocked}
                                data-testid="categories-icon-tab-custom"
                              >
                                Custom SVG
                              </button>
                            </div>

                            {iconPickerTab === 'library' ? (
                              <div className="space-y-3" data-testid="categories-icon-library-panel">
                                <input
                                  type="text"
                                  className="h-9 w-full rounded-md border border-slate-300 px-3 text-xs"
                                  placeholder="İkon ara (ev, araba, iş, teknoloji...)"
                                  value={iconLibraryQuery}
                                  onChange={(event) => setIconLibraryQuery(event.target.value)}
                                  disabled={isHierarchyLocked}
                                  data-testid="categories-icon-library-search"
                                />
                                <div className="flex flex-wrap gap-2" data-testid="categories-icon-library-tag-list">
                                  {iconLibraryTags.map((tag) => (
                                    <button
                                      key={tag}
                                      type="button"
                                      className={`h-7 rounded-full border px-3 text-[11px] font-semibold ${iconLibraryTag === tag ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-700 border-slate-300'}`}
                                      onClick={() => setIconLibraryTag(tag)}
                                      disabled={isHierarchyLocked}
                                      data-testid={`categories-icon-library-tag-${tag}`}
                                    >
                                      {tag === 'all' ? 'Tümü' : tag}
                                    </button>
                                  ))}
                                </div>
                                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3" data-testid="categories-icon-library-grid">
                                  {filteredApprovedIcons.length === 0 ? (
                                    <div className="rounded-md border border-dashed bg-white px-3 py-3 text-xs text-slate-500" data-testid="categories-icon-library-empty">
                                      Filtreye uygun ikon bulunamadı.
                                    </div>
                                  ) : (
                                    filteredApprovedIcons.map((iconItem) => {
                                      const selected = String(form.icon_svg || '').trim() === String(iconItem.svg || '').trim();
                                      return (
                                        <button
                                          key={iconItem.key}
                                          type="button"
                                          className={`flex items-center gap-2 rounded-md border px-2 py-2 text-left ${selected ? 'border-sky-500 bg-sky-50' : 'border-slate-200 bg-white'}`}
                                          onClick={() => {
                                            if (isHierarchyLocked) return;
                                            setForm((prev) => ({ ...prev, icon_svg: iconItem.svg }));
                                            setCategoryIconSvgError('');
                                            setHierarchyFieldErrors((prev) => {
                                              const next = { ...prev };
                                              delete next.main_icon_svg;
                                              return next;
                                            });
                                          }}
                                          disabled={isHierarchyLocked}
                                          data-testid={`categories-icon-library-item-${iconItem.key}`}
                                        >
                                          <CategoryIconSvg
                                            iconSvg={iconItem.svg}
                                            wrapperClassName="h-8 w-8 rounded-md border bg-white p-1"
                                            fallbackClassName="h-8 w-8 rounded-md border bg-slate-100 text-slate-500"
                                            fallbackText="SVG"
                                            testId={`categories-icon-library-item-preview-${iconItem.key}`}
                                          />
                                          <span className="min-w-0">
                                            <span className="block truncate text-xs font-semibold text-slate-900" data-testid={`categories-icon-library-item-label-${iconItem.key}`}>{iconItem.label}</span>
                                            <span className="block truncate text-[11px] text-slate-500" data-testid={`categories-icon-library-item-tags-${iconItem.key}`}>{(iconItem.tags || []).join(', ')}</span>
                                          </span>
                                        </button>
                                      );
                                    })
                                  )}
                                </div>
                              </div>
                            ) : (
                              <div className="space-y-3" data-testid="categories-icon-custom-panel">
                                <textarea
                                  className="min-h-[120px] w-full rounded-md border p-2 text-xs text-slate-900"
                                  value={form.icon_svg || ''}
                                  disabled={isHierarchyLocked}
                                  placeholder="<svg viewBox='0 0 24 24' xmlns='http://www.w3.org/2000/svg'>...</svg>"
                                  onChange={(event) => {
                                    const nextValue = event.target.value;
                                    setForm((prev) => ({ ...prev, icon_svg: nextValue }));
                                    setCategoryIconSvgError('');
                                    setHierarchyFieldErrors((prev) => {
                                      const next = { ...prev };
                                      delete next.main_icon_svg;
                                      return next;
                                    });
                                  }}
                                  data-testid="categories-icon-svg-input"
                                />
                              </div>
                            )}

                            <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-600" data-testid="categories-icon-svg-meta">
                              <span data-testid="categories-icon-svg-hint">Sanitize aktif: script/event handler/javascript/foreignObject engellenir.</span>
                              <span data-testid="categories-icon-svg-length">{categoryIconSvgLength}/{CATEGORY_ICON_SVG_MAX_LENGTH}</span>
                            </div>

                            <div className="flex flex-wrap items-center gap-2" data-testid="categories-icon-svg-actions">
                              <button
                                type="button"
                                className="h-8 rounded-md border border-slate-300 px-3 text-xs font-semibold text-slate-700 disabled:opacity-60"
                                disabled={isHierarchyLocked || !form.icon_svg}
                                onClick={() => {
                                  setForm((prev) => ({ ...prev, icon_svg: "" }));
                                  setCategoryIconSvgError("");
                                  setHierarchyFieldErrors((prev) => {
                                    const next = { ...prev };
                                    delete next.main_icon_svg;
                                    return next;
                                  });
                                }}
                                data-testid="categories-icon-svg-clear"
                              >
                                İkonu Temizle
                              </button>
                              <button
                                type="button"
                                className="h-8 rounded-md border border-slate-300 px-3 text-xs font-semibold text-slate-700 disabled:opacity-60"
                                disabled={isHierarchyLocked}
                                onClick={() => setIconPickerTab('custom')}
                                data-testid="categories-icon-svg-open-custom"
                              >
                                Custom'a Geç
                              </button>
                            </div>

                            <div className="flex items-center gap-3" data-testid="categories-icon-svg-preview-wrap">
                              <CategoryIconSvg
                                iconSvg={form.icon_svg}
                                wrapperClassName="h-10 w-10 rounded-md border bg-white p-1"
                                fallbackClassName="h-10 w-10 rounded-md border bg-slate-100 text-slate-500"
                                fallbackText="SVG"
                                testId="categories-icon-svg-preview"
                              />
                              <span className="text-xs text-slate-600" data-testid="categories-icon-svg-preview-hint">Önizleme (kayıt sonrası public kategori kartlarında görünür)</span>
                            </div>
                            {categoryIconSvgError ? (
                              <div className="text-xs text-rose-600" data-testid="categories-icon-svg-error">{categoryIconSvgError}</div>
                            ) : null}
                            {hierarchyFieldErrors.main_icon_svg ? (
                              <div className="text-xs text-rose-600" data-testid="categories-icon-svg-required-error">{hierarchyFieldErrors.main_icon_svg}</div>
                            ) : null}
                          </div>
                        ) : (
                          <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-700" data-testid="categories-icon-svg-root-only-note">
                            Alt kategorilerde ikon alanı kapalıdır.
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

                  <div className="rounded-lg border p-4 space-y-4" data-testid="categories-subcategory-section">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <h3 className="text-md font-semibold">Kademeli Hiyerarşi</h3>
                        <p className="text-xs text-slate-600" data-testid="categories-subcategory-hint">
                          Seviye listesini doldurun → Onayla → seçili kategori için bir sonraki seviye açılır. Leaf seçilirse dal kapanır.
                        </p>
                      </div>
                    </div>

                    {form.module === 'vehicle' && (
                      <div className="rounded-md border border-amber-200 bg-amber-50 p-3 space-y-3" data-testid="categories-vehicle-master-panel">
                        <div className="text-xs text-amber-700" data-testid="categories-vehicle-master-hint">
                          Vasıta modülünde önerilen seviye akışı: Level 1 (Araç Tipi) → Level 2 (Model Yılı) → Level 3 (Marka) → Level 4 (Model) → Level 5 (Yakıt) → Level 6 (Kasa) → Level 7 (Vites) → Level 8 (Alt Model/Detay).
                        </div>
                        <div className="flex flex-wrap items-center gap-2" data-testid="categories-vehicle-master-actions">
                          <button
                            type="button"
                            className="text-xs border rounded px-3 py-1"
                            onClick={handleApplyVehicleTemplate}
                            data-testid="categories-vehicle-template-apply"
                          >
                            Vasıta Şablonunu Uygula
                          </button>
                          <button
                            type="button"
                            className={`text-xs border rounded px-3 py-1 ${vehicleImportMode === 'api' ? 'bg-white text-slate-900' : 'text-slate-700'}`}
                            onClick={() => setVehicleImportMode(vehicleImportMode === 'api' ? '' : 'api')}
                            data-testid="categories-vehicle-import-api"
                          >
                            API'den Yükle
                          </button>
                          <button
                            type="button"
                            className={`text-xs border rounded px-3 py-1 ${vehicleImportMode === 'json' ? 'bg-white text-slate-900' : 'text-slate-700'}`}
                            onClick={() => setVehicleImportMode(vehicleImportMode === 'json' ? '' : 'json')}
                            data-testid="categories-vehicle-import-json"
                          >
                            JSON Yükle
                          </button>
                          <button
                            type="button"
                            className={`text-xs border rounded px-3 py-1 ${vehicleImportMode === 'excel' ? 'bg-white text-slate-900' : 'text-slate-700'}`}
                            onClick={() => setVehicleImportMode(vehicleImportMode === 'excel' ? '' : 'excel')}
                            data-testid="categories-vehicle-import-excel"
                          >
                            Excel Yükle
                          </button>
                        </div>

                        {vehicleImportMode === 'api' && (
                          <div className="space-y-2" data-testid="categories-vehicle-import-api-panel">
                            <textarea
                              className="w-full min-h-[120px] rounded border p-2 text-xs"
                              value={vehicleImportPayload}
                              onChange={(e) => setVehicleImportPayload(e.target.value)}
                              data-testid="categories-vehicle-import-api-payload"
                            />
                            <label className="flex items-center gap-2 text-xs" data-testid="categories-vehicle-import-api-dryrun">
                              <input
                                type="checkbox"
                                checked={vehicleImportDryRun}
                                onChange={(e) => setVehicleImportDryRun(e.target.checked)}
                                data-testid="categories-vehicle-import-api-dryrun-input"
                              />
                              Dry-run (önizleme)
                            </label>
                            <button
                              type="button"
                              className="text-xs text-white bg-[var(--brand-navy-deep)] rounded px-3 py-1 disabled:opacity-60"
                              onClick={handleVehicleImportApi}
                              disabled={vehicleImportLoading}
                              data-testid="categories-vehicle-import-api-submit"
                            >
                              {vehicleImportLoading ? 'Başlatılıyor...' : 'API Import Başlat'}
                            </button>
                          </div>
                        )}

                        {(vehicleImportMode === 'json' || vehicleImportMode === 'excel') && (
                          <div className="space-y-2" data-testid="categories-vehicle-import-upload-panel">
                            <input
                              type="file"
                              accept={vehicleImportMode === 'excel' ? '.xls,.xlsx' : 'application/json'}
                              onChange={(e) => setVehicleImportFile(e.target.files?.[0] || null)}
                              data-testid="categories-vehicle-import-upload-input"
                            />
                            <label className="flex items-center gap-2 text-xs" data-testid="categories-vehicle-import-upload-dryrun">
                              <input
                                type="checkbox"
                                checked={vehicleImportDryRun}
                                onChange={(e) => setVehicleImportDryRun(e.target.checked)}
                                data-testid="categories-vehicle-import-upload-dryrun-input"
                              />
                              Dry-run (önizleme)
                            </label>
                            <button
                              type="button"
                              className="text-xs text-white bg-[var(--brand-navy-deep)] rounded px-3 py-1 disabled:opacity-60"
                              onClick={() => handleVehicleImportUpload(vehicleImportMode)}
                              disabled={vehicleImportLoading}
                              data-testid="categories-vehicle-import-upload-submit"
                            >
                              {vehicleImportLoading ? 'Başlatılıyor...' : 'Dosya Import Başlat'}
                            </button>
                          </div>
                        )}

                        {vehicleImportStatus && (
                          <div className="text-xs text-emerald-700" data-testid="categories-vehicle-import-status">
                            {vehicleImportStatus}
                          </div>
                        )}
                        {vehicleImportError && (
                          <div className="text-xs text-rose-600" data-testid="categories-vehicle-import-error">
                            {vehicleImportError}
                          </div>
                        )}
                      </div>
                    )}

                    <div className="rounded-md border border-slate-200 bg-slate-50 p-3 space-y-2" data-testid="categories-level-navigator">
                      <div className="text-xs font-semibold text-slate-700" data-testid="categories-level-navigator-title">
                        Level Navigator
                      </div>
                      <div className="flex flex-wrap items-center gap-2" data-testid="categories-level-navigator-path">
                        <button
                          type="button"
                          className="text-xs border rounded px-2 py-1"
                          onClick={() => {
                            setLevelSelections([]);
                            resetLevelCompletionFrom(0);
                          }}
                          data-testid="categories-level-nav-root"
                        >
                          Level 0 (Modül)
                        </button>
                        {levelBreadcrumbs.map((crumb) => (
                          <button
                            key={`crumb-${crumb.levelIndex}`}
                            type="button"
                            className="text-xs border rounded px-2 py-1"
                            onClick={() => handleLevelJump(crumb.levelIndex)}
                            data-testid={`categories-level-nav-${crumb.levelIndex}`}
                          >
                            {`Level ${crumb.levelIndex + 1}: ${crumb.label}`}
                          </button>
                        ))}
                      </div>
                      <div className="flex flex-wrap items-center gap-2" data-testid="categories-level-navigator-actions">
                        <button
                          type="button"
                          className="text-xs border rounded px-3 py-1"
                          onClick={handleLevelBack}
                          data-testid="categories-level-nav-back"
                        >
                          Bir üst seviyeye dön
                        </button>
                        <button
                          type="button"
                          className="text-xs border rounded px-3 py-1"
                          onClick={handleCreateNextLevel}
                          data-testid="categories-level-nav-next"
                        >
                          Yeni seviye oluştur
                        </button>
                      </div>
                    </div>

                    {renderLevelColumns()}

                    <div className="rounded-md border border-dashed border-slate-300 bg-white p-3" data-testid="categories-hierarchy-live-preview">
                      <div className="mb-2 text-xs font-semibold text-slate-700">Canlı Hiyerarşi Önizleme</div>
                      {hierarchyLiveRows.length === 0 ? (
                        <div className="text-xs text-slate-500" data-testid="categories-hierarchy-live-preview-empty">
                          Önizleme için kategori ekleyin.
                        </div>
                      ) : (
                        <div className="space-y-1" data-testid="categories-hierarchy-live-preview-tree">
                          {hierarchyLiveRows.map((row) => (
                            <div
                              key={row.key}
                              className="flex items-center gap-2 text-xs"
                              style={{ paddingLeft: `${Math.min(row.level - 1, 8) * 14}px` }}
                              data-testid={`categories-hierarchy-live-preview-row-${row.key}`}
                            >
                              <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] font-semibold text-slate-700" data-testid={`categories-hierarchy-live-preview-level-${row.key}`}>
                                L{row.level}
                              </span>
                              <span className={`${row.missing ? "text-rose-600" : "text-slate-800"}`} data-testid={`categories-hierarchy-live-preview-name-${row.key}`}>
                                {row.label}
                              </span>
                              {row.is_leaf ? (
                                <span className="text-[10px] text-amber-600" data-testid={`categories-hierarchy-live-preview-leaf-${row.key}`}>
                                  Leaf
                                </span>
                              ) : null}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {editing && isHierarchyLocked && (
                    <div className="rounded-lg border border-dashed border-amber-300 bg-amber-50 p-4 text-sm text-amber-800" data-testid="categories-hierarchy-locked">
                      Bu kategori için hiyerarşi alanı şu an kilitli. "Düzenle" ile açıp eksik/hatalı alanları güncelleyebilirsiniz.
                    </div>
                  )}

                  {editing && !isHierarchyLocked && (
                    <div className="rounded-lg border border-dashed border-emerald-300 bg-emerald-50 p-4 text-sm text-emerald-800" data-testid="categories-hierarchy-editable">
                      Düzenleme modu açık. Eksik/hatalı alanları düzenleyip "Tamam" ile kaydedebilirsiniz.
                    </div>
                  )}

                  <div className="text-xs text-slate-700" data-testid="categories-hierarchy-warning">
                    {editing
                      ? (isHierarchyLocked
                        ? "Hiyerarşi kilitliyken çekirdek alan adımlarına geçebilirsiniz; hiyerarşi değişikliği için önce Düzenle ile kilidi açın."
                        : "Hiyerarşi düzenleme açık. Kaydetmeden önce gerekli adımları tamamlayın.")
                      : "Kategori tamamlanmadan çekirdek alanlara geçilemez."}
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
                    <div className="mt-1 text-xs text-slate-700" data-testid="categories-summary-icon-svg-status">
                      SVG İkon: {String(form.icon_svg || '').trim() ? 'Tanımlı' : 'Tanımlı değil'}
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
