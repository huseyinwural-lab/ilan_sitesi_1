# DB Connection Evidence

## DATABASE_URL (local)
`postgresql://admin_user:admin_pass@localhost:5432/admin_panel`

## Postgres Status
- Service: `postgresql` (15/main) **online**

## psql Connection Test
```
psql postgresql://admin_user:admin_pass@localhost:5432/admin_panel -c "SELECT 1"
?column?
----------
        1
(1 row)
```
