import { useState, useEffect } from 'react';
import axios from 'axios';
import { useLanguage } from '../contexts/LanguageContext';
import { 
  Menu, Plus, GripVertical, Eye, EyeOff, 
  ChevronDown, ChevronRight, Link, ExternalLink
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function MenuManager() {
  const [menuItems, setMenuItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedItem, setExpandedItem] = useState(null);
  const { t, getTranslated, language } = useLanguage();

  useEffect(() => {
    fetchMenuItems();
  }, []);

  const fetchMenuItems = async () => {
    try {
      const response = await axios.get(`${API}/menu/top-items`);
      setMenuItems(response.data);
    } catch (error) {
      console.error('Failed to fetch menu items:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleEnabled = async (itemId, currentState) => {
    try {
      await axios.patch(`${API}/menu/top-items/${itemId}`, { is_enabled: !currentState });
      fetchMenuItems();
    } catch (error) {
      console.error('Failed to toggle menu item:', error);
    }
  };

  return (
    <div className="space-y-6" data-testid="menu-manager-page">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Menu Manager</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Manage top navigation and mega menu
          </p>
        </div>
      </div>

      {/* Menu Items */}
      <div className="space-y-3">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
          </div>
        ) : menuItems.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground bg-card rounded-md border">
            <Menu size={48} className="mx-auto mb-4 opacity-50" />
            <p>No menu items configured</p>
          </div>
        ) : (
          menuItems.map((item, index) => (
            <div 
              key={item.id} 
              className={`bg-card rounded-md border overflow-hidden ${!item.is_enabled ? 'opacity-60' : ''}`}
              data-testid={`menu-item-${item.key}`}
            >
              <div 
                className="p-4 flex items-center gap-3 cursor-pointer hover:bg-muted/30"
                onClick={() => setExpandedItem(expandedItem === item.id ? null : item.id)}
              >
                <GripVertical size={16} className="text-muted-foreground cursor-grab" />
                
                <span className="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center text-primary font-bold">
                  {index + 1}
                </span>
                
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{getTranslated(item.name)}</span>
                    <code className="text-xs px-1.5 py-0.5 rounded bg-muted font-mono">{item.key}</code>
                    {item.required_module && (
                      <span className="text-xs px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">
                        {item.required_module}
                      </span>
                    )}
                  </div>
                  {item.icon && (
                    <p className="text-xs text-muted-foreground mt-0.5">Icon: {item.icon}</p>
                  )}
                </div>
                
                <div className="flex items-center gap-2">
                  {item.allowed_countries?.map(c => (
                    <span key={c} className="text-xs px-1.5 py-0.5 rounded bg-muted">{c}</span>
                  ))}
                </div>
                
                <button
                  onClick={(e) => { e.stopPropagation(); handleToggleEnabled(item.id, item.is_enabled); }}
                  className={`p-2 rounded hover:bg-muted ${item.is_enabled ? 'text-emerald-600' : 'text-muted-foreground'}`}
                >
                  {item.is_enabled ? <Eye size={18} /> : <EyeOff size={18} />}
                </button>
                
                {expandedItem === item.id ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
              </div>
              
              {expandedItem === item.id && (
                <div className="px-4 pb-4 pt-2 border-t bg-muted/20">
                  {item.sections && item.sections.length > 0 ? (
                    <div className="space-y-4">
                      <h4 className="font-medium text-sm">Mega Menu Sections ({item.sections.length})</h4>
                      {item.sections.map(section => (
                        <div key={section.id} className="p-3 rounded-md bg-card border">
                          <p className="font-medium text-sm mb-2">{getTranslated(section.title)}</p>
                          {section.links && section.links.length > 0 ? (
                            <div className="space-y-1">
                              {section.links.map(link => (
                                <div key={link.id} className="flex items-center gap-2 text-sm text-muted-foreground">
                                  {link.link_type === 'external' ? <ExternalLink size={12} /> : <Link size={12} />}
                                  <span>{getTranslated(link.label)}</span>
                                  <span className="text-xs px-1 rounded bg-muted">{link.link_type}</span>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <p className="text-sm text-muted-foreground">No links configured</p>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">No mega menu sections configured</p>
                  )}
                  
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-xs text-muted-foreground">
                      Badge: {item.badge ? JSON.stringify(item.badge) : 'None'} | 
                      Sort Order: {item.sort_order}
                    </p>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Info */}
      <div className="p-4 rounded-md bg-muted/50 text-sm text-muted-foreground">
        <p><strong>Tip:</strong> Menu items are linked to Feature Flags. If a required module is disabled, the menu item won't appear on the frontend.</p>
      </div>
    </div>
  );
}
