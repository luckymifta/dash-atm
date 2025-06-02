#!/usr/bin/env python3
"""
Database setup script for User Management System
Creates the necessary tables for users, sessions, and audit logging
"""

import sqlite3
import os
from datetime import datetime
import uuid
import bcrypt

# Database configuration
DATABASE_TYPE = "sqlite"  # Change to "postgresql" if using PostgreSQL
SQLITE_DB_PATH = "/Users/luckymifta/Documents/2. AREA/dash-atm/backend/user_management.db"

def create_sqlite_tables():
    """Create tables in SQLite database"""
    print("Setting up SQLite database...")
    
    # Remove existing database file if it exists
    if os.path.exists(SQLITE_DB_PATH):
        os.remove(SQLITE_DB_PATH)
        print(f"Removed existing database: {SQLITE_DB_PATH}")
    
    # Create new database
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            
            -- Password Management
            password_hash VARCHAR(255) NOT NULL,
            password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            failed_login_attempts INTEGER DEFAULT 0,
            account_locked_until TIMESTAMP NULL,
            
            -- Profile Information
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            
            -- Role & Permissions
            role VARCHAR(20) DEFAULT 'viewer' CHECK (role IN ('super_admin', 'admin', 'operator', 'viewer')),
            
            -- Account Status
            is_active BOOLEAN DEFAULT TRUE,
            is_deleted BOOLEAN DEFAULT FALSE,
            
            -- Audit Fields
            last_login_at TIMESTAMP,
            last_login_ip TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by TEXT REFERENCES users(id),
            updated_by TEXT REFERENCES users(id)
        )
    """)
    
    # Create user_sessions table
    cursor.execute("""
        CREATE TABLE user_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            session_token VARCHAR(255) UNIQUE NOT NULL,
            refresh_token VARCHAR(255) UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT,
            is_active BOOLEAN DEFAULT TRUE
        )
    """)
    
    # Create user_audit_log table
    cursor.execute("""
        CREATE TABLE user_audit_log (
            id TEXT PRIMARY KEY,
            user_id TEXT REFERENCES users(id),
            action VARCHAR(100) NOT NULL,
            entity_type VARCHAR(50) NOT NULL,
            entity_id TEXT,
            old_values TEXT, -- JSON string
            new_values TEXT, -- JSON string
            ip_address TEXT,
            user_agent TEXT,
            performed_by TEXT REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_users_username ON users(username)")
    cursor.execute("CREATE INDEX idx_users_email ON users(email)")
    cursor.execute("CREATE INDEX idx_user_sessions_token ON user_sessions(session_token)")
    cursor.execute("CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id)")
    cursor.execute("CREATE INDEX idx_audit_log_user_id ON user_audit_log(user_id)")
    cursor.execute("CREATE INDEX idx_audit_log_action ON user_audit_log(action)")
    cursor.execute("CREATE INDEX idx_audit_log_created_at ON user_audit_log(created_at)")
    
    conn.commit()
    print("✅ SQLite tables created successfully!")
    
    # Create default admin user
    create_default_admin_user(cursor, conn)
    
    conn.close()

def create_default_admin_user(cursor, conn):
    """Create default admin user for SQLite"""
    admin_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    # Hash the default password
    password = "admin123"
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    cursor.execute("""
        INSERT INTO users (
            id, username, email, password_hash, first_name, last_name,
            role, is_active, is_deleted, password_changed_at, failed_login_attempts,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        admin_id,
        "admin",
        "admin@atm-dashboard.com",
        password_hash,
        "System",
        "Administrator",
        "super_admin",
        True,
        False,
        now,
        0,
        now,
        now
    ))
    
    conn.commit()
    print("✅ Default admin user created:")
    print("   Username: admin")
    print("   Password: admin123")
    print("   ⚠️  Please change the password after first login!")

def test_database_connection():
    """Test database connection and show tables"""
    if os.path.exists(SQLITE_DB_PATH):
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        
        # Show tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("\n📋 Created tables:")
        for table in tables:
            print(f"   - {table[0]}")
        
        # Show admin user
        cursor.execute("SELECT username, email, role FROM users WHERE username = 'admin'")
        admin = cursor.fetchone()
        if admin:
            print(f"\n👤 Admin user: {admin[0]} ({admin[1]}) - Role: {admin[2]}")
        
        conn.close()
    else:
        print("❌ Database file not found!")

def main():
    print("🚀 Setting up User Management Database")
    print("=" * 50)
    
    create_sqlite_tables()
    
    print("\n🔍 Testing database connection...")
    test_database_connection()
    
    print("\n✅ Database setup completed!")
    print("\n📝 Next steps:")
    print("1. Run the user management API: python user_management_api.py")
    print("2. Test the API endpoints")
    print("3. Change the default admin password after first login")

if __name__ == "__main__":
    main()
