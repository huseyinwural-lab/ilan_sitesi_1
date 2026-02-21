# Alembic Evidence — Notifications

## Alembic Upgrade
- `alembic upgrade heads` başarıyla uygulandı.

## Alembic Current (local)
```
d2f4c9c4c7ab (head)
5710cb21ddfd (head)
f3b1c2d8a91b (head)
aa12b9c8d7e1 (head)
```

## Local DB Check
```
psql postgresql://admin_user:admin_pass@localhost:5432/admin_panel -c "SELECT 1"
?column?
----------
        1
(1 row)
```
