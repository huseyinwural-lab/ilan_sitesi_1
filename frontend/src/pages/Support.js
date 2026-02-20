import { useMemo, useState } from 'react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { toast } from '@/components/ui/use-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CATEGORY_OPTIONS = [
  { value: 'complaint', label: 'Şikayet' },
  { value: 'request', label: 'Talep' },
];

const createAttachment = () => ({ name: '', url: '' });

export default function SupportPage() {
  const { user } = useAuth();
  const [category, setCategory] = useState('');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [listingId, setListingId] = useState('');
  const [companyName, setCompanyName] = useState('');
  const [taxNumber, setTaxNumber] = useState('');
  const [attachments, setAttachments] = useState([createAttachment()]);
  const [kvkkConsent, setKvkkConsent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const isDealer = user?.role === 'dealer';

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const handleAttachmentChange = (index, field, value) => {
    setAttachments((prev) =>
      prev.map((item, idx) => (idx === index ? { ...item, [field]: value } : item))
    );
  };

  const handleAddAttachment = () => {
    setAttachments((prev) => [...prev, createAttachment()]);
  };

  const handleRemoveAttachment = (index) => {
    setAttachments((prev) => prev.filter((_, idx) => idx !== index));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!category) {
      toast({ title: 'Başvuru türü zorunludur.', variant: 'destructive' });
      return;
    }
    if (!subject.trim() || !description.trim()) {
      toast({ title: 'Konu ve açıklama zorunludur.', variant: 'destructive' });
      return;
    }
    if (isDealer && !companyName.trim()) {
      toast({ title: 'Firma adı zorunludur.', variant: 'destructive' });
      return;
    }
    if (!kvkkConsent) {
      toast({ title: 'KVKK onayını işaretleyin.', variant: 'destructive' });
      return;
    }

    setSubmitting(true);
    try {
      const filteredAttachments = attachments
        .filter((att) => att.name.trim() && att.url.trim())
        .map((att) => ({ name: att.name.trim(), url: att.url.trim() }));

      const payload = {
        category,
        subject: subject.trim(),
        description: description.trim(),
        attachments: filteredAttachments,
        listing_id: listingId.trim() || null,
        kvkk_consent: kvkkConsent,
        company_name: isDealer ? companyName.trim() : null,
        tax_number: isDealer ? taxNumber.trim() || null : null,
      };

      const res = await axios.post(`${API}/applications`, payload, { headers: authHeader });
      toast({ title: 'Başvurunuz alındı.', description: `Referans: ${res.data.application_id}` });
      setCategory('');
      setSubject('');
      setDescription('');
      setListingId('');
      setCompanyName('');
      setTaxNumber('');
      setAttachments([createAttachment()]);
      setKvkkConsent(false);
    } catch (err) {
      const message = err.response?.data?.detail || 'Başvuru gönderilemedi.';
      toast({ title: typeof message === 'string' ? message : 'Başvuru gönderilemedi.', variant: 'destructive' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6" data-testid="support-page">
      <div>
        <h1 className="text-2xl font-bold" data-testid="support-title">Destek Başvurusu</h1>
        <p className="text-sm text-muted-foreground" data-testid="support-subtitle">
          Başvurunuzu iletin, ekibimiz sizinle iletişime geçsin.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4" data-testid="support-form">
        <div>
          <label className="text-sm text-muted-foreground">Başvuru Türü</label>
          <select
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            className="h-10 w-full rounded-md border bg-background px-3 text-sm"
            data-testid="support-category"
          >
            <option value="">Seçiniz</option>
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm text-muted-foreground">Konu</label>
          <input
            value={subject}
            onChange={(event) => setSubject(event.target.value)}
            className="h-10 w-full rounded-md border bg-background px-3 text-sm"
            placeholder="Konu"
            data-testid="support-subject"
          />
        </div>

        <div>
          <label className="text-sm text-muted-foreground">Açıklama</label>
          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            className="min-h-[140px] w-full rounded-md border bg-background px-3 py-2 text-sm"
            placeholder="Detaylı açıklama"
            data-testid="support-description"
          />
        </div>

        <div>
          <label className="text-sm text-muted-foreground">İlgili İlan ID (opsiyonel)</label>
          <input
            value={listingId}
            onChange={(event) => setListingId(event.target.value)}
            className="h-10 w-full rounded-md border bg-background px-3 text-sm"
            placeholder="İlan ID"
            data-testid="support-listing-id"
          />
        </div>

        {isDealer && (
          <div className="grid gap-4 md:grid-cols-2" data-testid="support-dealer-fields">
            <div>
              <label className="text-sm text-muted-foreground">Firma Adı</label>
              <input
                value={companyName}
                onChange={(event) => setCompanyName(event.target.value)}
                className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                data-testid="support-company-name"
              />
            </div>
            <div>
              <label className="text-sm text-muted-foreground">Vergi No (opsiyonel)</label>
              <input
                value={taxNumber}
                onChange={(event) => setTaxNumber(event.target.value)}
                className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                data-testid="support-tax-number"
              />
            </div>
          </div>
        )}

        <div className="space-y-3" data-testid="support-attachments">
          <div className="text-sm text-muted-foreground">Dosya bağlantıları (opsiyonel)</div>
          {attachments.map((attachment, index) => (
            <div key={`attachment-${index}`} className="grid gap-3 md:grid-cols-2">
              <input
                value={attachment.name}
                onChange={(event) => handleAttachmentChange(index, 'name', event.target.value)}
                className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                placeholder="Dosya adı"
                data-testid={`support-attachment-name-${index}`}
              />
              <div className="flex items-center gap-2">
                <input
                  value={attachment.url}
                  onChange={(event) => handleAttachmentChange(index, 'url', event.target.value)}
                  className="h-10 w-full rounded-md border bg-background px-3 text-sm"
                  placeholder="Dosya URL"
                  data-testid={`support-attachment-url-${index}`}
                />
                {attachments.length > 1 && (
                  <button
                    type="button"
                    onClick={() => handleRemoveAttachment(index)}
                    className="h-10 px-3 rounded-md border text-sm"
                    data-testid={`support-attachment-remove-${index}`}
                  >
                    Kaldır
                  </button>
                )}
              </div>
            </div>
          ))}
          <button
            type="button"
            onClick={handleAddAttachment}
            className="h-9 px-3 rounded-md border text-sm"
            data-testid="support-attachment-add"
          >
            Dosya Ekle
          </button>
        </div>

        <label className="flex items-center gap-2 text-sm" data-testid="support-kvkk">
          <input
            type="checkbox"
            checked={kvkkConsent}
            onChange={(event) => setKvkkConsent(event.target.checked)}
            data-testid="support-kvkk-checkbox"
          />
          KVKK onaylıyorum.
        </label>

        <button
          type="submit"
          className="h-11 px-4 rounded-md bg-primary text-primary-foreground text-sm"
          disabled={submitting}
          data-testid="support-submit"
        >
          {submitting ? 'Gönderiliyor' : 'Başvuruyu Gönder'}
        </button>
      </form>
    </div>
  );
}
