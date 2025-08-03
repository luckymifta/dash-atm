#!/usr/bin/env python3
"""
Security Configuration Verification Script
Verifies that all security-related environment variables are properly configured
"""

import os
import sys
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env file"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, 'backend', '.env')
    
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✓ Loaded environment from: {env_path}")
    else:
        print(f"⚠️  No .env file found at: {env_path}")
        return False
    return True

def check_required_variables():
    """Check if all required environment variables are set"""
    required_vars = [
        'JWT_SECRET_KEY',
        'PASSWORD_RESET_SECRET',
        'DB_HOST',
        'DB_NAME',
        'DB_USER',
        'DB_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✓ All required environment variables are set")
        return True

def check_security_configuration():
    """Check security-related configurations"""
    issues = []
    warnings = []
    
    # Check environment setting
    environment = os.getenv('ENVIRONMENT', 'development').lower()
    print(f"📊 Environment: {environment}")
    
    # Check JWT secret key
    jwt_secret = os.getenv('JWT_SECRET_KEY', '')
    if len(jwt_secret) < 32:
        if environment == 'production':
            issues.append("JWT_SECRET_KEY must be at least 32 characters in production")
        else:
            warnings.append("JWT_SECRET_KEY should be at least 32 characters")
    
    if 'change-in-production' in jwt_secret.lower():
        if environment == 'production':
            issues.append("Default JWT_SECRET_KEY detected in production")
        else:
            warnings.append("Using default JWT_SECRET_KEY (change for production)")
    
    # Check password reset secret
    reset_secret = os.getenv('PASSWORD_RESET_SECRET', '')
    if len(reset_secret) < 32:
        if environment == 'production':
            issues.append("PASSWORD_RESET_SECRET must be at least 32 characters in production")
        else:
            warnings.append("PASSWORD_RESET_SECRET should be at least 32 characters")
    
    if 'change-in-production' in reset_secret.lower():
        if environment == 'production':
            issues.append("Default PASSWORD_RESET_SECRET detected in production")
        else:
            warnings.append("Using default PASSWORD_RESET_SECRET (change for production)")
    
    # Check if secrets are the same
    if jwt_secret == reset_secret and jwt_secret:
        issues.append("JWT_SECRET_KEY and PASSWORD_RESET_SECRET should be different")
    
    # Check CORS configuration
    cors_origins = os.getenv('CORS_ORIGINS', '').split(',')
    if environment == 'production' and 'http://localhost:3000' in cors_origins:
        warnings.append("localhost is allowed in CORS origins in production")
    
    # Check frontend URL
    frontend_url = os.getenv('FRONTEND_BASE_URL', '')
    if environment == 'production' and 'localhost' in frontend_url:
        warnings.append("Frontend URL contains localhost in production")
    
    return issues, warnings

def check_database_configuration():
    """Check database configuration"""
    db_config = {
        'host': os.getenv('DB_HOST'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME'),
        'user': os.getenv('DB_USER'),
    }
    
    print("📊 Database Configuration:")
    print(f"   Host: {db_config['host']}")
    print(f"   Port: {db_config['port']}")
    print(f"   Database: {db_config['database']}")
    print(f"   User: {db_config['user']}")
    print(f"   Password: {'*' * len(os.getenv('DB_PASSWORD', ''))}")

def check_email_configuration():
    """Check email configuration"""
    email_vars = ['MAILJET_API_KEY', 'MAILJET_SECRET_KEY', 'MAILJET_FROM_EMAIL']
    email_config = {}
    
    for var in email_vars:
        value = os.getenv(var, '')
        email_config[var] = value
    
    print("📊 Email Configuration:")
    for var, value in email_config.items():
        if value:
            if 'KEY' in var:
                print(f"   {var}: {'*' * 20}")
            else:
                print(f"   {var}: {value}")
        else:
            print(f"   {var}: Not set")

def generate_secure_keys():
    """Generate secure keys for configuration"""
    import secrets
    
    print("\n🔐 Generated Secure Keys (use these in your .env file):")
    print(f"JWT_SECRET_KEY={secrets.token_urlsafe(32)}")
    print(f"PASSWORD_RESET_SECRET={secrets.token_urlsafe(32)}")

def main():
    """Main verification function"""
    print("🔒 Security Configuration Verification")
    print("=" * 50)
    
    # Load environment
    if not load_environment():
        sys.exit(1)
    
    print()
    
    # Check required variables
    if not check_required_variables():
        print("\n❌ Configuration check failed!")
        sys.exit(1)
    
    print()
    
    # Check security configuration
    issues, warnings = check_security_configuration()
    
    # Display database configuration
    print()
    check_database_configuration()
    
    # Display email configuration
    print()
    check_email_configuration()
    
    # Display results
    print("\n" + "=" * 50)
    print("🔍 Security Verification Results:")
    
    if issues:
        print(f"\n❌ Critical Issues Found ({len(issues)}):")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    
    if warnings:
        print(f"\n⚠️  Warnings ({len(warnings)}):")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")
    
    if not issues and not warnings:
        print("\n✅ All security checks passed!")
    
    # Generate new keys if needed
    if issues or warnings:
        print()
        generate_secure_keys()
    
    # Exit with appropriate code
    if issues:
        print(f"\n❌ Security verification failed with {len(issues)} critical issues!")
        sys.exit(1)
    elif warnings:
        print(f"\n⚠️  Security verification completed with {len(warnings)} warnings")
        sys.exit(0)
    else:
        print("\n✅ Security verification completed successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()
