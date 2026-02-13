# Correlation ID Policy v1

**Header:** `X-Request-ID`

## 1. Ingress
-   **Middleware:** Reads header from Client/LB.
-   **Generation:** If missing, generates `uuid4`.
-   **Context:** Stores in `contextvars`.

## 2. Egress (Response)
-   **Header:** Adds `X-Request-ID` to every HTTP response.
-   **Error Body:** Adds `request_id` to JSON error payload.

## 3. Usage
-   **Logs:** Automatically injected into every log line via `structlog`.
-   **DB:** Optional trace tagging (if APM used).
