# Location Engine Specification

## 1. Objective
To accurately capture the location of a listing for map-based search and "radius" filtering, while maintaining user privacy (optional fuzzing).

## 2. User Flow (Wizard Step: Location)

### 2.1. Country Selection
*   **UI**: Dropdown.
*   **Options**: DE, AT, CH, FR, TR.
*   **Logic**: Sets the context for ZIP validation rules.

### 2.2. ZIP Code (PLZ) Entry
*   **Input**: User enters Postal Code.
*   **Action**: `GET /api/v1/location/validate-zip`.
*   **Response**: Returns `{ city: "Berlin", state: "Berlin", lat: 52.52, lon: 13.40 }`.
*   **Validation**: Must exist in master geo database (GeoNames).

### 2.3. Map Activation & Pinning
*   **Initial State**: Map centers on ZIP code coordinates.
*   **User Action**:
    1.  Enter Street Name (Optional).
    2.  Drag Pin to exact building (or approximate area).
*   **System Action**: Update `lat`/`lon` state.

### 2.4. IP & Verification (Anti-Fraud)
*   **Check**: Compare User IP geo-location with Selected Listing Country.
*   **Flag**: If `Distance(IP, Listing) > 500km`, flag as "Remote Posting" (Risk Signal).

## 3. Database Schema (`listings`)
*   `country`: String(2)
*   `zip_code`: String(10)
*   `city`: String(100)
*   `street`: String(255) (Encrypted/Hidden if private)
*   `latitude`: Float
*   `longitude`: Float
*   `location_accuracy`: Enum(`exact`, `approximate`)

## 4. API Endpoints
*   `GET /api/v1/location/geocode`: Resolves ZIP/Address to Coords.
*   `GET /api/v1/location/reverse`: Resolves Coords to Address (Pin drag).
