import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useCountry } from '../contexts/CountryContext';
import { Switch } from '@/components/ui/switch';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Globe, Pencil } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Countries() {
  const [countries, setCountries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingCountry, setEditingCountry] = useState(null);
  const [saving, setSaving] = useState(false);
  const { t, getTranslated } = useLanguage();
  const { getFlag } = useCountry();

  useEffect(() => {
    fetchCountries();
  }, []);

  const fetchCountries = async () => {
    try {
      const response = await axios.get(`${API}/countries`);
      setCountries(response.data);
    } catch (error) {
      console.error('Failed to fetch countries:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleEnabled = async (countryId, currentState) => {
    try {
      await axios.patch(`${API}/countries/${countryId}`, { is_enabled: !currentState });
      fetchCountries();
    } catch (error) {
      console.error('Failed to update country:', error);
    }
  };

  const openEdit = (country) => {
    setEditingCountry({
      ...country,
      default_currency: country.default_currency || 'EUR',
      default_language: (country.default_language || 'tr').toLowerCase(),
      support_email: country.support_email || '',
    });
  };

  const handleSave = async () => {
    if (!editingCountry) return;
    setSaving(true);
    try {
      await axios.patch(`${API}/countries/${editingCountry.id}`, {
        is_enabled: !!editingCountry.is_enabled,
        default_currency: editingCountry.default_currency,
        default_language: editingCountry.default_language,
        support_email: editingCountry.support_email || null,
      });
      setEditingCountry(null);
      fetchCountries();
    } catch (error) {
      console.error('Failed to save country:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6" data-testid="countries-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t('countries')}</h1>
          <p className="text-muted-foreground text-sm mt-1">
            {countries.filter(c => c.is_enabled).length} of {countries.length} countries enabled
          </p>
        </div>
      </div>

      {/* Countries Table */}
      {loading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : (
        <div className="border rounded-lg overflow-hidden bg-card">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50">
                <tr>
                  <th className="text-left p-3 font-medium">Ülke</th>
                  <th className="text-left p-3 font-medium">Kod</th>
                  <th className="text-left p-3 font-medium">Para Birimi</th>
                  <th className="text-left p-3 font-medium">Dil</th>
                  <th className="text-center p-3 font-medium">Enabled</th>
                  <th className="text-right p-3 font-medium">İşlemler</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {countries.map((country) => (
                  <tr key={country.id} className={!country.is_enabled ? 'opacity-60' : ''}>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xl">{getFlag(country.code)}</span>
                        <span className="font-medium">{getTranslated(country.name)}</span>
                      </div>
                    </td>
                    <td className="p-3">
                      <code className="text-xs px-1.5 py-0.5 rounded bg-muted font-mono">{country.code}</code>
                    </td>
                    <td className="p-3">{country.default_currency || '-'}</td>
                    <td className="p-3 uppercase">{country.default_language || '-'}</td>
                    <td className="p-3 text-center">
                      <div className="inline-flex items-center gap-2">
                        <Switch
                          checked={!!country.is_enabled}
                          onCheckedChange={() => handleToggleEnabled(country.id, country.is_enabled)}
                          data-testid={`country-enabled-${country.code}`}
                        />
                      </div>
                    </td>
                    <td className="p-3 text-right">
                      <button
                        onClick={() => openEdit(country)}
                        className="inline-flex items-center gap-2 h-8 px-3 rounded-md border text-sm font-medium hover:bg-muted"
                        data-testid={`country-edit-${country.code}`}
                      >
                        <Pencil size={14} />
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <Dialog open={!!editingCountry} onOpenChange={(open) => !open && setEditingCountry(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ülke Düzenle</DialogTitle>
            <DialogDescription>
              Sadece kritik alanlar burada görünür. Diğer alanlar sonraki iterasyonda drawer’a taşınacaktır.
            </DialogDescription>
          </DialogHeader>

          {editingCountry && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Kod</div>
                  <div className="font-mono text-sm px-3 py-2 rounded border bg-muted/30">{editingCountry.code}</div>
                </div>
                <div>
                  <div className="text-xs text-muted-foreground mb-1">Enabled</div>
                  <div className="flex items-center h-10 px-3 rounded border">
                    <Switch
                      checked={!!editingCountry.is_enabled}
                      onCheckedChange={(v) => setEditingCountry((c) => ({ ...c, is_enabled: v }))}
                      data-testid="country-edit-enabled"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <label className="space-y-1">
                  <div className="text-xs text-muted-foreground">Default Currency</div>
                  <input
                    value={editingCountry.default_currency}
                    onChange={(e) => setEditingCountry((c) => ({ ...c, default_currency: e.target.value.toUpperCase() }))}
                    className="w-full h-10 px-3 rounded-md border bg-background text-sm"
                    placeholder="EUR"
                    data-testid="country-edit-currency"
                  />
                </label>
                <label className="space-y-1">
                  <div className="text-xs text-muted-foreground">Default Language</div>
                  <select
                    value={editingCountry.default_language}
                    onChange={(e) => setEditingCountry((c) => ({ ...c, default_language: e.target.value }))}
                    className="w-full h-10 px-3 rounded-md border bg-background text-sm"
                    data-testid="country-edit-language"
                  >
                    <option value="tr">TR</option>
                    <option value="de">DE</option>
                    <option value="fr">FR</option>
                  </select>
                </label>
              </div>

              <label className="space-y-1">
                <div className="text-xs text-muted-foreground">Support Email</div>
                <input
                  value={editingCountry.support_email || ''}
                  onChange={(e) => setEditingCountry((c) => ({ ...c, support_email: e.target.value }))}
                  className="w-full h-10 px-3 rounded-md border bg-background text-sm"
                  placeholder="support@example.com"
                  data-testid="country-edit-support-email"
                />
              </label>
            </div>
          )}

          <DialogFooter>
            <button
              onClick={() => setEditingCountry(null)}
              className="inline-flex items-center h-9 px-4 rounded-md border text-sm font-medium hover:bg-muted"
              data-testid="country-edit-cancel"
            >
              İptal
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="inline-flex items-center h-9 px-4 rounded-md bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50"
              data-testid="country-edit-save"
            >
              {saving ? 'Kaydediliyor...' : 'Kaydet'}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
