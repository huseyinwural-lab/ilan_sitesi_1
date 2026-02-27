import React, { useState } from 'react';

import { CorporateHeaderDesigner } from './ui-designer/CorporateHeaderDesigner';
import { CorporateDashboardDesigner } from './ui-designer/CorporateDashboardDesigner';
import { ThemeTokenManagementTab } from './ui-designer/ThemeTokenManagementTab';

export default function AdminUserInterfaceDesignV2() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="space-y-6" data-testid="admin-user-interface-design-page">
      <div data-testid="admin-user-interface-design-header">
        <h1 className="text-2xl font-semibold" data-testid="admin-user-interface-design-title">Kullanıcı Tasarım</h1>
        <p className="text-sm text-slate-600" data-testid="admin-user-interface-design-subtitle">
          Dealer Dashboard V2: Grid DnD editör, kurumsal header yönetimi, draft→preview→publish ve rollback
        </p>
      </div>

      <div className="flex flex-wrap gap-2" data-testid="admin-user-interface-design-tabs">
        <button
          type="button"
          onClick={() => setActiveTab('dashboard')}
          className={`h-10 rounded-md border px-4 text-sm ${activeTab === 'dashboard' ? 'bg-slate-900 text-white' : ''}`}
          data-testid="admin-user-interface-design-tab-dashboard"
        >
          Kurumsal Dashboard V2
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('corporate-header')}
          className={`h-10 rounded-md border px-4 text-sm ${activeTab === 'corporate-header' ? 'bg-slate-900 text-white' : ''}`}
          data-testid="admin-user-interface-design-tab-corporate-header"
        >
          Kurumsal Header Tasarım
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('theme')}
          className={`h-10 rounded-md border px-4 text-sm ${activeTab === 'theme' ? 'bg-slate-900 text-white' : ''}`}
          data-testid="admin-user-interface-design-tab-theme"
        >
          Tema Yönetimi
        </button>
      </div>

      <div className="rounded-xl border bg-white p-4" data-testid="admin-user-interface-design-tab-content">
        {activeTab === 'dashboard' ? <CorporateDashboardDesigner /> : null}
        {activeTab === 'corporate-header' ? <CorporateHeaderDesigner /> : null}
        {activeTab === 'theme' ? <ThemeTokenManagementTab /> : null}
      </div>
    </div>
  );
}
