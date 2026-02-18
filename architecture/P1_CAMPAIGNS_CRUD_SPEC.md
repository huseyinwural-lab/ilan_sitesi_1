## P1 Kampanyalar CRUD Spec

### Kapsam
- Bireysel ve Kurumsal kampanya yönetimi
- Tarih aralığı + kota/indirim ilişkisi

### Campaign Alanları (MVP)
- id
- type: individual | corporate
- name
- country_code
- start_date (ISO8601)
- end_date (ISO8601)
- active_flag
- discount_type: percent | fixed
- discount_value
- quota_limit (opsiyonel)
- created_at / updated_at

### Kurallar
- start_date < end_date zorunlu
- active_flag=true ve tarih aralığı uygunsa aktif
- quota_limit dolduğunda kampanya pasif sayılır
- country_code zorunlu (global kampanya yok)

### Admin UI
- Liste + filtre (type, country, active)
- Create/Edit form (tarih + indirim + kota)
- Soft delete
