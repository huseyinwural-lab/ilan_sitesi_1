import React from "react";
import AdminPlaceholder from "../../components/AdminPlaceholder";

export default function IndividualApplications() {
  return (
    <AdminPlaceholder
      title="Bireysel Üye Başvurular"
      description="Mevcut sistemde bireysel başvuru kaydı bulunmuyor. Veri oluştuğunda liste burada görünecek."
      status="EMPTY"
      note="Yeni koleksiyon açılmadan v1’de yalnızca boş state gösterilir."
      testId="individual-applications-placeholder"
    />
  );
}
