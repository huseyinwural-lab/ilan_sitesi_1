# FAZ-U2.1: Wizard & Media Scope

## 1. Wizard Flow
The listing creation process is divided into 4 linear steps.

### Step 1: Category Selection
*   **UI**: Breadcrumb-style or Nested List.
*   **Logic**: User must select a *leaf* category to proceed.
*   **API**: `GET /api/v1/categories` (Recursive or Level-based).

### Step 2: Details (Dynamic Attributes)
*   **UI**: Form generated based on Category Attributes.
*   **Inputs**: Text, Number, Select, Checkbox, Date.
*   **API**: `GET /api/v1/attributes/form-schema/{category_id}`.
*   **Validation**: Server-side validation of required attributes.

### Step 3: Media Upload
*   **UI**: Drag & Drop zone. Reordering support.
*   **Constraints**: Max 20 images, Max 5MB each.
*   **API**: `POST /api/v1/media/upload`.

### Step 4: Preview & Publish
*   **UI**: Summary card.
*   **Action**: `POST /submit` (Triggers Status `PENDING_MODERATION`).

## 2. Media Service Spec (MVP)
*   **Storage**: Local Filesystem (`/app/backend/static/uploads`) for Dev/MVP.
*   **URL**: `/static/uploads/{filename}`.
*   **Processing**:
    *   Rename file to UUID.
    *   Validate MIME type (`image/jpeg`, `image/png`).
    *   (Future) Resize/WebP conversion.
