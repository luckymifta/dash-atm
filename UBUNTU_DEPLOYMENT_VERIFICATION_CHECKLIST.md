# ✅ Ubuntu Deployment Verification Checklist

## 📋 Pre-Deployment Verification

### ✅ Environment Setup
- [ ] SSH access to Ubuntu server working
- [ ] Located in `/var/www/dash-atm` directory
- [ ] Backup created successfully
- [ ] Git repository up to date
- [ ] Required services installed (Node.js, Python, PostgreSQL, nginx, PM2)

### ✅ Code Updates
- [ ] Latest code pulled from GitHub (`git pull origin main`)
- [ ] Password reset files present:
  - [ ] `backend/email_service.py`
  - [ ] `frontend/src/components/ForgotPasswordForm.tsx`
  - [ ] `frontend/src/components/ResetPasswordForm.tsx`
  - [ ] `frontend/src/app/auth/forgot-password/page.tsx`
  - [ ] `frontend/src/app/auth/reset-password/page.tsx`

## 🐍 Backend Verification

### ✅ Environment & Dependencies
- [ ] Virtual environment activated (`source venv/bin/activate`)
- [ ] Requirements installed (`pip install -r requirements.txt`)
- [ ] Mailjet package installed (`pip list | grep mailjet`)
- [ ] `.env.production` file exists and configured

### ✅ Environment Variables (Backend)
```bash
# Verify these are set in /var/www/dash-atm/backend/.env.production
```
- [ ] `MAILJET_API_KEY` (actual key from Mailjet dashboard)
- [ ] `MAILJET_SECRET_KEY` (actual secret from Mailjet dashboard)
- [ ] `MAILJET_FROM_EMAIL=dash@britimorleste.tl`
- [ ] `MAILJET_FROM_NAME=BRI ATM Dashboard`
- [ ] `FRONTEND_BASE_URL` (your actual domain, e.g., `https://yourdomain.com`)
- [ ] Database credentials (`DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`)

### ✅ Backend Tests
- [ ] Python imports test passed:
```bash
python3 -c "
try:
    import psycopg2
    from mailjet_rest import Client
    import secrets
    print('✅ All dependencies loaded successfully')
except ImportError as e:
    print('❌ Import error:', e)
"
```

- [ ] Database connection test passed:
```bash
python3 -c "
import os, psycopg2
from dotenv import load_dotenv
load_dotenv('.env.production')
try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=os.getenv('DB_PORT'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    print('✅ Database connection successful')
    conn.close()
except Exception as e:
    print('❌ Database connection error:', e)
"
```

- [ ] Mailjet connection test passed:
```bash
python3 -c "
import os
from dotenv import load_dotenv
from mailjet_rest import Client
load_dotenv('.env.production')
api_key = os.getenv('MAILJET_API_KEY')
api_secret = os.getenv('MAILJET_SECRET_KEY')
if not api_key or not api_secret:
    print('❌ Mailjet credentials not configured')
else:
    try:
        mailjet = Client(auth=(api_key, api_secret), version='v3.1')
        result = mailjet.send.get()
        print('✅ Mailjet connection successful')
    except Exception as e:
        print('❌ Mailjet connection error:', e)
"
```

## 🌐 Frontend Verification

### ✅ Environment & Build
- [ ] Node modules installed (`npm install`)
- [ ] `.env.production` file exists and configured
- [ ] Frontend build successful (`npm run build`)

### ✅ Environment Variables (Frontend)
```bash
# Verify these are set in /var/www/dash-atm/frontend/.env.production
```
- [ ] `NEXT_PUBLIC_API_BASE_URL` (your domain + `/api`, e.g., `https://yourdomain.com/api`)
- [ ] `NEXT_PUBLIC_API_URL` (same as above)

### ✅ Frontend Tests
- [ ] Build completed without errors
- [ ] `.next` directory created successfully
- [ ] No TypeScript or build errors in output

## 🔄 Service Deployment Verification

### ✅ PM2 Services
- [ ] All previous PM2 processes stopped (`pm2 stop all`)
- [ ] Backend service started successfully:
```bash
pm2 start "uvicorn main:app --host 0.0.0.0 --port 8000" --name "dash-atm-backend"
```
- [ ] Frontend service started successfully:
```bash
pm2 start "npm start" --name "dash-atm-frontend"
```
- [ ] PM2 configuration saved (`pm2 save`)
- [ ] All services showing as "online" in `pm2 status`

### ✅ Service Health Checks
- [ ] Backend health endpoint responds:
```bash
curl -X GET "http://localhost:8000/health"
# Expected: {"status": "healthy"} or similar
```

- [ ] Frontend responds:
```bash
curl -I http://localhost:3000
# Expected: HTTP/1.1 200 OK
```

- [ ] Backend API documentation accessible:
```bash
curl -I http://localhost:8000/docs
# Expected: HTTP/1.1 200 OK
```

## 🧪 API Endpoint Testing

### ✅ Password Reset Endpoints
- [ ] Forgot password endpoint responds:
```bash
curl -X POST "http://localhost:8000/auth/forgot-password" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'
# Expected: {"message": "If email exists, reset link sent"} or similar
```

- [ ] Reset token verification endpoint responds:
```bash
curl -X GET "http://localhost:8000/auth/verify-reset-token/test-token"
# Expected: Error response (normal for invalid token)
```

