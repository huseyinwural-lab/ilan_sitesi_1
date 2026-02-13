import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { ChevronDown, ChevronUp, Search, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { tr, de, fr } from 'date-fns/locale';

// ==================== SUB-COMPONENTS ====================

const LightweightCheckbox = ({ id, checked, onChange, disabled, label, count }) => {
  return (
    <div className={cn(
      "flex items-center justify-between py-1.5 px-2 -mx-2 rounded-md transition-colors group",
      !disabled && "hover:bg-muted/50 cursor-pointer",
      disabled && "opacity-50 cursor-not-allowed"
    )}>
      <div className="flex items-center gap-2 flex-1 min-w-0" onClick={() => !disabled && onChange(!checked)}>
        <div className={cn(
          "h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 flex items-center justify-center transition-colors",
          checked ? "bg-primary text-primary-foreground" : "bg-background",
          disabled && "border-muted-foreground/30"
        )}>
          {checked && <Search className="h-3 w-3 stroke-[3]" style={{ maskImage: 'none', WebkitMaskImage: 'none' }} />} 
          {/* Using a simple Check icon replica or lucide Check if imported */}
          {checked && (
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              strokeWidth="3" 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              className="h-3 w-3"
            >
              <polyline points="20 6 9 17 4 12" />
            </svg>
          )}
        </div>
        <label 
          htmlFor={id} 
          className="text-sm font-normal leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70 truncate select-none cursor-pointer"
        >
          {label}
        </label>
      </div>
      <span className="text-xs text-muted-foreground tabular-nums ml-2">
        ({count})
      </span>
    </div>
  );
};

const CheckboxFacet = ({ facet, onChange }) => {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [searchTerm, setSearchTerm] = React.useState('');
  
  const MAX_VISIBLE = 5;
  const showSearch = facet.options.length > 10;
  
  const filteredOptions = facet.options.filter(opt => 
    opt.label.toLowerCase().includes(searchTerm.toLowerCase())
  );
  
  const visibleOptions = isExpanded ? filteredOptions : filteredOptions.slice(0, MAX_VISIBLE);

  const handleCheck = (value, checked) => {
    const current = new Set(facet.selectedValues || []);
    if (checked) {
      current.add(value);
    } else {
      current.delete(value);
    }
    onChange(Array.from(current));
  };

  return (
    <div className="space-y-1">
      {showSearch && (
        <div className="relative mb-2">
          <Search className="absolute left-2 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
          <Input 
            placeholder="Ara..." 
            className="pl-8 h-8 text-xs bg-muted/20 border-none focus-visible:ring-1" 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      )}
      
      <div className="flex flex-col">
        {visibleOptions.map((opt) => (
          <LightweightCheckbox 
            key={opt.value}
            id={`${facet.key}-${opt.value}`}
            checked={facet.selectedValues?.includes(opt.value) || false}
            onChange={(checked) => handleCheck(opt.value, checked)}
            disabled={opt.count === 0 && !facet.selectedValues?.includes(opt.value)}
            label={opt.label}
            count={opt.count}
          />
        ))}
      </div>

      {filteredOptions.length > MAX_VISIBLE && (
        <Button 
          variant="link" 
          className="p-0 h-8 text-xs text-primary font-medium hover:no-underline pl-1"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? 'Daha az göster' : `+ ${filteredOptions.length - MAX_VISIBLE} daha fazla`}
        </Button>
      )}
    </div>
  );
};

const ToggleFacet = ({ facet, onChange }) => {
  // true, false, null (all)
  // We can model this as a switch or radio. 
  // Per spec: Toggle Switch with 3 states logic is tricky with standard switch. 
  // Let's implement as a specialized 3-state toggle or simple switch if it only filters for "True".
  // Spec says: "Three states: true, false, null (any) - Click toggles through states"
  
  const currentState = facet.value; // true, false, null
  
  const handleToggle = () => {
    if (currentState === null) onChange(true);
    else if (currentState === true) onChange(false);
    else onChange(null);
  };
  
  return (
    <div className="flex items-center justify-between py-1">
      <div className="flex items-center space-x-2">
        <div 
          className={cn(
            "w-10 h-5 rounded-full relative cursor-pointer transition-colors",
            currentState === true ? "bg-green-500" : currentState === false ? "bg-red-500" : "bg-gray-300"
          )}
          onClick={handleToggle}
        >
          <div className={cn(
            "absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform shadow-sm",
            currentState === true ? "left-5" : currentState === false ? "left-0.5" : "left-[11px]"
          )} />
        </div>
        <span className="text-sm font-medium">
          {currentState === true ? 'Evet' : currentState === false ? 'Hayır' : 'Farketmez'}
        </span>
      </div>
      <Badge variant="secondary" className="text-xs">
        {currentState === true ? facet.trueCount : currentState === false ? facet.falseCount : (facet.trueCount + facet.falseCount)}
      </Badge>
    </div>
  );
};

