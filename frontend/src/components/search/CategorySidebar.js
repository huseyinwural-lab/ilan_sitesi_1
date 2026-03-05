import React, { useEffect, useMemo, useState } from 'react';
import { ChevronDown, ChevronRight, Folder } from 'lucide-react';
import { cn } from '@/lib/utils';

const normalizeToken = (value) => String(value || '').trim().toLowerCase();

const buildL0L1Tree = (categories = []) => {
  const byParent = new Map();
  categories.forEach((item) => {
    const parentKey = item?.parent_id || '__root__';
    if (!byParent.has(parentKey)) byParent.set(parentKey, []);
    byParent.get(parentKey).push(item);
  });

  const sortNodes = (items) => [...items].sort((a, b) => {
    const aOrder = Number(a?.sort_order || 0);
    const bOrder = Number(b?.sort_order || 0);
    if (aOrder !== bOrder) return aOrder - bOrder;
    return String(a?.name || '').localeCompare(String(b?.name || ''), 'tr');
  });

  return sortNodes(byParent.get('__root__') || []).map((root) => ({
    ...root,
    children: sortNodes(byParent.get(root.id) || []),
  }));
};

export const CategorySidebar = ({
  categories,
  activeCategorySlug,
  onCategoryChange,
  showCounts = true,
  treeBehavior = 'expanded',
}) => {
  const tree = useMemo(() => buildL0L1Tree(Array.isArray(categories) ? categories : []), [categories]);
  const [openRootId, setOpenRootId] = useState('');
  const selectedToken = normalizeToken(activeCategorySlug);

  useEffect(() => {
    if (!selectedToken || !tree.length) return;
    const matchedRoot = tree.find((root) => {
      const rootMatches = [root.id, root.slug].some((token) => normalizeToken(token) === selectedToken);
      const childMatches = (root.children || []).some((child) => [child.id, child.slug].some((token) => normalizeToken(token) === selectedToken));
      return rootMatches || childMatches;
    });
    if (matchedRoot?.id) setOpenRootId(matchedRoot.id);
  }, [selectedToken, tree]);

  if (!tree.length) return null;

  return (
    <div className="mb-6 space-y-3" data-testid="category-sidebar-tree-root">
      <div className="flex items-center gap-2 text-sm font-semibold text-foreground/80" data-testid="category-sidebar-tree-title">
        <Folder className="h-4 w-4" />
        Kategoriler
      </div>

      <div className="rounded-lg border bg-white p-2" data-testid="category-sidebar-tree-container">
        {tree.map((root) => {
          const rootToken = root.id || root.slug;
          const rootSelected = [root.id, root.slug].some((token) => normalizeToken(token) === selectedToken);
          const isOpen = treeBehavior === 'expanded' || openRootId === root.id;
          const hasChildren = Array.isArray(root.children) && root.children.length > 0;

          return (
            <div key={root.id} className="border-b last:border-b-0" data-testid={`category-sidebar-root-${root.id}`}>
              <div className="flex items-center gap-1 py-1">
                {hasChildren ? (
                  <button
                    type="button"
                    onClick={() => setOpenRootId((prev) => (prev === root.id ? '' : root.id))}
                    className="rounded p-1 text-slate-500 hover:bg-slate-100"
                    data-testid={`category-sidebar-root-toggle-${root.id}`}
                  >
                    {isOpen ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
                  </button>
                ) : <span className="inline-block h-6 w-6" aria-hidden="true" />}

                <button
                  type="button"
                  onClick={() => onCategoryChange(rootToken || null)}
                  className={cn(
                    'flex w-full items-center justify-between rounded-md px-2 py-1.5 text-left text-sm transition',
                    rootSelected ? 'bg-slate-900 font-semibold text-white' : 'font-semibold text-slate-800 hover:bg-slate-100',
                  )}
                  data-testid={`category-sidebar-root-select-${root.id}`}
                >
                  <span>{root.name}</span>
                  {showCounts ? <span className={cn('text-xs', rootSelected ? 'text-white/90' : 'text-slate-500')}>({Number(root.listing_count || 0)})</span> : null}
                </button>
              </div>

              {hasChildren && isOpen ? (
                <div className="mb-2 ml-7 space-y-1" data-testid={`category-sidebar-children-${root.id}`}>
                  {root.children.map((child) => {
                    const childToken = child.id || child.slug;
                    const childSelected = [child.id, child.slug].some((token) => normalizeToken(token) === selectedToken);
                    return (
                      <button
                        key={child.id}
                        type="button"
                        onClick={() => onCategoryChange(childToken || null)}
                        className={cn(
                          'flex w-full items-center justify-between rounded-md px-2 py-1 text-left text-sm transition',
                          childSelected ? 'bg-blue-50 font-medium text-blue-700' : 'text-slate-600 hover:bg-slate-50',
                        )}
                        data-testid={`category-sidebar-child-select-${child.id}`}
                      >
                        <span>{child.name}</span>
                        {showCounts ? <span className="text-xs text-slate-500">({Number(child.listing_count || 0)})</span> : null}
                      </button>
                    );
                  })}
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
    </div>
  );
};
