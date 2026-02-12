# Seed Cleanup Procedure

**Scenario:** Resetting Staging for fresh test.

## 1. Automated Cleanup
Run the seed script with clean flag:
```bash
python scripts/seed_dummy_users.py --clean
```
*Effect:* Deletes `listings`, `dealer_subscriptions`, `dealers`, `dealer_applications`, `users` (where email like `user_%@example.com`).

## 2. Manual SQL
```sql
DELETE FROM listings WHERE title LIKE '%Test%';
DELETE FROM dealers WHERE company_name LIKE '%Test%';
DELETE FROM users WHERE email LIKE '%example.com%';
```
