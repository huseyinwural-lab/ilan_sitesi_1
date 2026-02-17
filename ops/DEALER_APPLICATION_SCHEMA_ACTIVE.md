# DEALER_APPLICATION_SCHEMA_ACTIVE

## Amaç
`dealer_applications` koleksiyonunu SPRINT 1.2 kapsamında aktif etmek ve alanları kilitlemek.

## Koleksiyon
- `dealer_applications`

## Alanlar
- `id` (uuid)
- `email`
- `company_name`
- `country_code`
- `status` (`pending` | `approved` | `rejected`)
- `reason` (reject için zorunlu; enum: /app/architecture/DEALER_APPLICATION_REASON_ENUMS_V1.md)
- `reason_note` (`reason=other` için zorunlu)
- `created_at`
- `reviewed_at`
- `reviewed_by` (admin user id)
- `updated_at`

## Index önerileri (MVP)
- `status`
- `country_code`
- `email`
- `created_at`
