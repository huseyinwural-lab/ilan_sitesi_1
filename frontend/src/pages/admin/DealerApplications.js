import SupportApplications from './SupportApplications';

export default function DealerApplications() {
  return (
    <SupportApplications
      applicationType="dealer"
      title="Kurumsal Başvurular"
      subtitle="Kurumsal kullanıcı başvurularını yönetin"
      testIdPrefix="dealer-applications"
    />
  );
}
