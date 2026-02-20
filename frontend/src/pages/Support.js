import { useMemo, useState } from 'react';
import axios from 'axios';
import { toast } from '@/components/ui/use-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const REQUEST_TYPE_OPTIONS = [
  { value: 'complaint', label: 'Şikayet' },
  { value: 'request', label: 'Talep' },
];

export default function SupportPage() {
  const [requestType, setRequestType] = useState('complaint');
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [attachmentName, setAttachmentName] = useState('');
  const [attachmentUrl, setAttachmentUrl] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const authHeader = useMemo(() => ({
    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  }), []);

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!requestType) {
      toast({ title: 'Başvuru türü zorunludur.', variant: 'destructive' });
      return;
    }
    if (!subject.trim() || !description.trim()) {
      toast({ title: 'Konu ve açıklama zorunludur.', variant: 'destructive' });
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        request_type: requestType,
        subject: subject.trim(),
        description: description.trim(),
        attachment_name: attachmentName.trim() || null,
        attachment_url: attachmentUrl.trim() || null,
      };

      const res = await axios.post(`${API}/applications`, payload, { headers: authHeader });
      toast({ title: 'Başvurunuz alındı.', description: `Referans: ${res.data.application_id}` });
      setRequestType('complaint');
      setSubject('');
      setDescription('');
      setAttachmentName('');
      setAttachmentUrl('');
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
          Talep veya şikayetinizi iletin, ekibimiz sizinle iletişime geçsin.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4" data-testid="support-form">
        <div>
          <label className="text-sm text-muted-foreground">Başvuru Türü</label>
          <select
            value={requestType}
            onChange={(event) => setRequestType(event.target.value)}
            className="h-10 w-full rounded-md border bg-background px-3 text-sm"
            data-testid="support-request-type"
          >
            {REQUEST_TYPE_OPTIONS.map((option) => (
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

        <div className="grid gap-4 md:grid-cols-2" data-testid="support-attachment-fields">
          <div>
            <label className="text-sm text-muted-foreground">Dosya Adı (opsiyonel)</label>
            <input
              value={attachmentName}
              onChange={(event) => setAttachmentName(event.target.value)}
              className="h-10 w-full rounded-md border bg-background px-3 text-sm"
              placeholder="Dosya adı"
              data-testid="support-attachment-name"
            />
          </div>
          <div>
            <label className="text-sm text-muted-foreground">Dosya URL (opsiyonel)</label>
            <input
              value={attachmentUrl}
              onChange={(event) => setAttachmentUrl(event.target.value)}
              className="h-10 w-full rounded-md border bg-background px-3 text-sm"
              placeholder="https://..."
              data-testid="support-attachment-url"
            />
          </div>
        </div>

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
