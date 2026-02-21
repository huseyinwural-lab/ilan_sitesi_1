# DATA_MODEL_SPEC_EU_PROFILES_V1

## consumer_profile
- id (UUID, PK)
- user_id (FK → users.id, unique)
- display_name
- locale
- country_code
- avatar_url
- marketing_consent (bool)
- created_at / updated_at

## dealer_profile
- id (UUID, PK)
- user_id (FK → users.id, unique)
- company_name (required)
- vat_id (required)
- trade_registry_no
- legal_representative
- address_json (EU format)
- logo_url
- consumer_info_text
- controller_settings_json
- created_at / updated_at

## Notlar
- Profil tabloları FAZ-EU-PANEL-02’de migration olarak uygulanacak.
