# Emergent Managed Google Auth — Integration Notes (Applied)

## Scope
- Provider: Google (Emergent-managed)
- Frontend redirect initiator: `https://auth.emergentagent.com/?redirect=<CALLBACK_URL>`
- Backend session resolver: `GET https://demobackend.emergentagent.com/auth/v1/session-data` with header `X-Session-ID`

## Implemented App Flow
1. User clicks **Google ile devam et** in login page.
2. Frontend stores selected `portal_scope` (`account` / `dealer`) in localStorage.
3. Frontend redirects to Emergent auth URL with callback: `/auth/google/callback`.
4. Callback page reads `session_id` and calls backend exchange endpoint.
5. Backend verifies session via demobackend endpoint, resolves email/profile, creates or updates user, returns local JWT tokens.
6. Frontend applies session and routes by role.

## Endpoints in this project
- `POST /api/auth/google/emergent/exchange`
  - body: `{ "session_id": "...", "portal_scope": "account|dealer" }`
  - response: existing `TokenResponse` (access_token, refresh_token, user)

## Critical Reminder
Do not change Emergent auth URL, callback format, demobackend session endpoint, or `X-Session-ID` header without re-validating the whole flow.
