
import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { useCountry } from '../contexts/CountryContext';
import { 
  Package, Plus, Edit2, Check, X, Filter, 
  TrendingUp, Settings, DollarSign, Calendar
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function PremiumProducts() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCountry, setSelectedCountry] = useState('DE'); // Default
  const [showModal, setShowModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const { t } = useLanguage();
  const { countries } = useCountry(); // Assuming context provides list

  // Ranking Rules State
  const [rankingRules, setRankingRules] = useState(null);
  const [showRankingModal, setShowRankingModal] = useState(false);

  useEffect(() => {
    fetchProducts();
    fetchRankingRules();
  }, [selectedCountry]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/premium-products?country=${selectedCountry}`);
      setProducts(response.data);
    } catch (error) {
      console.error('Failed to fetch products:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRankingRules = async () => {
    try {
      // Assuming endpoint allows fetching by country or list all
      const response = await axios.get(`${API}/premium-ranking-rules`);
      const rule = response.data.find(r => r.country === selectedCountry);
      setRankingRules(rule || { country: selectedCountry, premium_first: true, weight_priority: 50 });
    } catch (error) {
      console.error('Failed to fetch ranking rules:', error);
    }
  };

  const handleSaveProduct = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      key: formData.get('key'),
      name: { tr: formData.get('name_tr'), de: formData.get('name_de'), fr: formData.get('name_fr') }, // Simplified
      country: selectedCountry,
      currency: formData.get('currency'),
      price_net: parseFloat(formData.get('price_net')),
      duration_days: parseInt(formData.get('duration_days')),
      tax_category: formData.get('tax_category'),
      is_active: formData.get('is_active') === 'on'
    };

    try {
      if (editingProduct) {
        await axios.patch(`${API}/premium-products/${editingProduct.id}`, data);
      } else {
        await axios.post(`${API}/premium-products`, data);
      }
      setShowModal(false);
      setEditingProduct(null);
      fetchProducts();
    } catch (error) {
      alert(error.response?.data?.detail || 'Error saving product');
    }
  };

  const handleSaveRanking = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = {
      premium_first: formData.get('premium_first') === 'on',
      weight_priority: parseInt(formData.get('weight_priority')),
      weight_recency: parseInt(formData.get('weight_recency'))
    };

    try {
      await axios.patch(`${API}/premium-ranking-rules/${selectedCountry}`, data);
      setShowRankingModal(false);
      fetchRankingRules();
    } catch (error) {
      alert('Error updating ranking rules');
    }
  };

  return (
    <div className="space-y-6" data-testid="premium-products-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Premium Products</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage monetization products and ranking logic
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowRankingModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-md border hover:bg-muted"
          >
            <Settings size={16} />
            Ranking Rules
          </button>
          <button
            onClick={() => { setEditingProduct(null); setShowModal(true); }}
            className="flex items-center gap-2 px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90"
          >
            <Plus size={16} />
            New Product
          </button>
        </div>
      </div>

      {/* Country Filter */}
      <div className="flex items-center gap-2 bg-card p-2 rounded-md border w-fit">
        <Filter size={16} className="text-muted-foreground ml-2" />
        <select 
          value={selectedCountry}
          onChange={(e) => setSelectedCountry(e.target.value)}
          className="bg-transparent border-none text-sm font-medium focus:ring-0 cursor-pointer"
        >
          {['DE', 'CH', 'FR', 'AT'].map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* Product List */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <div className="col-span-full text-center py-12">Loading...</div>
        ) : products.map((product) => (
          <div key={product.id} className="bg-card rounded-md border p-4 hover:shadow-md transition-all relative group">
            <div className="flex justify-between items-start mb-2">
              <span className="px-2 py-1 bg-primary/10 text-primary text-xs font-semibold rounded uppercase">
                {product.key}
              </span>
              <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button 
                  onClick={() => { setEditingProduct(product); setShowModal(true); }}
                  className="p-1 hover:bg-muted rounded"
                >
                  <Edit2 size={14} />
                </button>
              </div>
            </div>
            
            <h3 className="font-semibold text-lg mb-1">{product.name.en || product.name.de || Object.values(product.name)[0]}</h3>
            <div className="text-muted-foreground text-sm mb-4 line-clamp-2">
              {product.description?.en || "No description"}
            </div>

            <div className="flex items-center gap-4 text-sm font-medium">
              <div className="flex items-center gap-1">
                <DollarSign size={14} className="text-muted-foreground" />
                {product.price_net} {product.currency}
              </div>
              <div className="flex items-center gap-1">
                <Calendar size={14} className="text-muted-foreground" />
                {product.duration_days} Days
              </div>
            </div>

            {!product.is_active && (
              <div className="absolute inset-0 bg-background/50 flex items-center justify-center backdrop-blur-sm rounded-md">
                <span className="bg-muted px-3 py-1 rounded text-sm font-medium">Inactive</span>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Product Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-lg p-6">
            <h2 className="text-lg font-bold mb-4">
              {editingProduct ? 'Edit Product' : 'New Premium Product'}
            </h2>
            <form onSubmit={handleSaveProduct} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Key (Code)</label>
                  <input name="key" defaultValue={editingProduct?.key} className="w-full rounded-md border px-3 py-2 bg-background" required />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Currency</label>
                  <select name="currency" defaultValue={editingProduct?.currency || (selectedCountry === 'CH' ? 'CHF' : 'EUR')} className="w-full rounded-md border px-3 py-2 bg-background">
                    <option value="EUR">EUR</option>
                    <option value="CHF">CHF</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-2">
                <input name="name_de" placeholder="Name (DE)" defaultValue={editingProduct?.name?.de} className="rounded-md border px-3 py-2 bg-background" required />
                <input name="name_tr" placeholder="Name (TR)" defaultValue={editingProduct?.name?.tr} className="rounded-md border px-3 py-2 bg-background" required />
                <input name="name_fr" placeholder="Name (FR)" defaultValue={editingProduct?.name?.fr} className="rounded-md border px-3 py-2 bg-background" required />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Price (Net)</label>
                  <input type="number" step="0.01" name="price_net" defaultValue={editingProduct?.price_net} className="w-full rounded-md border px-3 py-2 bg-background" required />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Duration (Days)</label>
                  <input type="number" name="duration_days" defaultValue={editingProduct?.duration_days} className="w-full rounded-md border px-3 py-2 bg-background" required />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Tax Category</label>
                <select name="tax_category" defaultValue={editingProduct?.tax_category || 'digital_service'} className="w-full rounded-md border px-3 py-2 bg-background">
                  <option value="digital_service">Digital Service</option>
                  <option value="advertising">Advertising</option>
                </select>
              </div>

              <div className="flex items-center gap-2">
                <input type="checkbox" name="is_active" defaultChecked={editingProduct?.is_active ?? true} id="is_active" />
                <label htmlFor="is_active" className="text-sm font-medium">Active</label>
              </div>

              <div className="flex gap-2 justify-end pt-4">
                <button type="button" onClick={() => setShowModal(false)} className="px-4 py-2 rounded-md hover:bg-muted">Cancel</button>
                <button type="submit" className="px-4 py-2 rounded-md bg-primary text-primary-foreground">Save</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Ranking Rules Modal */}
      {showRankingModal && rankingRules && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-card rounded-lg border shadow-xl w-full max-w-md p-6">
            <h2 className="text-lg font-bold mb-4">Ranking Rules ({selectedCountry})</h2>
            <form onSubmit={handleSaveRanking} className="space-y-6">
              <div className="flex items-center justify-between p-3 bg-muted/50 rounded-md">
                <div>
                  <label className="font-medium block">Premium First</label>
                  <p className="text-xs text-muted-foreground">Always show premium listings on top</p>
                </div>
                <input type="checkbox" name="premium_first" defaultChecked={rankingRules.premium_first} className="h-5 w-5" />
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1 flex justify-between">
                    <span>Priority Score Weight</span>
                    <span className="text-muted-foreground">{rankingRules.weight_priority}%</span>
                  </label>
                  <input type="range" name="weight_priority" min="0" max="100" defaultValue={rankingRules.weight_priority} className="w-full" />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1 flex justify-between">
                    <span>Recency Weight</span>
                    <span className="text-muted-foreground">{rankingRules.weight_recency}%</span>
                  </label>
                  <input type="range" name="weight_recency" min="0" max="100" defaultValue={rankingRules.weight_recency} className="w-full" />
                </div>
              </div>

              <div className="flex gap-2 justify-end pt-4">
                <button type="button" onClick={() => setShowRankingModal(false)} className="px-4 py-2 rounded-md hover:bg-muted">Cancel</button>
                <button type="submit" className="px-4 py-2 rounded-md bg-primary text-primary-foreground">Update Rules</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
