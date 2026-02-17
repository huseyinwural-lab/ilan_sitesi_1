# ADMIN_AUDIT_COUNTRY_SCOPE_ENHANCEMENT

## Amaç
Admin işlemlerinde country scope ve mode’un audit log’da görünmesi.

## Log Alanları
- ts
- user_id
- action
- resource
- mode: global|country
- country_scope: null|"DE"
- request_path

## MVP
- Bu iterasyonda mevcut audit log altyapısı yoksa, en azından:
  - önemli admin write işlemlerinde (countries PATCH gibi)
  - MongoDB’de `admin_audit_logs` koleksiyonuna append yapılır.
