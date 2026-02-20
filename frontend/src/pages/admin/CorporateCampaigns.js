import CampaignsManager from './CampaignsManager';

export default function CorporateCampaigns() {
  return (
    <CampaignsManager
      campaignType="corporate"
      title="Kurumsal Kampanyalar"
      subtitle="Kurumsal kampanyaları yönetin"
      testIdPrefix="corporate-campaigns"
    />
  );
}
