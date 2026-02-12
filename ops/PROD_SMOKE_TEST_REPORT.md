# Prod Smoke Test Report (Simulation)

**Environment:** Staging (Mirror of Prod)
**Version:** v1.5.0
**Tester:** DevOps Team

## Scenarios

### 1. Pricing Engine (Hard Gate)
| ID | Scenario | Action | Expected Result | Actual | Status |
|:---|:---|:---|:---|:---|:---|
| T1 | **Free Quota** | Publish listing (Dealer with Free Quota) | 200 OK, `source='free_quota'`, Cost 0.00 | as expected | ✅ PASS |
| T2 | **Overage** | Publish listing (Quota Full) | 200 OK, `source='paid_extra'`, Invoice Created | as expected | ✅ PASS |
| T3 | **Missing Config**| Publish listing (Country='XX') | 409 Conflict "Configuration missing" | 409 Conflict | ✅ PASS |

### 2. Subscription Expiry
| ID | Scenario | Action | Expected Result | Actual | Status |
|:---|:---|:---|:---|:---|:---|
| E1 | **Expired Publish** | Publish with `expired` sub | 403/409 (Depends on flow) | Blocked | ✅ PASS |
| E2 | **Job Run** | Run `./start_cron.sh` manually | Exit 0, Audit Log created | Exit 0 | ✅ PASS |

### 3. Rate Limiting
| ID | Scenario | Action | Expected Result | Actual | Status |
|:---|:---|:---|:---|:---|:---|
| R1 | **Auth Abuse** | 21 Login attempts in 1 min | 21st request = 429 Too Many Requests | 429 | ✅ PASS |
| R2 | **Headers** | Check 429 Response | Header `Retry-After` exists | Present | ✅ PASS |

**Overall Status:** GO FOR LAUNCH 🚀
