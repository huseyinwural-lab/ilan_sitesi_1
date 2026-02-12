
import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useCountry } from '../contexts/CountryContext';
import { 
  Percent, Plus, Edit2, Calendar, AlertTriangle, 
  CheckCircle, XCircle
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function TaxRates() {
  const [rates, setRates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCountry, setSelectedCountry] = useState('DE');
  const [showModal, setShowModal] = useState(false);
  const [editingRate, setEditingRate] = useState(null);
  const { t } = useLanguage();

  useEffect(() => {
    fetchRates();
  }, [selectedCountry]);

  const fetchRates = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/vat-rates?country=${selectedCountry}`);
      setRates(response.data);
    } catch (error) {
      console.error('Failed to fetch VAT rates:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveRate = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      country: selectedCountry,
      rate: parseFloat(formData.get('rate')),
      valid_from: new Date(formData.get('valid_from')).toISOString(),
      valid_to: formData.get('valid_to') ? new Date(formData.get('valid_to')).toISOString() : null,
      tax_type: formData.get('tax_type'),
      description: formData.get('description'),
    };

    try {
      if (editingRate) {
        await axios.patch(`${API}/vat-rates/${editingRate.id}`, data);
      } else {
        await axios.post(`${API}/vat-rates`, data);
      }
      setShowModal(false);
      setEditingRate(null);
      fetchRates();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error saving VAT rate');
    }
  };

  return (
    <div className="space-y-6" data-testid="tax-rates-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">VAT & Tax Rates</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage historical and current VAT rates per country
          </p>
        </div>
        <button
          onClick={() => { setEditingRate(null); setShowModal(true); }}
          className="flex items-center gap-2 px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
        >
          <Plus size={16} />
          New Rate
        </button>
      </div>

      {/* Country Filter */}
      <div className="flex gap-2 mb-6">
        {['DE', 'CH', 'FR', 'AT'].map(country => (
          <button
            key={country}
            onClick={() => setSelectedCountry(country)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              selectedCountry === country 
                ? 'bg-primary text-primary-foreground' 
                : 'bg-muted hover:bg-muted/80'
            }`}
          >
            {country}
          </button>
        ))}
      </div>

      {/* Rates List */}
      <div className="bg-card rounded-md border">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-muted/50 text-left">
              <th className="p-4 font-medium">Rate</th>
              <th className="p-4 font-medium">Type</th>
              <th className="p-4 font-medium">Valid From</th>
              <th className="p-4 font-medium">Valid To</th>
              <th className="p-4 font-medium">Status</th>
              <th className="p-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} className="p-8 text-center">Loading...</td></tr>
            ) : rates.length === 0 ? (
              <tr><td colSpan={6} className="p-8 text-center text-muted-foreground">No rates defined for {selectedCountry}</td></tr>
            ) : (
              rates.map((rate) => (
                <tr key={rate.id} className="border-b last:border-0 hover:bg-muted/50">
                  <td className="p-4 font-bold text-lg">{rate.rate}%</td>
                  <td className="p-4 capitalize">{rate.tax_type}</td>
                  <td className="p-4">{new Date(rate.valid_from).toLocaleDateString()}</td>
                  <td className="p-4 text-muted-foreground">
                    {rate.valid_to ? new Date(rate.valid_to).toLocaleDateString() : 'Indefinite'}
                  </td>
                  <td className="p-4">
                    {rate.is_active ? (
                      <span className="inline-flex items-center gap-1 text-emerald-600 px-2 py-1 rounded-full bg-emerald-50 text-xs font-medium">
                        <CheckCircle size={12} /> Active
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-muted-foreground px-2 py-1 rounded-full bg-muted text-xs font-medium">
                        <XCircle size={12} /> Inactive
                      </span>
                    )}
                  </td>
                  <td className="p-4 text-right">
                    <button 
                      onClick={() => { setEditingRate(rate); setShowModal(true); }}
                      className="p-2 hover:bg-muted rounded-md"
                    >
                      <Edit2 size={16} />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-md p-6">
            <h2 className="text-lg font-bold mb-4">
              {editingRate ? 'Edit VAT Rate' : 'New VAT Rate'} ({selectedCountry})
            </h2>
            <form onSubmit={handleSaveRate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Rate (%)</label>
                <div className="relative">
                  <input type="number" step="0.1" name="rate" defaultValue={editingRate?.rate} className="w-full rounded-md border px-3 py-2 bg-background pl-8" required />
                  <Percent size={14} className="absolute left-2.5 top-3 text-muted-foreground" />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Valid From</label>
                  <input type="date" name="valid_from" defaultValue={editingRate?.valid_from?.split('T')[0]} className="w-full rounded-md border px-3 py-2 bg-background" required />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Valid To (Optional)</label>
                  <input type="date" name="valid_to" defaultValue={editingRate?.valid_to?.split('T')[0]} className="w-full rounded-md border px-3 py-2 bg-background" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Tax Type</label>
                <select name="tax_type" defaultValue={editingRate?.tax_type || 'standard'} className="w-full rounded-md border px-3 py-2 bg-background">
                  <option value="standard">Standard</option>
                  <option value="reduced">Reduced</option>
                  <option value="zero">Zero</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <input name="description" defaultValue={editingRate?.description} className="w-full rounded-md border px-3 py-2 bg-background" />
              </div>

              <div className="bg-amber-50 text-amber-800 p-3 rounded-md text-xs flex gap-2">
                <AlertTriangle size={16} className="shrink-0" />
                <p>Ensure date ranges do not overlap with existing active rates for {selectedCountry}.</p>
              </div>

              <div className="flex gap-2 justify-end pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 rounded-md hover:bg-muted">Cancel</button>
                <button type="submit" className="px-4 py-2 rounded-md bg-primary text-primary-foreground">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
