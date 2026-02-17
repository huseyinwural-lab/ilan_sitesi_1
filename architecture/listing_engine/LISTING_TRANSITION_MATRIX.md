# Listing Transition Matrix

## 1. Geçiş Tablosu

| Mevcut Durum | Hedef Durum | Tetikleyici | Koşul |
| :--- | :--- | :--- | :--- |
| `None` (New) | `DRAFT` | `create_draft` | - |
| `DRAFT` | `PENDING_MODERATION` | `submit_listing` | %100 Completion |
| `PENDING_MODERATION` | `ACTIVE` | `approve_listing` | Admin/Auto Check |
| `PENDING_MODERATION` | `REJECTED` | `reject_listing` | Reason Required |
| `REJECTED` | `DRAFT` | `edit_listing` | - |
| `ACTIVE` | `EXPIRED` | `cron_job` | Date > expires_at |
| `ACTIVE` | `SOLD` | `mark_sold` | User Action |
| `ACTIVE` | `SUSPENDED` | `suspend_listing` | Admin Action |
| `*` | `DELETED` | `delete_listing` | Soft Delete |

## 2. Yasaklı Geçişler
*   `DRAFT` -> `ACTIVE` (Asla direkt geçiş yok, moderasyon şart).
*   `REJECTED` -> `ACTIVE` (Önce düzenlenip tekrar onaya girmeli).
*   `DELETED` -> `ACTIVE` (Geri dönüş yok, yeni ilan açılmalı).
