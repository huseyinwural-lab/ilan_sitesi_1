# InvoiceStatus State Machine (V1)

## Status Set
- draft
- issued
- paid
- void
- refunded

## Allowed Transitions
| From | To |
|------|----|
| draft | issued, void |
| issued | paid, void |
| paid | refunded |
| void | — |
| refunded | — |

## Notes
- `issued_at` **required** for issued/paid.
- `due_at` optional for issued (null => immediate due).
