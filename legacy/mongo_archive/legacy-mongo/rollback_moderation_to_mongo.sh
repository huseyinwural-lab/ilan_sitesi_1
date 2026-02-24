#!/usr/bin/env bash
set -e

echo "Rollback: Mongo read fallback (Moderation)"
echo "1) pymongo yeniden eklenmeli: pip install pymongo"
echo "2) backend/.env içinde MONGO_URL ve DB_NAME doğrulanmalı"
echo "3) Gerekirse legacy moderation scriptleri archive/legacy-mongo altından geri taşınmalı"
echo "4) Backend restart: sudo supervisorctl restart backend"
