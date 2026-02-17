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

      {/* Countries Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {countries.map((country) => (
            <div 
              key={country.id} 
              className={`bg-card rounded-md border p-6 transition-all ${
                !country.is_enabled ? 'opacity-60' : ''
              }`}
              data-testid={`country-card-${country.code}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <span className="text-4xl">{getFlag(country.code)}</span>
                  <div>
                    <h3 className="font-semibold text-lg">{getTranslated(country.name)}</h3>
                    <code className="text-xs px-1.5 py-0.5 rounded bg-muted font-mono">{country.code}</code>
                  </div>
                </div>
                <button
                  onClick={() => handleToggleEnabled(country.id, country.is_enabled)}
                  className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                    country.is_enabled 
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400' 
                      : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                  }`}
                  data-testid={`country-toggle-${country.code}`}
                >
                  {country.is_enabled ? 'Enabled' : 'Disabled'}
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-muted-foreground">Currency</p>
                  <p className="font-medium">{country.default_currency}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Language</p>
                  <p className="font-medium uppercase">{country.default_language}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Date Format</p>
                  <p className="font-medium">{country.date_format}</p>
                </div>
                <div>
                  <p className="text-muted-foreground">Number Format</p>
                  <p className="font-medium">{country.number_format}</p>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t">
                <div className="grid grid-cols-3 gap-2 text-xs text-center">
                  <div className="p-2 rounded bg-muted/50">
                    <p className="text-muted-foreground">Area</p>
                    <p className="font-medium">{country.area_unit}</p>
                  </div>
                  <div className="p-2 rounded bg-muted/50">
                    <p className="text-muted-foreground">Distance</p>
                    <p className="font-medium">{country.distance_unit}</p>
                  </div>
                  <div className="p-2 rounded bg-muted/50">
                    <p className="text-muted-foreground">Weight</p>
                    <p className="font-medium">{country.weight_unit}</p>
                  </div>
                </div>
              </div>

              {country.support_email && (
                <div className="mt-4 text-sm">
                  <p className="text-muted-foreground">Support</p>
                  <p className="font-medium">{country.support_email}</p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
