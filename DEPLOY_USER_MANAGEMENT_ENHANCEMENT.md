# Deploy Enhanced User Management API

## 🎯 Enhancement Summary

The user management API has been enhanced with **full CRUD operations**:

### ✅ New Endpoints Added:
- `POST /users` - Create new user (admin/super_admin only)
- `PUT /users/{user_id}` - Update user information
- `DELETE /users/{user_id}` - Soft delete user (admin/super_admin only) 
- `PUT /users/{user_id}/password` - Change user password

### 🔐 Security Features:
- **Role-based permissions** - Proper access control for all operations
- **Self-service updates** - Users can update their own basic info
- **Admin restrictions** - Only super admins can modify super admin accounts
- **Session invalidation** - Automatic logout on password changes and deletions
- **Audit logging** - All actions are logged for security

### 🛡️ Validation Features:
- **Unique usernames and emails** - Prevents duplicates
- **Password verification** - Current password required for self-updates
- **Soft deletion** - Users are marked as deleted, not physically removed
- **Account protection** - Cannot delete your own account

---

## 🚀 Deployment Steps (Run on VPS)

### Step 1: SSH to VPS and Pull Updates
```bash
ssh root@staging.luckymifta.dev
cd /var/www/dash-atm
git pull origin main
```

### Step 2: Stop Current User Management API
```bash
# Find and stop the current user API process
ps aux | grep user_management
pkill -f "user_management_api.py"

# Verify it's stopped
ps aux | grep user_management
```

### Step 3: Start Enhanced User Management API
```bash
cd /var/www/dash-atm/backend

# Start the enhanced user management API
python3 user_management_api.py &

# Verify it's running on port 8001
ps aux | grep user_management
netstat -tlnp | grep :8001
```

### Step 4: Test the New Endpoints
```bash
# Test that existing endpoints still work
curl -s https://staging.luckymifta.dev/user-api/users

# Test new endpoints (will need authentication)
curl -X POST https://staging.luckymifta.dev/user-api/users
curl -X PUT https://staging.luckymifta.dev/user-api/users/test-id
curl -X DELETE https://staging.luckymifta.dev/user-api/users/test-id
curl -X PUT https://staging.luckymifta.dev/user-api/users/test-id/password
```

---

## 🧪 Testing the New Features

### 1. Test User Creation (Admin Required)
```bash
# You'll need to login first and get a token
curl -X POST https://staging.luckymifta.dev/user-api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Use the token to create a user
curl -X POST https://staging.luckymifta.dev/user-api/users \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "first_name": "Test",
    "last_name": "User",
    "role": "viewer"
  }'
```

### 2. Test Password Change
```bash
curl -X PUT https://staging.luckymifta.dev/user-api/users/USER_ID/password \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "password123",
    "new_password": "newpassword123"
  }'
```

### 3. Test User Deletion
```bash
curl -X DELETE https://staging.luckymifta.dev/user-api/users/USER_ID \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔍 Frontend Integration

The enhanced API endpoints will now work with your frontend user management features:

### ✅ Working Features:
- ✅ **Create User** - `POST /users` 
- ✅ **Update User** - `PUT /users/{user_id}`
- ✅ **Delete User** - `DELETE /users/{user_id}` 
- ✅ **Change Password** - `PUT /users/{user_id}/password`
- ✅ **List Users** - `GET /users` (existing)
- ✅ **Get User** - `GET /users/{user_id}` (existing)

### 🎯 Expected Results:
- **No more 404 errors** on user management operations
- **No more 405 Method Not Allowed** errors
- **Proper validation** and error messages
- **Security-compliant** user management
- **Audit trail** for all user operations

---

## 🔧 Quick Deployment Commands

```bash
# Single command deployment
ssh root@staging.luckymifta.dev << 'EOF'
cd /var/www/dash-atm
git pull origin main
pkill -f "user_management_api.py"
cd backend
python3 user_management_api.py &
ps aux | grep user_management
netstat -tlnp | grep :8001
echo "✅ Enhanced User Management API deployed successfully!"
EOF
```

After deployment, test the website user management features - they should now work without 404/405 errors!

## 🎉 Success Criteria
- ✅ User Management API running on port 8001
- ✅ All CRUD operations available (POST, PUT, DELETE)
- ✅ Password change functionality working
- ✅ Frontend user management features working
- ✅ No more 404/405 errors in browser network tab