const RangeFacet = ({ facet, onChange }) => {
  const [localMin, setLocalMin] = React.useState(facet.selectedMin || facet.min);
  const [localMax, setLocalMax] = React.useState(facet.selectedMax || facet.max);
  
  // Update local state when props change (reset)
  React.useEffect(() => {
    setLocalMin(facet.selectedMin ?? facet.min);
    setLocalMax(facet.selectedMax ?? facet.max);
  }, [facet.selectedMin, facet.selectedMax, facet.min, facet.max]);

  const handleSliderChange = (values) => {
    setLocalMin(values[0]);
    setLocalMax(values[1]);
  };

  const handleCommit = () => {
    onChange(localMin, localMax);
  };

  return (
    <div className="space-y-4 pt-2">
      <div className="flex items-center justify-between gap-2">
        <Input 
          type="number" 
          value={localMin}
          onChange={(e) => setLocalMin(Number(e.target.value))}
          onBlur={handleCommit}
          className="h-8 text-xs w-20"
        />
        <span className="text-muted-foreground">-</span>
        <Input 
          type="number" 
          value={localMax}
          onChange={(e) => setLocalMax(Number(e.target.value))}
          onBlur={handleCommit}
          className="h-8 text-xs w-20"
        />
        {facet.unit && <span className="text-xs text-muted-foreground">{facet.unit}</span>}
      </div>
      <Slider 
        defaultValue={[localMin, localMax]} 
        value={[localMin, localMax]}
        min={facet.min} 
        max={facet.max} 
        step={facet.step || 1} 
        onValueChange={handleSliderChange}
        onValueCommit={handleCommit}
        className="my-4"
      />
    </div>
  );
};

// ==================== MAIN COMPONENT ====================

const FacetGroup = ({ title, type, isOpen, onToggle, children, activeCount }) => {
  return (
    <div className="border-b last:border-0">
      <Button 
        variant="ghost" 
        className="w-full flex justify-between items-center py-4 px-0 hover:bg-transparent hover:no-underline"
        onClick={onToggle}
      >
        <span className="font-semibold text-sm flex items-center gap-2">
          {title}
          {activeCount > 0 && (
            <Badge variant="secondary" className="h-5 px-1.5 text-[10px] bg-primary/10 text-primary">
              {activeCount}
            </Badge>
          )}
        </span>
        {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </Button>
      
      {isOpen && (
        <div className="pb-4 animate-in slide-in-from-top-1 duration-200">
          {children}
        </div>
      )}
    </div>
  );
};

export const FacetRenderer = ({ 
  facets, 
  facetMeta, 
  selections, 
  onFilterChange,
  className 
}) => {
  // Local state for collapsed sections
  const [openSections, setOpenSections] = React.useState({});

  const toggleSection = (key) => {
    setOpenSections(prev => ({ ...prev, [key]: !prev[key] }));
  };

  // Helper to get active count for a facet
  const getActiveCount = (key, type) => {
    const val = selections[key];
    if (!val) return 0;
    if (Array.isArray(val)) return val.length;
    if (type === 'range') return (val.min !== undefined || val.max !== undefined) ? 1 : 0;
    if (type === 'boolean') return val !== null ? 1 : 0;
    return 0;
  };

  // Sort facets by priority (if defined) or meta order
  const sortedKeys = Object.keys(facetMeta || {}).sort((a, b) => {
    // Custom sort logic could go here based on a 'priority' field in meta
    return 0; 
  });

  return (
    <div className={cn("w-full space-y-1", className)}>
      <div className="flex items-center justify-between pb-2 mb-2 border-b">
        <h3 className="font-bold text-lg">Filtrele</h3>
        {Object.keys(selections).length > 0 && (
          <Button 
            variant="ghost" 
            size="sm" 
            className="h-8 px-2 text-xs text-muted-foreground hover:text-destructive"
            onClick={() => onFilterChange({})} // Clear all
          >
            Temizle
          </Button>
        )}
      </div>

      {sortedKeys.map(key => {
        const meta = facetMeta[key];
        const data = facets[key];
        
        // Skip if no data available for this facet
        if (!data && meta.type !== 'range') return null;

        const isOpen = openSections[key] ?? true; // Default open
        const activeCount = getActiveCount(key, meta.type);

        let content = null;
        
        switch (meta.type) {
          case 'select':
          case 'multi_select':
            content = (
              <CheckboxFacet 
                facet={{ 
                  key, 
                  label: meta.label, 
                  options: data || [], 
                  selectedValues: selections[key] 
                }} 
                onChange={(vals) => onFilterChange({ ...selections, [key]: vals.length ? vals : undefined })}
              />
            );
            break;
            
          case 'boolean':
             // Assuming boolean facet data structure
             content = (
               <ToggleFacet 
                 facet={{
                    key,
                    label: meta.label,
                    value: selections[key] ?? null,
                    trueCount: data?.trueCount || 0,
                    falseCount: data?.falseCount || 0
                 }}
                 onChange={(val) => onFilterChange({ ...selections, [key]: val })}
               />
             );
             break;

          case 'number':
          case 'range':
            content = (
              <RangeFacet 
                facet={{
                  key,
                  label: meta.label,
                  min: meta.min || 0,
                  max: meta.max || 1000000,
                  unit: meta.unit,
                  selectedMin: selections[key]?.min,
                  selectedMax: selections[key]?.max
                }}
                onChange={(min, max) => {
                   const newVal = {};
                   if (min !== undefined) newVal.min = min;
                   if (max !== undefined) newVal.max = max;
                   // Only update if something is set, else remove key
                   if (Object.keys(newVal).length) {
                     onFilterChange({ ...selections, [key]: newVal });
                   } else {
                     const { [key]: removed, ...rest } = selections;
                     onFilterChange(rest);
                   }
                }}
              />
            );
            break;

          default:
            return null;
        }

        return (
          <FacetGroup 
            key={key} 
            title={meta.label} 
            type={meta.type} 
            isOpen={isOpen} 
            onToggle={() => toggleSection(key)}
            activeCount={activeCount}
          >
            {content}
          </FacetGroup>
        );
      })}
    </div>
  );
};
