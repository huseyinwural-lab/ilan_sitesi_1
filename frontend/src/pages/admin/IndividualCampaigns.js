import CampaignsManager from './CampaignsManager';

export default function IndividualCampaigns() {
  return (
    <CampaignsManager
      campaignType="individual"
      title="Bireysel Kampanyalar"
      subtitle="Bireysel kullanıcı kampanyalarını yönetin"
      testIdPrefix="individual-campaigns"
    />
  );
}
