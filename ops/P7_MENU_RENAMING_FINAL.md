# P7 Menu Renaming Final Specification

**Date:** 2026-03-15
**Status:** LOCKED

## 1. Renaming Map (English/Code -> Turkish UI)

| Current / Code Key | Old Label | **New Label (Final)** |
| :--- | :--- | :--- |
| `dashboard` | Kontrol Paneli | **Dashboard** |
| `users` | Kullanıcılar | **Kullanıcılar** (Sistem Yöneticileri) |
| `members_individual`| - | **Bireysel Kullanıcılar** (New) |
| `dealers` | Dealers | **Ticari Üyeler** |
| `categories` | Categories | **Kategori Yönetimi** |
| `attributes` | Attributes | **İlan Alanları** |
| `moderation` | Moderation | **İçerik Denetimi** |
| `premium` | Premium | **Paket & Vitrin Yönetimi** |
| `invoices` | Invoices | **Faturalar** |
| `tax_rates` | Tax Rates | **Vergi Oranları** |
| `countries` | Ülkeler | **Ülke & Lokalizasyon** |
| `feature_flags` | Özellik Bayrakları| **Sistem Özellikleri** |
| `menu` | Menu | **Menü Yönetimi** |
| `audit_logs` | Denetim Kayıtları | **Sistem Logları** |

## 2. Implementation Rules
-   **Breadcrumbs:** Must match the New Label exactly.
-   **Page Titles:** `<title>New Label - Admin Panel</title>`.
-   **Sidebar:** Update `sidebar_config.js` or database `top_menu_items`.
