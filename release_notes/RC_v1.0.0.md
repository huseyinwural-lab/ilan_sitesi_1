## RC v1.0.0 — Release Candidate Notes

### Kapsam (Sprints 2-5)
- Admin Listings + Moderation + Audit-first
- Reports Engine (public submit + admin review)
- Finance Domain (Invoices + Tax Rates + Plans + Revenue)
- System Settings + Countries + Dashboard KPI
- Master Data Engines (Categories, Attributes, Vehicle Make/Model) + Search entegrasyonu

### Sprint 6 Gate Sonuçları
- RBAC / Country-scope / Audit coverage / Critical flows / Non-functional kontrolleri tamamlandı.
- Finance endpoint’leri sadece `finance` + `super_admin` rolü ile sınırlandı.
- Listing publish guard, master data map formatıyla uyumlu hale getirildi.

### Bilinen Riskler
- `UNAUTHORIZED_ROLE_CHANGE_ATTEMPT` audit event’i, permission guard nedeniyle handler’a düşmediğinden gözlemlenmedi. İhtiyaç halinde middleware seviyesinde log’lanabilir.

### Rollback Notu
- Emergent rollback checkpoint kullanılabilir (kod bazında geri dönüş gerekirse).
