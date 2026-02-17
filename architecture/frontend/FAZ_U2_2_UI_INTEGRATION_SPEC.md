# FAZ-U2.2: Wizard UI Integration Spec

## 1. Objective
To build the client-side "Listing Creation Wizard" that consumes the U2/U2.1 Backend APIs.

## 2. Component Architecture

### 2.1. State Management (`WizardContext`)
*   **Store**: `draftId`, `currentStep`, `formData`, `mediaFiles`.
*   **Persistence**: Sync with Backend Draft API (`PATCH /listings-v2/{id}`) on every step change.

### 2.2. Step Components
1.  **CategorySelector**:
    *   Fetches `/api/v1/categories`.
    *   Renders nested list.
    *   On selection -> Create Draft (`POST /listings-v2`).
2.  **AttributeForm**:
    *   Fetches `/api/v1/attributes/form-schema/{cat_id}`.
    *   Renders inputs based on `type`.
    *   Validates required fields.
3.  **MediaUploader**:
    *   File input -> `POST /api/v1/media/upload`.
    *   Displays thumbnails.
    *   Allows reordering (Array manipulation).
4.  **ReviewSubmit**:
    *   Read-only summary.
    *   "Publish" button -> `POST /listings-v2/{id}/submit`.

## 3. Error Handling
*   **Validation Errors**: Display inline (e.g., "Price is required").
*   **API Errors**: Toast notification (e.g., "Upload failed").

## 4. Route Structure
*   `/account/create-listing` (Wrapper)
    *   Renders `<WizardContainer />`.
