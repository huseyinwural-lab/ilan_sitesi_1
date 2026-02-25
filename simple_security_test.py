#!/usr/bin/env python3

import requests
import time
import json

# Read base URL from frontend/.env
try:
    with open('/app/frontend/.env', 'r') as f:
        for line in f:
            if line.startswith('REACT_APP_BACKEND_URL='):
                base_url = line.split('=', 1)[1].strip()
                break
        else:
            base_url = "https://monetize-listings.preview.emergentagent.com"
except FileNotFoundError:
    base_url = "https://monetize-listings.preview.emergentagent.com"

api_url = f"{base_url}/api"

print(f"🚀 FAZ-FINAL-02 Security Audit Test")
print(f"Base URL: {base_url}")
print("=" * 60)

# 1. Login as admin
print("\n🔐 Step 1: Admin Login")
response = requests.post(f"{api_url}/auth/login", json={
    'email': 'admin@platform.com',
    'password': 'Admin123!'
})

if response.status_code == 200:
    admin_data = response.json()
    admin_token = admin_data['access_token']
    print(f"✅ Admin login successful: {admin_data['user']['full_name']}")
else:
    print(f"❌ Admin login failed: {response.status_code}")
    exit(1)

# 2. Test failed login attempts
print("\n🔍 Step 2: Failed Login Audit Test")
print("Testing 3 failed login attempts...")

failed_count = 0
for i in range(3):
    print(f"  Attempt {i+1}: Wrong password")
    response = requests.post(f"{api_url}/auth/login", json={
        'email': 'admin@platform.com',
        'password': 'WrongPassword123!'
    })
    
    print(f"    Status: {response.status_code}")
    if response.status_code == 401:
        failed_count += 1
        print(f"    ✅ Got 401 as expected")
    else:
        print(f"    ❌ Expected 401, got {response.status_code}")

print(f"\nFailed attempts recorded: {failed_count}/3")

# Test 4th attempt (should be rate limited)
print(f"\n  Attempt 4: Should be rate limited")
response = requests.post(f"{api_url}/auth/login", json={
    'email': 'admin@platform.com',
    'password': 'WrongPassword123!'
})

print(f"    Status: {response.status_code}")
if response.status_code == 429:
    print(f"    ✅ Got 429 (rate limited) as expected")
    rate_limited = True
elif response.status_code == 401:
    print(f"    ⚠️  Got 401 instead of 429 - rate limiting may need different timing")
    rate_limited = False
else:
    print(f"    ❌ Unexpected status: {response.status_code}")
    rate_limited = False

# 3. Check audit logs
print("\n🔍 Step 3: Audit Log Verification")

headers = {'Authorization': f'Bearer {admin_token}'}

# Check FAILED_LOGIN entries
print("Checking FAILED_LOGIN audit entries...")
response = requests.get(f"{api_url}/audit-logs", 
                       params={'event_type': 'FAILED_LOGIN', 'limit': 10},
                       headers=headers)

if response.status_code == 200:
    failed_login_logs = response.json()
    print(f"  Found {len(failed_login_logs)} FAILED_LOGIN entries")
    
    if failed_login_logs:
        sample = failed_login_logs[0]
        required_fields = ['event_type', 'email', 'ip_address', 'user_agent', 'created_at']
        missing = [f for f in required_fields if f not in sample]
        if missing:
            print(f"  ⚠️  Missing fields: {missing}")
        else:
            print(f"  ✅ Audit log structure is correct")
else:
    print(f"  ❌ Failed to get audit logs: {response.status_code}")

# Check RATE_LIMIT_BLOCK entries
print("Checking RATE_LIMIT_BLOCK audit entries...")
response = requests.get(f"{api_url}/audit-logs", 
                       params={'event_type': 'RATE_LIMIT_BLOCK', 'limit': 5},
                       headers=headers)

if response.status_code == 200:
    rate_limit_logs = response.json()
    print(f"  Found {len(rate_limit_logs)} RATE_LIMIT_BLOCK entries")
else:
    print(f"  ❌ Failed to get rate limit audit logs: {response.status_code}")

# 4. Test role change audit
print("\n🔍 Step 4: Role Change Audit Test")

