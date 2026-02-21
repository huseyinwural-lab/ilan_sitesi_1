# Invoices V1 Evidence

## Migration
- Migration: `d827659f4150_invoices_v1_schema.py`
- Alembic current:
```
d2f4c9c4c7ab (head)
d827659f4150 (head)
aa12b9c8d7e1 (head)
f3b1c2d8a91b (head)
```

## Simulation (create → issue → paid)
- Create invoice (issued): OK
- Mark paid: OK
- Status: `issued` → `paid`
- Payment status: `requires_payment_method` → `succeeded`

## Admin list
- `GET /api/admin/invoices?status=paid` → PASS

## Index / EXPLAIN
```
EXPLAIN SELECT * FROM admin_invoices WHERE user_id='02020c1e-afa4-4e6b-9c06-69532f632400' ORDER BY created_at DESC LIMIT 10;
Index Scan using ix_admin_invoices_user on admin_invoices

EXPLAIN SELECT * FROM admin_invoices WHERE status='paid' ORDER BY created_at DESC LIMIT 10;
Index Scan using ix_admin_invoices_status on admin_invoices
```
