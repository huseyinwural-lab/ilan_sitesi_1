import React, { useMemo } from 'react';
import { Loader2 } from 'lucide-react';
import AdSlot from '@/components/public/AdSlot';
import LayoutRenderer from '@/components/layout-builder/LayoutRenderer';
import { MenuSnapshotBlock } from '@/components/layout-builder/MenuSnapshotBlock';
import { EXTENDED_RUNTIME_REGISTRY } from '@/components/layout-builder/ExtendedRuntimeBlocks';
import { useContentLayoutResolve } from '@/hooks/useContentLayoutResolve';

const HomeLayoutEmptyState = ({ countryCode, error }) => (
  <section className="rounded-xl border border-dashed bg-white p-6 text-center" data-testid="home-runtime-layout-empty-state">
    <h1 className="text-base font-semibold" data-testid="home-runtime-layout-empty-title">Home layout bulunamadı</h1>
    <p className="mt-1 text-sm text-slate-600" data-testid="home-runtime-layout-empty-description">
      İçerik sadece Admin &gt; Site Design &gt; Content Builder publish edilmiş düzenlerden gösterilir.
    </p>
    <p className="mt-2 text-xs text-slate-500" data-testid="home-runtime-layout-empty-meta">
      country={countryCode} · page_type=home · module=global · error={error || 'none'}
    </p>
  </section>
);

export default function HomePageRefreshed() {
  const countryCode = useMemo(() => (localStorage.getItem('selected_country') || 'DE').toUpperCase(), []);

  const {
    loading,
    layout: resolvedHomeLayout,
    error,
    hasLayoutRows,
  } = useContentLayoutResolve({
    country: countryCode,
    module: 'global',
    pageType: 'home',
    enabled: Boolean(countryCode),
  });

  const runtimeRegistry = {
    ...EXTENDED_RUNTIME_REGISTRY,
    'shared.text-block': ({ props }) => (
      <section className="rounded-xl border bg-white p-4" data-testid="home-runtime-text-block">
        <h2 className="text-base font-semibold" data-testid="home-runtime-text-title">{props?.title || 'Başlık'}</h2>
        <p className="mt-1 text-sm text-slate-600" data-testid="home-runtime-text-body">{props?.body || ''}</p>
      </section>
    ),
    'shared.ad-slot': ({ props }) => (
      <section data-testid="home-runtime-ad-slot">
        <AdSlot placement={props?.placement || 'AD_HOME_TOP'} className="rounded-xl border" />
      </section>
    ),
    'menu.snapshot.*': ({ props, component }) => (
      <MenuSnapshotBlock props={props} componentKey={component?.key} />
    ),
  };

  const runtimeContext = useMemo(() => ({
    countryCode,
    module: 'global',
  }), [countryCode]);

  return (
    <div className="home-runtime-page" data-testid="home-runtime-page">
      {loading ? (
        <div className="flex min-h-[220px] items-center justify-center" data-testid="home-runtime-layout-loading">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : null}

      {!loading && hasLayoutRows ? (
        <LayoutRenderer
          payload={resolvedHomeLayout?.revision?.payload_json}
          registry={runtimeRegistry}
          runtimeContext={runtimeContext}
          dataTestIdPrefix="home-runtime-layout"
        />
      ) : null}

      {!loading && !hasLayoutRows ? (
        <HomeLayoutEmptyState countryCode={countryCode} error={error} />
      ) : null}
    </div>
  );
}