- [ ] Reset password endpoint responds:
```bash
curl -X POST "http://localhost:8000/auth/reset-password" \
  -H "Content-Type: application/json" \
  -d '{"token": "test", "new_password": "test123"}'
# Expected: Error response (normal for invalid token)
```

## 🌐 Frontend Route Testing

### ✅ Password Reset Pages
- [ ] Forgot password page accessible:
```bash
curl -I http://localhost:3000/auth/forgot-password
# Expected: HTTP/1.1 200 OK
```

- [ ] Reset password page accessible:
```bash
curl -I http://localhost:3000/auth/reset-password
# Expected: HTTP/1.1 200 OK
```

- [ ] Main login page still works:
```bash
curl -I http://localhost:3000/auth/login
# Expected: HTTP/1.1 200 OK
```

## 🔧 Nginx Verification (if applicable)

### ✅ Nginx Configuration
- [ ] Nginx configuration test passes (`sudo nginx -t`)
- [ ] Nginx service reloaded (`sudo systemctl reload nginx`)
- [ ] Nginx status is active (`sudo systemctl status nginx`)

### ✅ External Access Tests
- [ ] Frontend accessible from external URL:
```bash
curl -I https://yourdomain.com
# Expected: HTTP/1.1 200 OK
```

- [ ] API accessible from external URL:
```bash
curl -X GET "https://yourdomain.com/api/health"
# Expected: {"status": "healthy"} or similar
```

- [ ] Password reset pages accessible externally:
```bash
curl -I https://yourdomain.com/auth/forgot-password
curl -I https://yourdomain.com/auth/reset-password
# Expected: HTTP/1.1 200 OK for both
```

## 📧 Email Testing (End-to-End)

### ✅ Complete Password Reset Flow
- [ ] Navigate to `https://yourdomain.com/auth/forgot-password`
- [ ] Enter a valid email address from your system
- [ ] Submit the form
- [ ] Check that success message appears
- [ ] Check email inbox for password reset email
- [ ] Verify email contains proper reset link with your domain
- [ ] Click reset link and verify it opens reset password page
- [ ] Enter new password and submit
- [ ] Verify success message appears
- [ ] Try logging in with new password
- [ ] Verify login successful

## 📊 Log Monitoring

### ✅ Service Logs
- [ ] Backend logs show no errors:
```bash
pm2 logs dash-atm-backend --lines 10
# Look for: No ERROR level messages
```

- [ ] Frontend logs show no errors:
```bash
pm2 logs dash-atm-frontend --lines 10
# Look for: Successful startup messages
```

- [ ] Nginx logs show no errors:
```bash
sudo tail -10 /var/log/nginx/error.log
# Look for: No recent error entries
```

### ✅ System Resources
- [ ] System resources healthy:
```bash
# Check memory, CPU, disk space
free -h
df -h
htop (or top)
```

## 🎯 Final Production Verification

### ✅ User Experience Testing
- [ ] Login page loads correctly
- [ ] "Forgot Password?" link visible and clickable
- [ ] Forgot password form works properly
- [ ] Email delivery confirmed (check actual email)
- [ ] Reset link works and opens correct page
- [ ] Reset password form works properly
- [ ] New password allows successful login
- [ ] Previous password no longer works

### ✅ Security Verification
- [ ] Reset tokens expire after 24 hours (test later)
- [ ] Reset tokens are single-use (test reusing same token)
- [ ] Invalid tokens show proper error messages
- [ ] Email addresses are properly validated
- [ ] Password complexity requirements enforced

### ✅ Error Handling
- [ ] Invalid email addresses show proper errors
- [ ] Expired tokens show proper errors
- [ ] Used tokens show proper errors
- [ ] Network errors handled gracefully
- [ ] Form validation works correctly

## 📝 Deployment Documentation

### ✅ Documentation Complete
- [ ] Deployment steps documented
- [ ] Environment variables documented  
- [ ] Troubleshooting guide available
- [ ] Rollback procedure documented
- [ ] Contact information for support

### ✅ Backup & Recovery
- [ ] Backup created before deployment
- [ ] Backup location documented
- [ ] Rollback procedure tested (if needed)
- [ ] Recovery instructions available

---

## 🎉 Deployment Success Criteria

**✅ ALL ITEMS CHECKED = SUCCESSFUL DEPLOYMENT**

### Summary of Working Features:
- ✅ Backend API endpoints for password reset
- ✅ Email integration with Mailjet
- ✅ Frontend forms and pages
- ✅ Complete user flow working
- ✅ All services running stable
- ✅ External access working
- ✅ Email delivery confirmed

### Next Steps After Successful Deployment:
1. Monitor logs for first 24 hours
2. Test password reset with real users
3. Verify email deliverability across different email providers
4. Document any issues and solutions
5. Schedule regular backups

---

## 🚨 If Any Item Fails

**DO NOT PROCEED - Troubleshoot First**

1. Refer to `UBUNTU_DEPLOYMENT_TROUBLESHOOTING.md`
2. Check specific error messages in logs
3. Verify environment variables are correct
4. Test individual components in isolation
5. Consider rollback if critical issues persist

**Remember: A failed verification step now saves hours of debugging later!** 🛡️
