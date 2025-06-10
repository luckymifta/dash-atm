#!/usr/bin/env python3
"""
ATM Dashboard Database Validation Script
Tests database connectivity and verifies required tables for user management and audit logs
"""

import psycopg2
import sys
from datetime import datetime

# Database configuration
DB_CONFIG = {
    "host": "88.222.214.26",
    "port": 5432,
    "database": "development_db",
    "user": "timlesdev",
    "password": "timlesdev",
    "sslmode": "prefer"
}

def test_connection():
    """Test database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Database connection successful")
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def check_tables(conn):
    """Check if required tables exist"""
    required_tables = [
        'users',
        'user_sessions', 
        'user_audit_log'
    ]
    
    cursor = conn.cursor()
    
    print("\n📋 Checking required tables:")
    for table in required_tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ Table '{table}' exists ({count} records)")
        except Exception as e:
            print(f"❌ Table '{table}' missing or inaccessible: {e}")
    
    cursor.close()

def create_tables_if_missing(conn):
    """Create missing tables with proper schema"""
    cursor = conn.cursor()
    
    # Users table
    users_table_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100) NOT NULL,
        phone VARCHAR(20),
        role VARCHAR(20) NOT NULL DEFAULT 'viewer' CHECK (role IN ('super_admin', 'admin', 'operator', 'viewer')),
        is_active BOOLEAN NOT NULL DEFAULT true,
        is_deleted BOOLEAN NOT NULL DEFAULT false,
        password_changed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        failed_login_attempts INTEGER NOT NULL DEFAULT 0,
        account_locked_until TIMESTAMP WITH TIME ZONE,
        last_login_at TIMESTAMP WITH TIME ZONE,
        last_login_ip INET,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        created_by UUID
    );
    """
    
    # User sessions table
    sessions_table_sql = """
    CREATE TABLE IF NOT EXISTS user_sessions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID NOT NULL,
        session_token TEXT NOT NULL UNIQUE,
        refresh_token TEXT NOT NULL UNIQUE,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT true,
        ip_address INET,
        user_agent TEXT,
        remember_me BOOLEAN NOT NULL DEFAULT false,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        last_accessed_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    """
    
    # Audit log table
    audit_table_sql = """
    CREATE TABLE IF NOT EXISTS user_audit_log (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        user_id UUID,
        action VARCHAR(50) NOT NULL,
        entity_type VARCHAR(50) NOT NULL DEFAULT 'user',
        entity_id UUID,
        old_values JSONB,
        new_values JSONB,
        ip_address INET,
        user_agent TEXT,
        performed_by UUID,
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (performed_by) REFERENCES users(id) ON DELETE SET NULL
    );
    """
    
    # Create indexes
    indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);",
        "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);",
        "CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active, is_deleted);",
        "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_sessions_token ON user_sessions(session_token);",
        "CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active, expires_at);",
        "CREATE INDEX IF NOT EXISTS idx_audit_user_id ON user_audit_log(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_audit_action ON user_audit_log(action);",
        "CREATE INDEX IF NOT EXISTS idx_audit_created ON user_audit_log(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_audit_performed_by ON user_audit_log(performed_by);"
    ]
    
    try:
        print("\n🔨 Creating tables if missing...")
        cursor.execute(users_table_sql)
        print("✅ Users table ready")
        
        cursor.execute(sessions_table_sql)
        print("✅ User sessions table ready")
        
        cursor.execute(audit_table_sql)
        print("✅ Audit log table ready")
        
        print("\n📊 Creating indexes...")
        for index_sql in indexes_sql:
            cursor.execute(index_sql)
        print("✅ All indexes created")
        
        conn.commit()
        print("✅ Database schema ready for production")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        conn.rollback()
    
    cursor.close()

def test_basic_operations(conn):
    """Test basic database operations"""
    cursor = conn.cursor()
    
    try:
        print("\n🧪 Testing basic operations...")
        
        # Test insert (if no users exist)
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'super_admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            print("📝 Creating default admin user...")
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, first_name, last_name, role)
                VALUES ('admin', 'admin@atm-dashboard.com', '$2b$12$placeholder', 'System', 'Administrator', 'super_admin')
                ON CONFLICT (username) DO NOTHING
            """)
            conn.commit()
            print("✅ Default admin user created")
        else:
            print(f"✅ Found {admin_count} admin user(s)")
        
        # Test audit log insert
        cursor.execute("""
            INSERT INTO user_audit_log (action, entity_type, new_values)
            VALUES ('database_validation', 'system', '{"test": true, "timestamp": "%s"}')
        """ % datetime.now().isoformat())
        
        conn.commit()
        print("✅ Audit log test successful")
        
    except Exception as e:
        print(f"❌ Error testing operations: {e}")
        conn.rollback()
    
    cursor.close()

def main():
    """Main validation function"""
    print("🚀 ATM Dashboard Database Validation")
    print("=" * 50)
    
    # Test connection
    conn = test_connection()
    if not conn:
        sys.exit(1)
    
    try:
        # Check existing tables
        check_tables(conn)
        
        # Create missing tables
        create_tables_if_missing(conn)
        
        # Test operations
        test_basic_operations(conn)
        
        print("\n" + "=" * 50)
        print("✅ Database validation completed successfully!")
        print("\n📋 Next steps:")
        print("1. Update SECRET_KEY in .env file")
        print("2. Change default admin password")
        print("3. Start the user management API")
        print("4. Test login functionality")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        sys.exit(1)
    
    finally:
        conn.close()

if __name__ == "__main__":
    main()
