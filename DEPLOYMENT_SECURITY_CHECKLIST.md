# Deployment Security Checklist

## Pre-Deployment Security Verification

### 1. **Environment Configuration** ✅
- [ ] Run `python verify_security.py` and ensure all checks pass
- [ ] Confirm no hardcoded credentials in code
- [ ] Verify `.env` file is not committed to git
- [ ] Ensure production environment variables are set

### 2. **Secret Key Generation** 🔐
For production deployment, generate new secure keys:
```bash
# Generate new JWT secret
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate new password reset secret  
python -c "import secrets; print('PASSWORD_RESET_SECRET=' + secrets.token_urlsafe(32))"
```

### 3. **Environment Variables Verification** 📋

#### Required Variables:
- [ ] `JWT_SECRET_KEY` - Strong random key (32+ chars)
- [ ] `PASSWORD_RESET_SECRET` - Different from JWT secret
- [ ] `DB_HOST` - Production database host
- [ ] `DB_NAME` - Production database name
- [ ] `DB_USER` - Production database user
- [ ] `DB_PASSWORD` - Secure database password

#### Production-Specific:
- [ ] `ENVIRONMENT=production`
- [ ] `DEBUG=false`
- [ ] `CORS_ORIGINS` - No localhost allowed
- [ ] `FRONTEND_BASE_URL` - Production frontend URL

### 4. **Security Validation Commands** 🛡️

```bash
# Verify environment loads correctly
cd /path/to/your/project
python verify_security.py

# Test application imports
python -c "from backend.user_management_api import app; print('✅ App loads successfully')"

# Check no hardcoded secrets
grep -r "change-in-production" backend/ || echo "✅ No default secrets found"

# Verify .env is in .gitignore
grep "\.env" .gitignore || echo "⚠️ Add .env to .gitignore"
```

### 5. **Database Security** 🗄️
- [ ] Use dedicated production database user
- [ ] Enable database SSL/TLS connections
- [ ] Configure proper database firewall rules
- [ ] Test database connectivity from application server

### 6. **Network Security** 🌐
- [ ] Configure proper firewall rules
- [ ] Enable HTTPS/SSL for frontend
- [ ] Restrict database access to application servers only
- [ ] Configure reverse proxy if applicable

### 7. **Application Security** 🔒
- [ ] Set strong session timeouts
- [ ] Configure appropriate CORS origins
- [ ] Enable request rate limiting
- [ ] Configure proper logging levels

### 8. **Monitoring Setup** 📊
- [ ] Configure application logs
- [ ] Set up security alerts
- [ ] Monitor failed authentication attempts
- [ ] Track configuration changes

## Post-Deployment Verification

### 1. **Functional Tests** ✅
```bash
# Test environment loading
curl -X GET http://your-api/health

# Test authentication endpoint  
curl -X POST http://your-api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'

# Verify security headers
curl -I http://your-api/
```

### 2. **Security Tests** 🔍
- [ ] Verify JWT tokens are properly signed
- [ ] Test password reset functionality
- [ ] Confirm session management works
- [ ] Check CORS configuration is effective

### 3. **Log Verification** 📝
Check application logs for:
- [ ] Environment validation success
- [ ] No configuration warnings
- [ ] Database connection success
- [ ] No security errors

## Emergency Procedures

### If Secrets Are Compromised:
1. Generate new secrets immediately
2. Update environment variables
3. Restart application
4. Invalidate all existing sessions
5. Notify users if necessary

### If Database Is Compromised:
1. Change database passwords
2. Update application configuration
3. Review audit logs
4. Reset user passwords if needed

## Maintenance

### Regular Security Tasks:
- [ ] Rotate secrets quarterly
- [ ] Review audit logs monthly
- [ ] Update dependencies regularly
- [ ] Monitor security alerts

### Security Monitoring:
- [ ] Failed login attempts
- [ ] Unusual access patterns
- [ ] Configuration changes
- [ ] Database connection errors

## Quick Commands Reference

```bash
# Verify security configuration
python verify_security.py

# Generate new secrets
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Check environment variables
env | grep -E "(JWT|DB|MAILJET)" | sed 's/=.*/=***/'

# Test application startup
python -c "from backend.user_management_api import app"

# View configuration (masked)
python -c "
from backend.user_management_api import get_secure_config_summary
import json
print(json.dumps(get_secure_config_summary(), indent=2))
"
```

## Notes

- ✅ **Green checkmarks** indicate completed/verified items
- ⚠️ **Warning symbols** indicate items needing attention  
- 🔒 **Lock symbols** indicate critical security items
- 📋 **Clipboard symbols** indicate verification checklists

**Remember:** Security is an ongoing process, not a one-time setup!
