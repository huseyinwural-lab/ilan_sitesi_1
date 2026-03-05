import React from 'react';
import { Link } from 'react-router-dom';

const sanitizeKey = (value) => String(value || 'menu').replace(/[^a-zA-Z0-9-]/g, '-');

const normalizeMenuChildren = (rawChildren) => {
  if (!Array.isArray(rawChildren)) return [];
  return rawChildren
    .filter((item) => item && item.label)
    .map((item) => ({
      id: item.id || item.slug || item.label,
      label: item.label,
      url: item.url || '',
    }));
};

export const MenuSnapshotBlock = ({ props, componentKey = 'menu.snapshot' }) => {
  const snapshot = props?.menu_snapshot && typeof props.menu_snapshot === 'object' ? props.menu_snapshot : {};
  const title = props?.title || snapshot.label || props?.menu_label || 'Menü Bloğu';
  const url = props?.menu_url || snapshot.url || '';
  const mode = props?.style === 'chips' ? 'chips' : 'list';
  const showChildren = props?.show_children !== false;
  const maxChildren = Math.max(1, Math.min(20, Number(props?.max_children || 8)));
  const children = normalizeMenuChildren(snapshot.children).slice(0, maxChildren);
  const keySuffix = sanitizeKey(componentKey);

  return (
    <section className="rounded-xl border bg-white p-4" data-testid={`runtime-menu-block-${keySuffix}`}>
      <div className="flex flex-wrap items-center justify-between gap-2" data-testid={`runtime-menu-block-header-${keySuffix}`}>
        <h3 className="text-sm font-semibold text-slate-900" data-testid={`runtime-menu-block-title-${keySuffix}`}>{title}</h3>
        {url ? (
          <Link className="text-xs font-medium text-sky-700 underline" to={url} data-testid={`runtime-menu-block-main-link-${keySuffix}`}>
            Menüye Git
          </Link>
        ) : null}
      </div>

      {showChildren && children.length > 0 ? (
        <div
          className={`mt-3 ${mode === 'chips' ? 'flex flex-wrap gap-2' : 'space-y-2'}`}
          data-testid={`runtime-menu-block-children-${keySuffix}`}
        >
          {children.map((item) => (
            <Link
              key={item.id}
              to={item.url || '#'}
              className={mode === 'chips'
                ? 'rounded-full border border-slate-300 bg-slate-50 px-3 py-1 text-xs text-slate-700 transition hover:bg-slate-100'
                : 'block rounded-md border border-slate-200 px-3 py-2 text-xs text-slate-700 transition hover:border-sky-300 hover:bg-sky-50'}
              data-testid={`runtime-menu-block-child-${keySuffix}-${sanitizeKey(item.id)}`}
            >
              {item.label}
            </Link>
          ))}
        </div>
      ) : (
        <p className="mt-2 text-xs text-slate-500" data-testid={`runtime-menu-block-empty-${keySuffix}`}>
          Bu menü için gösterilecek alt menü bulunmuyor.
        </p>
      )}
    </section>
  );
};