# Get users
response = requests.get(f"{api_url}/users", params={'limit': 10}, headers=headers)
if response.status_code == 200:
    users = response.json()
    target_user = None
    
    for user in users:
        if user.get('role') != 'super_admin' and user.get('email') != 'admin@platform.com':
            target_user = user
            break
    
    if target_user:
        user_id = target_user['id']
        original_role = target_user['role']
        new_role = 'support' if original_role != 'support' else 'moderator'
        
        print(f"  Changing role for {target_user['email']}: {original_role} → {new_role}")
        
        # Change role
        response = requests.patch(f"{api_url}/users/{user_id}", 
                                json={'role': new_role}, 
                                headers=headers)
        
        if response.status_code == 200:
            print(f"  ✅ Role change successful")
            
            # Check audit log
            time.sleep(1)
            response = requests.get(f"{api_url}/audit-logs", 
                                  params={'event_type': 'ADMIN_ROLE_CHANGE', 'limit': 5},
                                  headers=headers)
            
            if response.status_code == 200:
                role_change_logs = response.json()
                matching_logs = [log for log in role_change_logs if log.get('target_user_id') == user_id]
                
                if matching_logs:
                    audit_entry = matching_logs[0]
                    print(f"  ✅ Found ADMIN_ROLE_CHANGE audit entry")
                    print(f"    Previous role: {audit_entry.get('previous_role')}")
                    print(f"    New role: {audit_entry.get('new_role')}")
                    print(f"    Applied: {audit_entry.get('applied')}")
                else:
                    print(f"  ❌ No matching audit entry found")
            else:
                print(f"  ❌ Failed to get role change audit logs: {response.status_code}")
        else:
            print(f"  ❌ Role change failed: {response.status_code}")
    else:
        print(f"  ⚠️  No suitable user found for role change test")
else:
    print(f"  ❌ Failed to get users: {response.status_code}")

# 5. Test audit log filtering
print("\n🔍 Step 5: Audit Log Filtering Test")

response = requests.get(f"{api_url}/audit-logs", 
                       params={'event_type': 'ADMIN_ROLE_CHANGE', 'limit': 5},
                       headers=headers)

if response.status_code == 200:
    filtered_logs = response.json()
    wrong_type_logs = [log for log in filtered_logs if log.get('event_type') != 'ADMIN_ROLE_CHANGE']
    
    if wrong_type_logs:
        print(f"  ❌ Found {len(wrong_type_logs)} entries with wrong event_type")
    else:
        print(f"  ✅ Filtering works correctly, returned {len(filtered_logs)} ADMIN_ROLE_CHANGE entries")
else:
    print(f"  ❌ Failed to test filtering: {response.status_code}")

# 6. Test moderation taxonomy
print("\n🔍 Step 6: Moderation Taxonomy Sanity Check")

response = requests.get(f"{api_url}/audit-logs", params={'limit': 50}, headers=headers)

if response.status_code == 200:
    all_logs = response.json()
    moderation_logs = [log for log in all_logs if log.get('event_type', '').startswith('MODERATION_')]
    
    if not moderation_logs:
        print(f"  ℹ️  No moderation audit entries found (acceptable)")
    else:
        print(f"  Found {len(moderation_logs)} moderation audit entries")
        
        valid_event_types = {'MODERATION_APPROVE', 'MODERATION_REJECT', 'MODERATION_NEEDS_REVISION'}
        valid_actions = {'APPROVE', 'REJECT', 'NEEDS_REVISION'}
        
        invalid_count = 0
        for log in moderation_logs:
            event_type = log.get('event_type')
            action = log.get('action')
            
            if event_type not in valid_event_types:
                print(f"    ⚠️  Invalid event_type: {event_type}")
                invalid_count += 1
            
            if action not in valid_actions:
                print(f"    ⚠️  Invalid action: {action}")
                invalid_count += 1
        
        if invalid_count == 0:
            print(f"  ✅ All moderation entries follow correct taxonomy")
        else:
            print(f"  ❌ Found {invalid_count} taxonomy violations")
else:
    print(f"  ❌ Failed to get audit logs for taxonomy check: {response.status_code}")

print("\n" + "=" * 60)
print("🎉 FAZ-FINAL-02 Security Audit Test Complete!")