import React, { useState } from 'react';

import { CorporateHeaderDesigner } from './ui-designer/CorporateHeaderDesigner';
import { IndividualHeaderConfigTab } from './ui-designer/IndividualHeaderConfigTab';
import { ThemeTokenManagementTab } from './ui-designer/ThemeTokenManagementTab';

export default function AdminUserInterfaceDesignV2() {
  const [activeTab, setActiveTab] = useState('corporate');

  return (
    <div className="space-y-6" data-testid="admin-user-interface-design-page">
      <div data-testid="admin-user-interface-design-header">
        <h1 className="text-2xl font-semibold" data-testid="admin-user-interface-design-title">Kullanıcı Tasarım</h1>
        <p className="text-sm text-slate-600" data-testid="admin-user-interface-design-subtitle">
          Sprint 2 başlangıcı: Kurumsal Header 3 satır drag&drop + Row1 logo upload + token bazlı tema editörü
        </p>
      </div>

      <div className="flex flex-wrap gap-2" data-testid="admin-user-interface-design-tabs">
        <button
          type="button"
          onClick={() => setActiveTab('corporate')}
          className={`h-10 rounded-md border px-4 text-sm ${activeTab === 'corporate' ? 'bg-slate-900 text-white' : ''}`}
          data-testid="admin-user-interface-design-tab-corporate"
        >
          Kurumsal UI Tasarım
        </button>
        <button
          type="button"
          onClick={() => setActiveTab('individual')}
          className={`h-10 rounded-md border px-4 text-sm ${activeTab === 'individual' ? 'bg-slate-900 text-white' : ''}`}
          data-testid="admin-user-interface-design-tab-individual"
        >
          Bireysel Header Tasarım
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
        {activeTab === 'corporate' ? <CorporateHeaderDesigner /> : null}
        {activeTab === 'individual' ? <IndividualHeaderConfigTab /> : null}
        {activeTab === 'theme' ? <ThemeTokenManagementTab /> : null}
      </div>
    </div>
  );
}
