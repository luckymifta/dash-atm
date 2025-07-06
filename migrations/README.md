# Database Migrations

This directory contains database migration scripts for the ATM Dashboard System.

## Migration 001: Terminal Maintenance Table

Creates the `terminal_maintenance` table as specified in PRD.md section 2.2.1.

### Files

- `001_create_terminal_maintenance.py` - Main migration script
- `test_terminal_maintenance.py` - Test script with sample data
- `migration_requirements.txt` - Python dependencies

### Prerequisites

1. Install required Python packages:
```bash
pip install -r migration_requirements.txt
```

2. Ensure your `.env` file has the correct database configuration:
```bash
DB_HOST=88.222.214.26
DB_PORT=5432
DB_NAME=development_db
DB_USER=timlesdev
DB_PASSWORD=timlesdev
```

### Running the Migration

1. **Create the table and indexes:**
```bash
python 001_create_terminal_maintenance.py
```

2. **Test the table with sample data:**
```bash
python test_terminal_maintenance.py
```

3. **Clean up test data (optional):**
```bash
python test_terminal_maintenance.py --cleanup
```

4. **Rollback migration (if needed):**
```bash
python 001_create_terminal_maintenance.py --rollback
```

### What the Migration Creates

#### Table: `terminal_maintenance`
- **Primary Key**: `id` (UUID)
- **Foreign Key**: `terminal_id` → `terminal_details.terminal_id`
- **Timestamps**: `start_datetime`, `end_datetime`, `created_at`, `updated_at`
- **Text Fields**: `problem_description`, `solution_description`
- **Enums**: `maintenance_type`, `priority`, `status`
- **JSON Field**: `images` (for file attachments)
- **Audit**: `created_by`

#### Performance Indexes
- `idx_terminal_maintenance_terminal_id` - For ATM-specific queries
- `idx_terminal_maintenance_start_datetime` - For date range queries
- `idx_terminal_maintenance_status` - For status filtering
- `idx_terminal_maintenance_created_by` - For user filtering
- `idx_terminal_maintenance_maintenance_type` - For type filtering
- `idx_terminal_maintenance_priority` - For priority filtering
- `idx_terminal_maintenance_created_at` - For chronological sorting

#### Constraints
- **Check Constraints**: Validates enum values for maintenance_type, priority, status
- **Foreign Key**: Links to terminal_details table (if exists)
- **Not Null**: Required fields enforced

#### Trigger
- **Auto-update**: `updated_at` timestamp automatically updated on record changes

### Verification

After running the migration, verify the table creation:

```sql
-- Check table structure
\d terminal_maintenance

-- Check indexes
\di terminal_maintenance*

-- Check constraints
SELECT conname, consrc FROM pg_constraint WHERE conrelid = 'terminal_maintenance'::regclass;

-- Test sample insert
INSERT INTO terminal_maintenance (
    terminal_id, start_datetime, problem_description, created_by
) VALUES (
    'TEST001', NOW(), 'Test maintenance record', 'test_user'
);
```

### Troubleshooting

#### Foreign Key Issues
If the `terminal_details` table doesn't exist, the migration will skip the foreign key constraint and log a warning. You can add it manually later:

```sql
ALTER TABLE terminal_maintenance 
ADD CONSTRAINT fk_terminal_maintenance_terminal 
FOREIGN KEY (terminal_id) REFERENCES terminal_details(terminal_id) ON DELETE CASCADE;
```

#### Permission Issues
Ensure your database user has the necessary permissions:
- CREATE TABLE
- CREATE INDEX
- CREATE FUNCTION
- CREATE TRIGGER

#### Connection Issues
Verify your database configuration and network connectivity:
```bash
# Test connection
psql -h 88.222.214.26 -p 5432 -U timlesdev -d development_db
```

### Next Steps

After successful migration:
1. Implement FastAPI endpoints (section 2.2.2 of PRD)
2. Create Pydantic models (section 2.2.3 of PRD)
3. Develop frontend components (section 2.3.2 of PRD)
4. Set up file upload system for images
5. Implement role-based access control

### Migration History

| Version | Date | Description | Status |
|---------|------|-------------|--------|
| 001 | 2025-01-30 | Create terminal_maintenance table | ✅ Ready |

---

**Note**: Always backup your database before running migrations in production!
