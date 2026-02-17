# UI_CHECK_SCOPE_LOCK_NO_REFACTOR

## Faz Kilidi: "Refactor Yok"

Bu faz (FAZ-UI-CHECK-02) kapsamında:
- **Refactor yapılmayacak**.
- Multi-portal ayrıştırma, ayrı login path’leri, route yeniden tasarımı gibi **yapısal değişiklikler yapılmayacak**.
- Amaç: **mevcut yapı üzerinde** kurumsal kalite kontrol, eksik/gap tespiti ve düzeltme backlog’u üretmek.

### Bu fazda yapılacaklar
- 7 arayüz için: checklist + kanıt + PASS/PARTIAL/FAIL kararı.
- Güvenlik/RBAC/country-scope gibi kritik açıklar 🔴 önceliklendirilecek.

### Bu fazda yapılmayacaklar
- Uygulamanın portal bazlı yeniden kurgulanması.
- Tüm route’ların yeniden isimlendirilmesi.
- Büyük komponent parçalama / kapsamlı mimari refactor.
