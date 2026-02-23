import React, { useEffect, useMemo, useRef, useState } from 'react';
import { toast } from '@/components/ui/use-toast';
import { useWizard } from './WizardContext';

const MIN_PHOTOS = 3;

const stripExif = (file) => new Promise((resolve) => {
  if (!file.type.startsWith('image/')) {
    resolve(file);
    return;
  }
  const img = new Image();
  const reader = new FileReader();
  reader.onload = () => {
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(img, 0, 0);
      canvas.toBlob((blob) => {
        if (!blob) {
          resolve(file);
          return;
        }
        resolve(new File([blob], file.name, { type: 'image/jpeg' }));
      }, 'image/jpeg', 0.92);
    };
    img.src = reader.result;
  };
  reader.readAsDataURL(file);
});

const FeaturesMediaStep = () => {
  const {
    dynamicValues,
    setDynamicValues,
    detailGroups,
    setDetailGroups,
    schema,
    basicInfo,
    media,
    setMedia,
    draftId,
    saveDraft,
    trackWizardEvent,
    setAutosaveStatus,
    setStep,
    completedSteps,
    setCompletedSteps,
    loading,
  } = useWizard();

  const [files, setFiles] = useState([]);
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const saveLockRef = useRef(false);
  const [dragIndex, setDragIndex] = useState(null);

  useEffect(() => {
    if (media.length === 0) return;
    setFiles((prev) => {
      if (prev.length > 0) return prev;
      return media.map((item) => ({
        id: item.media_id,
        media_id: item.media_id,
        preview: item.url,
        file: null,
        is_cover: item.is_cover || false,
      }));
    });
  }, [media]);

  const dynamicFields = schema?.dynamic_fields || [];
  const detailFieldGroups = schema?.detail_groups || [];

  const handleDynamicChange = (key, value) => {
    setDynamicValues((prev) => ({ ...prev, [key]: value }));
  };

  const handleDetailToggle = (groupId, optionId) => {
    setDetailGroups((prev) => {
      const current = prev[groupId] || [];
      const exists = current.includes(optionId);
      const next = exists ? current.filter((id) => id !== optionId) : [...current, optionId];
      return { ...prev, [groupId]: next };
    });
  };

  const onFilesSelected = (fileList) => {
    const nextFiles = Array.from(fileList).map((file, idx) => ({
      id: `${file.name}-${Date.now()}-${idx}`,
      file,
      preview: URL.createObjectURL(file),
      media_id: null,
      is_cover: files.length === 0 && idx === 0,
    }));
    setFiles((prev) => [...prev, ...nextFiles]);
  };

  const handleDragStart = (index) => {
    setDragIndex(index);
  };

  const handleDrop = (index) => {
    if (dragIndex === null) return;
    const next = [...files];
    const [moved] = next.splice(dragIndex, 1);
    next.splice(index, 0, moved);
    setFiles(next);
    setDragIndex(null);
  };

  const handleCover = (index) => {
    setFiles((prev) => prev.map((item, idx) => ({
      ...item,
      is_cover: idx === index,
    })));
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, idx) => idx !== index));
  };

  const validate = () => {
    const nextErrors = {};
    dynamicFields.forEach((field) => {
      if (field.required && !dynamicValues[field.key]) {
        nextErrors[field.key] = 'Zorunlu alan.';
      }
    });
    detailFieldGroups.forEach((group) => {
      if (group.required) {
        const selected = detailGroups[group.id] || [];
        if (!selected.length) {
          nextErrors[`detail_${group.id}`] = 'En az 1 seçim yapın.';
        }
      }
    });
    if (files.length < MIN_PHOTOS) {
      nextErrors.media = `En az ${MIN_PHOTOS} fotoğraf ekleyin.`;
    }
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const scrollToFirstError = () => {
    setTimeout(() => {
      const container = document.querySelector('[data-testid="wizard-features-step"]');
      const target = container?.querySelector('[data-testid$="-error"]');
      if (target) {
        target.scrollIntoView({ behavior: window.innerWidth < 768 ? 'smooth' : 'auto', block: 'center' });
      }
    }, 0);
  };

  const uploadFiles = async () => {
    const newFiles = files.filter((item) => item.file && !item.media_id);
    if (newFiles.length === 0) return { media: media };

    const cleaned = await Promise.all(newFiles.map((item) => stripExif(item.file)));
    const formData = new FormData();
    cleaned.forEach((file) => formData.append('files', file));

    const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/listings/vehicle/${draftId}/media`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      body: formData,
    });
    if (!res.ok) {
      throw new Error('Media upload failed');
    }
    return await res.json();
  };

  const reorderMedia = async (order, coverMediaId) => {
    const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/listings/vehicle/${draftId}/media/order`, {
      method: 'PATCH',
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ order, cover_media_id: coverMediaId }),
    });
    if (!res.ok) {
      throw new Error('Media order update failed');
    }
    return await res.json();
  };

  const handleComplete = async () => {
    if (saving || saveLockRef.current) return { ok: false };
    saveLockRef.current = true;
    if (!validate()) {
      scrollToFirstError();
      saveLockRef.current = false;
      return { ok: false };
    }
    setSaving(true);

    try {
      const saved = await saveDraft({
        dynamic_fields: dynamicValues,
        detail_groups: detailGroups,
      });
      if (!saved) {
        setErrors((prev) => ({ ...prev, submit: 'Özellikler kaydedilemedi.' }));
        scrollToFirstError();
        return false;
      }

      const existingIds = new Set(files.filter((item) => item.media_id).map((item) => item.media_id));
      const uploadResponse = await uploadFiles();
      const serverMedia = uploadResponse.media || media;
      const newMediaItems = serverMedia.filter((item) => !existingIds.has(item.media_id));

      let newIndex = 0;
      const assignedFiles = files.map((item) => {
        if (item.media_id) return item;
        const assigned = newMediaItems[newIndex];
        newIndex += 1;
        if (!assigned) return item;
        return {
          ...item,
          media_id: assigned.media_id,
          preview: assigned.url || item.preview,
        };
      });

      const order = assignedFiles.map((item) => item.media_id).filter(Boolean);
      const coverFile = assignedFiles.find((item) => item.is_cover) || assignedFiles[0];
      const coverId = coverFile?.media_id || order[0];

      const reordered = await reorderMedia(order, coverId);
      const updatedMedia = (reordered.media || []).map((item) => ({
        media_id: item.media_id,
        url: item.url || item.preview_url || `/media/listings/${draftId}/${item.file}`,
        is_cover: item.is_cover,
        file: item.file,
      }));
      setMedia(updatedMedia);
      setFiles(updatedMedia.map((item) => ({
        id: item.media_id,
        media_id: item.media_id,
        preview: item.url,
        file: null,
        is_cover: item.is_cover,
      })));

      setCompletedSteps((prev) => ({ ...prev, 6: true }));
      return true;
    } catch (err) {
      console.error(err);
      setErrors((prev) => ({ ...prev, submit: 'Medya kaydedilemedi.' }));
      scrollToFirstError();
      return false;
    } finally {
      setSaving(false);
      saveLockRef.current = false;
    }
  };

  const handleNext = async () => {
    if (!validate()) {
      scrollToFirstError();
      await trackWizardEvent('wizard_step_autosave_error', {
        step_id: 'features',
        category_id: basicInfo.category_id,
        module: basicInfo.module || 'vehicle',
        country: basicInfo.country || (localStorage.getItem('selected_country') || 'DE'),
        reason: 'validation_failed',
      });
      setAutosaveStatus((prev) => ({
        ...prev,
        status: 'error',
        lastErrorAt: new Date().toISOString(),
      }));
      return;
    }
    if (!completedSteps[6]) {
      const ok = await handleComplete();
      if (!ok) {
        await trackWizardEvent('wizard_step_autosave_error', {
          step_id: 'features',
          category_id: basicInfo.category_id,
          module: basicInfo.module || 'vehicle',
          country: basicInfo.country || (localStorage.getItem('selected_country') || 'DE'),
          reason: 'save_failed',
        });
        setAutosaveStatus((prev) => ({
          ...prev,
          status: 'error',
          lastErrorAt: new Date().toISOString(),
        }));
        return;
      }
    }
    await trackWizardEvent('wizard_step_autosave_success', {
      step_id: 'features',
      category_id: basicInfo.category_id,
      module: basicInfo.module || 'vehicle',
      country: basicInfo.country || (localStorage.getItem('selected_country') || 'DE'),
    });
    setAutosaveStatus((prev) => ({
      ...prev,
      status: 'success',
      lastSuccessAt: new Date().toISOString(),
    }));
    toast({
      title: 'Kaydedildi',
      duration: 2500,
      dismissible: false,
      'data-testid': 'wizard-autosave-toast',
    });
    setStep(7);
  };

  const nextDisabled = saving;

  return (
    <div className="space-y-8" data-testid="wizard-features-step">
      <div className="bg-white p-6 rounded-xl shadow-sm border space-y-6" data-testid="features-section">
        <h3 className="text-lg font-semibold">Özellikler</h3>

        {dynamicFields.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4" data-testid="dynamic-fields">
            {dynamicFields.map((field) => (
              <div key={field.id || field.key}>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {field.label || field.key} {field.required ? '*' : ''}
                </label>
                {field.type === 'select' && (
                  <select
                    className="w-full p-2 border rounded-md"
                    value={dynamicValues[field.key] || ''}
                    onChange={(e) => handleDynamicChange(field.key, e.target.value)}
                    data-testid={`dynamic-select-${field.key}`}
                  >
                    <option value="">Seç...</option>
                    {(field.options || []).map((opt) => (
                      <option key={opt.id || opt} value={opt.id || opt}>
                        {opt.label || opt}
                      </option>
                    ))}
                  </select>
                )}
                {(!field.type || field.type === 'text') && (
                  <input
                    type="text"
                    className="w-full p-2 border rounded-md"
                    value={dynamicValues[field.key] || ''}
                    onChange={(e) => handleDynamicChange(field.key, e.target.value)}
                    data-testid={`dynamic-text-${field.key}`}
                  />
                )}
                {field.type === 'number' && (
                  <input
                    type="number"
                    className="w-full p-2 border rounded-md"
                    value={dynamicValues[field.key] || ''}
                    onChange={(e) => handleDynamicChange(field.key, e.target.value)}
                    data-testid={`dynamic-number-${field.key}`}
                  />
                )}
                {errors[field.key] && (
                  <div className="text-xs text-red-600 mt-1" data-testid={`dynamic-error-${field.key}`}>
                    {errors[field.key]}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {detailFieldGroups.map((group) => (
          <div key={group.id} className="space-y-2" data-testid={`detail-group-${group.id}`}>
            <div className="font-medium text-sm">{group.title}{group.required ? ' *' : ''}</div>
            <div className="flex flex-wrap gap-2">
              {(group.options || []).map((option) => {
                const optionId = option.id || option;
                const optionLabel = option.label || option;
                const selected = (detailGroups[group.id] || []).includes(optionId);
                return (
                  <button
                    key={optionId}
                    type="button"
                    onClick={() => handleDetailToggle(group.id, optionId)}
                    className={`px-3 py-1 rounded-full border text-sm ${selected ? 'bg-blue-50 border-blue-500 text-blue-700' : 'border-gray-200 text-gray-600'}`}
                    data-testid={`detail-option-${group.id}-${optionId}`}
                  >
                    {optionLabel}
                  </button>
                );
              })}
            </div>
            {errors[`detail_${group.id}`] && <div className="text-xs text-red-600" data-testid={`detail-error-${group.id}`}>{errors[`detail_${group.id}`]}</div>}
          </div>
        ))}
      </div>

      <div className="bg-white p-6 rounded-xl shadow-sm border space-y-4" data-testid="media-section">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Medya</h3>
          <span className="text-xs text-gray-500" data-testid="media-min-note">Min {MIN_PHOTOS} fotoğraf</span>
        </div>
        <div className="border border-dashed rounded-lg p-6 text-center" data-testid="media-dropzone">
          <input
            type="file"
            accept="image/*"
            multiple
            onChange={(e) => onFilesSelected(e.target.files)}
            data-testid="media-file-input"
          />
          <p className="text-xs text-gray-500 mt-2" data-testid="media-exif-note">EXIF otomatik temizlenir.</p>
        </div>

        {errors.media && <div className="text-xs text-red-600" data-testid="media-error">{errors.media}</div>}

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4" data-testid="media-grid">
          {files.map((item, idx) => (
            <div
              key={item.id}
              draggable
              onDragStart={() => handleDragStart(idx)}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => handleDrop(idx)}
              className={`border rounded-lg overflow-hidden relative ${item.is_cover ? 'border-blue-500' : 'border-gray-200'}`}
              data-testid={`media-card-${idx}`}
            >
              <img src={item.preview} alt="media" className="w-full h-28 object-cover" data-testid={`media-image-${idx}`} />
              {item.is_cover && (
                <span className="absolute top-2 left-2 text-xs bg-blue-600 text-white px-2 py-1 rounded" data-testid={`media-cover-badge-${idx}`}>Kapak</span>
              )}
              <div className="flex items-center justify-between p-2">
                <button
                  type="button"
                  className="text-xs text-blue-600"
                  onClick={() => handleCover(idx)}
                  data-testid={`media-cover-button-${idx}`}
                >
                  Kapak Yap
                </button>
                <button
                  type="button"
                  className="text-xs text-red-500"
                  onClick={() => removeFile(idx)}
                  data-testid={`media-remove-button-${idx}`}
                >
                  Sil
                </button>
              </div>
            </div>
          ))}
        </div>

        {errors.submit && <div className="text-xs text-red-600" data-testid="media-submit-error">{errors.submit}</div>}
      </div>

      <div className="flex items-center justify-between" data-testid="features-actions">
        <button
          type="button"
          onClick={() => setStep(5)}
          className="px-4 py-2 text-sm text-gray-500"
          data-testid="features-back"
        >
          Geri
        </button>
        <div className="flex items-center gap-3">
          <div title={nextDisabled ? 'Önce bu adımı tamamlayın.' : ''} data-testid="features-next-tooltip">
            <button
              type="button"
              onClick={handleNext}
              disabled={nextDisabled}
              className="px-4 py-2 border rounded-md text-sm disabled:opacity-50"
              data-testid="features-next"
            >
              Next
            </button>
          </div>
          <button
            type="button"
            onClick={handleComplete}
            disabled={loading || saving}
            className="px-5 py-2 bg-blue-600 text-white rounded-md disabled:opacity-60"
            data-testid="features-complete"
          >
            Tamam
          </button>
        </div>
      </div>
    </div>
  );
};

export default FeaturesMediaStep;
