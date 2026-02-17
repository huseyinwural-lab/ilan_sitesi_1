# P20: Mobile Rate Limit Configuration

## 1. Objective
Protect the backend from abusive automated mobile traffic while allowing legitimate heavy users.

## 2. Segmentation
We will identify mobile traffic via headers.
*   **Header**: `X-Device-ID` (Unique UUID generated on install).
*   **User-Agent**: Contains `EmergentMobile/1.0`.

## 3. Limits
| Scope | Limit | Action |
| :--- | :--- | :--- |
| **Auth** (Login) | 5 / minute | Block IP for 15 mins. |
| **Feed** (Scroll) | 60 / minute | Soft throttle (429). |
| **Detail** (View) | 100 / minute | Soft throttle (429). |

## 4. Implementation
*   **Redis**: Use Redis to count hits per `X-Device-ID`.
*   **Response**: 429 Too Many Requests.
