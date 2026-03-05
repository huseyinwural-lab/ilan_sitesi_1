import React, { useMemo } from 'react';

const clampWidth = (value, fallback = 12) => {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return fallback;
  return Math.max(1, Math.min(12, Math.floor(numeric)));
};

const normalizeRows = (payload) => {
  if (!payload || typeof payload !== 'object') return [];
  const rawRows = Array.isArray(payload.rows) ? payload.rows : [];
  return rawRows.map((row, rowIndex) => {
    const columns = Array.isArray(row?.columns) ? row.columns : [];
    return {
      id: row?.id || `row-${rowIndex + 1}`,
      columns: columns.map((column, colIndex) => ({
        id: column?.id || `col-${rowIndex + 1}-${colIndex + 1}`,
        width: {
          desktop: clampWidth(column?.width?.desktop ?? column?.width ?? 12, 12),
          tablet: clampWidth(column?.width?.tablet ?? column?.width ?? 12, 12),
          mobile: clampWidth(column?.width?.mobile ?? 12, 12),
        },
        components: Array.isArray(column?.components)
          ? column.components.map((component, componentIndex) => ({
              id: component?.id || `cmp-${rowIndex + 1}-${colIndex + 1}-${componentIndex + 1}`,
              key: component?.key || 'unknown.component',
              props: component?.props && typeof component.props === 'object' ? component.props : {},
              visibility: component?.visibility && typeof component.visibility === 'object' ? component.visibility : {},
            }))
          : [],
      })),
    };
  });
};

const resolveRenderer = (registry, componentKey) => {
  if (!registry || typeof registry !== 'object') return null;
  if (registry[componentKey]) return registry[componentKey];

  const entries = Object.entries(registry);
  for (const [pattern, renderer] of entries) {
    if (!pattern.endsWith('*')) continue;
    const prefix = pattern.slice(0, -1);
    if (prefix && String(componentKey || '').startsWith(prefix)) {
      return renderer;
    }
  }
  return null;
};

export default function LayoutRenderer({
  payload,
  registry = {},
  dataTestIdPrefix = 'layout-renderer',
}) {
  const rows = useMemo(() => normalizeRows(payload), [payload]);

  if (!rows.length) {
    return null;
  }

  return (
    <div className="space-y-5" data-testid={`${dataTestIdPrefix}-root`}>
      {rows.map((row, rowIndex) => (
        <section className="grid grid-cols-12 gap-4" key={row.id} data-testid={`${dataTestIdPrefix}-row-${rowIndex}`}>
          {row.columns.map((column, columnIndex) => (
            <div
              key={column.id}
              className="col-span-12"
              style={{
                gridColumn: `span ${column.width.desktop} / span ${column.width.desktop}`,
              }}
              data-testid={`${dataTestIdPrefix}-row-${rowIndex}-column-${columnIndex}`}
            >
              <div className="space-y-3" data-testid={`${dataTestIdPrefix}-column-components-${rowIndex}-${columnIndex}`}>
                {column.components.map((component, componentIndex) => {
                  const renderer = resolveRenderer(registry, component.key);
                  if (!renderer) {
                    return (
                      <div
                        key={component.id}
                        className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-3 text-sm text-slate-500"
                        data-testid={`${dataTestIdPrefix}-missing-component-${rowIndex}-${columnIndex}-${componentIndex}`}
                      >
                        Tanımsız bileşen: <strong>{component.key}</strong>
                      </div>
                    );
                  }

                  return (
                    <div key={component.id} data-testid={`${dataTestIdPrefix}-component-${component.key}-${rowIndex}-${columnIndex}-${componentIndex}`}>
                      {renderer({
                        props: component.props || {},
                        component,
                        row,
                        column,
                        rowIndex,
                        columnIndex,
                        componentIndex,
                      })}
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </section>
      ))}
    </div>
  );
}
