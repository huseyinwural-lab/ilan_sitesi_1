import React, { useState } from 'react';
import { useWizard } from './WizardContext';

const MediaUploader = () => {
  const { saveStep, loading } = useWizard();
  const [files, setFiles] = useState([]);
  const [errors, setErrors] = useState([]);

  const handleFileSelect = (e) => {
    const selected = Array.from(e.target.files);
    const newFiles = selected.map(file => ({
      file,
      preview: URL.createObjectURL(file),
      id: Math.random().toString(36).substr(2, 9)
    }));
    setFiles([...files, ...newFiles]);
  };

  const validatePhotos = async () => {
    const errs = [];
    if (files.length < 3) {
      errs.push('En az 3 fotoğraf yüklemelisiniz.');
    }

    const MIN_W = 800;
    const MIN_H = 600;

    const checks = await Promise.all(
      files.map(
        (file) =>
          new Promise((resolve) => {
            const img = new Image();
            img.onload = () => resolve({ ok: img.width >= MIN_W && img.height >= MIN_H, w: img.width, h: img.height, name: file.file.name });
            img.onerror = () => resolve({ ok: false, w: 0, h: 0, name: file.file.name });
            img.src = file.preview;
          })
      )
    );

    const bad = checks.filter((c) => !c.ok);
    if (bad.length > 0) {
      errs.push(`Minimum çözünürlük ${MIN_W}x${MIN_H}. Uymayan: ${bad.map(b => `${b.name} (${b.w}x${b.h})`).join(', ')}`);
    }

    setErrors(errs);
    return errs.length === 0;
  };

  const handleNext = async () => {
    const ok = await validatePhotos();
    if (!ok) return;

    // Upload to backend and register media
    const draftId = window.__WIZARD_DRAFT_ID__;
    const token = localStorage.getItem('access_token');
    if (!draftId) {
      setErrors(['Draft bulunamadı. Lütfen baştan deneyin.']);
      return;
    }

    const form = new FormData();
    files.forEach((f) => form.append('files', f.file));

    const res = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/v1/listings/vehicle/${draftId}/media`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: form,
    });

    if (!res.ok) {
      const t = await res.text();
      setErrors([t || 'Foto upload başarısız']);
      return;
    }

    const data = await res.json();
    const previewUrls = (data.media || []).map((m) => m.preview_url);
    saveStep(previewUrls);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold" data-testid="wizard-media-title">Fotoğraflar</h2>
      <p className="text-sm text-muted-foreground" data-testid="wizard-media-subtitle">Yükleme canlıdır, en az 3 fotoğraf ekleyin.</p>
            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center bg-gray-50 hover:bg-blue-50 transition">
        <input 
          type="file" 
          multiple 
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden" 
          id="file-upload"
          data-testid="wizard-photo-input"
        />
        <label htmlFor="file-upload" className="cursor-pointer block" data-testid="wizard-photo-label">
          <div className="text-4xl mb-2">📸</div>
          <span className="text-blue-600 font-medium">Fotoğraf yüklemek için tıkla</span>
          <p className="text-sm text-gray-500 mt-1">(min 3 foto, min 800x600)</p>
        </label>
      </div>

      {/* Error Display */}
      {errors.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4" data-testid="wizard-photo-errors">
          <div className="text-red-800 font-medium mb-2">Hatalar:</div>
          <ul className="text-red-700 text-sm space-y-1">
            {errors.map((error, index) => (
              <li key={index}>• {error}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Preview Grid */}
      {files.length > 0 && (
        <div className="grid grid-cols-3 gap-4" data-testid="wizard-photo-grid">
          {files.map((f, index) => (
            <div key={f.id} className="relative group aspect-square bg-gray-100 rounded-lg overflow-hidden border" data-testid={`wizard-photo-card-${index}`}>
              <img src={f.preview} alt="preview" className="w-full h-full object-cover" data-testid={`wizard-photo-preview-${index}`} />
              <button 
                onClick={() => setFiles(files.filter(x => x.id !== f.id))}
                className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-0 group-hover:opacity-100 transition"
                data-testid={`wizard-photo-remove-${index}`}
              >
                ×
              </button>
              {index === 0 && (
                <span className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs text-center py-1">
                  Cover Photo
                </span>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="flex justify-end">
        <button 
          onClick={handleNext}
          disabled={loading || files.length === 0}
          className="bg-blue-600 text-white px-8 py-3 rounded-lg hover:bg-blue-700 font-medium disabled:opacity-50"
          data-testid="wizard-photos-next"
        >
          Next: Review
        </button>
      </div>
    </div>
  );
};

export default MediaUploader;
