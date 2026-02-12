# Tier Rate Limit Matrix (v1)

**Config Source:** `app.core.config` / Env Vars
**Effective Date:** P6 Sprint 2 Cutover

## 1. Limits by Tier (Write / Auth)
| Tier | Limit (Req/Min) | Burst (Max concurrent) | Rationale |
| :--- | :--- | :--- | :--- |
| **STANDARD** | 60 | 5 | Base limit to prevent spam. |
| **PREMIUM** | 300 | 20 | Supports bulk upload scripts. |
| **ENTERPRISE** | 1000 | 50 | High volume API integration. |
| **ADMIN** | 5000 | 100 | Internal operations. |
| **ANONYMOUS** | 20 | 0 | Login/Register protection. |

## 2. Read Limits (Public)
-   Global Default: 100/min (IP Based).
-   Logged In: 300/min (User Based).

## 3. Configuration Management
-   Changes require PR to `app/core/config.py`.
-   Hot-reload not supported (requires deployment).
-   Emergency Override: Redis Key `config:limit:override:{tier}` (if implemented in Lua).
