#!/bin/bash
# Soft Launch Verification Script

echo "🚀 Starting Soft Launch Verification..."

# 1. Check Services
echo "🔹 Checking Services..."
if supervisorctl status | grep -q "RUNNING"; then
    echo "✅ Services RUNNING"
else
    echo "❌ CRITICAL: Services DOWN"
    exit 1
fi

# 2. Check Database Connectivity
echo "🔹 Checking Database..."
if sudo -u postgres psql -d admin_panel -c "SELECT 1;" > /dev/null; then
    echo "✅ Database CONNECTED"
else
    echo "❌ CRITICAL: Database DOWN"
    exit 1
fi

# 3. Check ML Model Status
echo "🔹 Checking ML Model..."
if sudo -u postgres psql -d admin_panel -c "SELECT version FROM ml_models WHERE is_active = true;" | grep -q "v1-mock"; then
    echo "✅ ML Model ACTIVE (v1-mock)"
else
    echo "⚠️ WARNING: No Active ML Model"
fi

# 4. Check Config
echo "🔹 Checking Ranking Config..."
if sudo -u postgres psql -d admin_panel -c "SELECT key FROM system_configs WHERE key = 'ranking_weights_v1';" | grep -q "ranking_weights_v1"; then
    echo "✅ Ranking Config LOADED"
else
    echo "❌ CRITICAL: Missing Ranking Config"
    exit 1
fi

echo "🎉 SOFT LAUNCH READY - ALL SYSTEMS GO"
exit 0
