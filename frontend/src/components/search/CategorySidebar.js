import React from 'react';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, Folder } from 'lucide-react';
import { cn } from '@/lib/utils';

export const CategorySidebar = ({ 
  categories, 
  activeCategorySlug, 
  onCategoryChange 
}) => {
  // Flatten tree to find active category and its relations easily
  // Assuming categories is a flat list for now, or we traverse tree.
  // API returns flat list on /api/categories which is easier for lookup.
  
  const activeCategory = categories.find(c => c.slug.en === activeCategorySlug || c.slug.tr === activeCategorySlug); // fallback logic
  
  // Find Parent
  const parentCategory = activeCategory?.parent_id 
    ? categories.find(c => c.id === activeCategory.parent_id)
    : null;

  // Find Children
  const childCategories = activeCategory 
    ? categories.filter(c => c.parent_id === activeCategory.id)
    : categories.filter(c => !c.parent_id); // Root categories if none active

  // Find Siblings (if no children, show siblings to allow lateral move)
  const siblingCategories = activeCategory && childCategories.length === 0 && activeCategory.parent_id
    ? categories.filter(c => c.parent_id === activeCategory.parent_id)
    : [];

  const displayCategories = childCategories.length > 0 ? childCategories : siblingCategories;
  const listTitle = childCategories.length > 0 ? 'Alt Kategoriler' : 'Diğer Kategoriler';

  if (!categories || categories.length === 0) return null;

  return (
    <div className="space-y-4 mb-6">
      <div className="flex items-center gap-2 font-semibold text-sm text-foreground/80">
        <Folder className="h-4 w-4" />
        Kategoriler
      </div>

      {/* Navigation Header */}
      {activeCategory && (
        <div className="space-y-2">
          {parentCategory ? (
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start px-0 text-muted-foreground hover:text-foreground h-auto py-1"
              onClick={() => onCategoryChange(parentCategory.slug.en || parentCategory.slug.tr)}
            >
              <ChevronLeft className="h-3 w-3 mr-1" />
              {parentCategory.translations?.find(t => t.language === 'tr')?.name || parentCategory.slug.en}
            </Button>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start px-0 text-muted-foreground hover:text-foreground h-auto py-1"
              onClick={() => onCategoryChange(null)}
            >
              <ChevronLeft className="h-3 w-3 mr-1" />
              Tüm Kategoriler
            </Button>
          )}
          
          <div className="font-bold text-lg px-1">
            {activeCategory.translations?.find(t => t.language === 'tr')?.name || activeCategory.slug.en}
          </div>
        </div>
      )}

      {/* Category List */}
      <div className="space-y-1">
        {activeCategory && childCategories.length === 0 && (
           <div className="px-2 py-1.5 text-sm font-medium bg-primary/10 text-primary rounded-md">
             {activeCategory.translations?.find(t => t.language === 'tr')?.name || activeCategory.slug.en}
           </div>
        )}
        
        {displayCategories.map(cat => (
          <Button
            key={cat.id}
            variant="ghost"
            className={cn(
              "w-full justify-between h-8 px-2 text-sm font-normal",
              activeCategorySlug === cat.slug.en ? "bg-accent text-accent-foreground font-medium" : "text-muted-foreground"
            )}
            onClick={() => onCategoryChange(cat.slug.en || cat.slug.tr)}
          >
            <span>{cat.translations?.find(t => t.language === 'tr')?.name || cat.slug.en}</span>
            {cat.listing_count > 0 && (
              <span className="text-xs text-muted-foreground ml-2">({cat.listing_count})</span>
            )}
          </Button>
        ))}
      </div>
    </div>
  );
};
