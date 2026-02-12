# API Error Contract (Addendum v1.0)

This document standardizes the HTTP error codes used across the Pricing, Commercial, and Core domains.

## 1. Global Rules
- **Consistency:** All endpoints must return standard Pydantic models or JSON for errors.
- **Security:** Do not leak stack traces in 500 errors.

## 2. Status Code Definitions

### 400 Bad Request
- **Usage:** Invalid input syntax, missing required fields (Pydantic validation), or logical domain errors that are client-fixable.
- **Example:** "Invalid email format", "Refund amount negative".

### 401 Unauthorized
- **Usage:** Missing or invalid authentication token.
- **Action:** Client should redirect to login.

### 403 Forbidden
- **Usage:** Authenticated, but lacks permission or **Quota Exceeded** (Old Logic).
- **Note:** For Pricing Engine, we moved "Missing Config" from 403 to 409. 403 is now strictly for "You are not allowed" or "Account Suspended".

### 409 Conflict (CRITICAL)
- **Usage:** State of the system prevents the action.
- **Scenarios:**
  - **Missing Pricing Configuration:** (e.g., No PriceConfig for 'DE').
  - **Missing VAT Rate:** (e.g., No VAT for 'FR').
  - **Duplicate Resource:** (e.g., Registering existing email).
  - **State Mismatch:** (e.g., Trying to publish a 'suspended' listing).
- **Client Action:** Show specific error message; usually requires Admin intervention or User fixing data.

### 422 Unprocessable Entity
- **Usage:** Standard FastAPI validation error (wrong data types).

### 429 Too Many Requests
- **Usage:** Rate limit exceeded.
- **Action:** Client must wait `Retry-After` seconds.

## 3. Error Response Body
```json
{
  "detail": "Human readable message",
  "code": "optional_machine_code",  // e.g. "pricing_config_missing"
  "meta": {} // Optional context
}
```
