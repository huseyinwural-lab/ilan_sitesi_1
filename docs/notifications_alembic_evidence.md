# Alembic Evidence — Notifications

## Alembic History (local)
```
p28_email_verification_fields -> 5710cb21ddfd (head), add notifications table v1
p27_dealer_profile_slug -> p28_email_verification_fields, P28: Email verification fields for users
...
```

## Alembic Current (local)
```
FAILED: connection to server at "127.0.0.1", port 5432 failed: Connection refused
Is the server running on that host and accepting TCP/IP connections?
```

## Local DB Check
```
python /app/backend/test_db_conn.py
Connection failed: connection to server at "127.0.0.1", port 5432 failed: Connection refused
Is the server running on that host and accepting TCP/IP connections?
```

> Not: Lokal Postgres çalışmadığı için `alembic current` ve `alembic upgrade head` uygulanamadı. DB ayağa kalktığında yeniden çalıştırılmalı.
