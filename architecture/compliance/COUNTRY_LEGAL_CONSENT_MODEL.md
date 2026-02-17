# Country Legal Consent Model

## 1. Requirement
Every user must accept the Terms & Conditions (AGB) and Privacy Policy (Datenschutz) specific to their country of residence or the platform's operating country.

## 2. Consent Versioning
Legal texts change. We must track *which version* a user accepted.

### 2.1. Schema: `legal_consents`
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | UUID | PK |
| `user_id` | UUID | FK |
| `country_code` | String | Context of consent |
| `document_type` | String | `terms`, `privacy`, `marketing` |
| `version` | String | `v1.0`, `v2026.01` |
| `ip_address` | String | Audit requirement |
| `accepted_at` | DateTime | Timestamp |

## 3. Flow
1.  **Signup**: User selects Country -> Backend fetches active `terms_v1.0_de` -> User accepts -> `legal_consents` row created.
2.  **Login**: Check if `current_version` > `accepted_version`. If so, show "New Terms" modal.
