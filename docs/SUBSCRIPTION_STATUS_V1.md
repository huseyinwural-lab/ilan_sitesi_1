# Subscription Status V1

## Status Set
- trial
- active
- past_due
- canceled

## Allowed Transitions
| From | To |
|------|----|
| trial | active, canceled |
| active | past_due, canceled |
| past_due | active, canceled |
| canceled | — |

## Payment Success Rule
- Payment succeeded → Subscription status = **active**
