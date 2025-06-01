#!/usr/bin/env python3
"""
Regional ATM Database Cleanup Script

This script provides various options to clean up the regional_atm_counts database table:
- Delete all records
- Delete records older than specified time
- Delete duplicate records (keep latest per region)
- Delete specific regions
- View records before deletion

Usage:
    python clean_regional_database.py [--action ACTION] [--region REGION] [--hours HOURS] [--confirm]
"""

import argparse
import sys
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(funcName)s]: %(message)s",
    handlers=[
        logging.FileHandler("database_cleanup.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger("DatabaseCleanup")

# Try to import database connector
try:
    import db_connector
    DB_AVAILABLE = True
    log.info("Database connector available")
except ImportError:
    DB_AVAILABLE = False
    log.error("Database connector not available")
    sys.exit(1)

class RegionalDatabaseCleaner:
    """Class for managing regional ATM database cleanup operations"""
    
    def __init__(self):
        """Initialize the cleaner"""
        self.conn = None
        log.info("Initialized RegionalDatabaseCleaner")
    
    def get_connection(self):
        """Get database connection"""
        if not self.conn:
            self.conn = db_connector.get_db_connection()
        return self.conn
    
    def close_connection(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def view_current_records(self) -> Dict[str, Any]:
        """View current records in the database"""
        conn = self.get_connection()
        if not conn:
            log.error("Cannot connect to database")
            return {}
        
        cursor = conn.cursor()
        try:
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM regional_atm_counts")
            total_count = cursor.fetchone()[0]
            
            # Get breakdown by region
            cursor.execute("""
                SELECT region_code, COUNT(*) as count, 
                       MIN(date_creation) as oldest, 
                       MAX(date_creation) as newest
                FROM regional_atm_counts 
                GROUP BY region_code 
                ORDER BY region_code
            """)
            
            region_breakdown = cursor.fetchall()
            
            # Get recent records
            cursor.execute("""
                SELECT unique_request_id, region_code, date_creation, 
                       count_available, count_warning, count_zombie, 
                       count_wounded, count_out_of_service, total_atms_in_region
                FROM regional_atm_counts 
                ORDER BY date_creation DESC 
                LIMIT 10
            """)
            
            recent_records = cursor.fetchall()
            
            # Get oldest records
            cursor.execute("""
                SELECT unique_request_id, region_code, date_creation, 
                       count_available, count_warning, count_zombie, 
                       count_wounded, count_out_of_service, total_atms_in_region
                FROM regional_atm_counts 
                ORDER BY date_creation ASC 
                LIMIT 10
            """)
            
            oldest_records = cursor.fetchall()
            
            return {
                'total_count': total_count,
                'region_breakdown': region_breakdown,
                'recent_records': recent_records,
                'oldest_records': oldest_records
            }
            
        except Exception as e:
            log.error(f"Error viewing records: {str(e)}")
            return {}
        finally:
            cursor.close()
    
    def delete_all_records(self, confirm: bool = False) -> bool:
        """Delete all records from regional_atm_counts table"""
        if not confirm:
            log.warning("Delete all operation requires --confirm flag")
            return False
        
        conn = self.get_connection()
        if not conn:
            log.error("Cannot connect to database")
            return False
        
        cursor = conn.cursor()
        try:
            # First get count
            cursor.execute("SELECT COUNT(*) FROM regional_atm_counts")
            count_before = cursor.fetchone()[0]
            
            log.info(f"Deleting all {count_before} records from regional_atm_counts table...")
            
            cursor.execute("DELETE FROM regional_atm_counts")
            conn.commit()
            
            # Verify deletion
            cursor.execute("SELECT COUNT(*) FROM regional_atm_counts")
            count_after = cursor.fetchone()[0]
            
            log.info(f"Successfully deleted {count_before - count_after} records")
            log.info(f"Records remaining: {count_after}")
            
            return True
            
        except Exception as e:
            conn.rollback()
            log.error(f"Error deleting all records: {str(e)}")
            return False
        finally:
            cursor.close()
    
    def delete_old_records(self, hours_old: int, confirm: bool = False) -> bool:
        """Delete records older than specified hours"""
        if not confirm:
            log.warning("Delete old records operation requires --confirm flag")
            return False
        
        conn = self.get_connection()
        if not conn:
            log.error("Cannot connect to database")
            return False
        
        cursor = conn.cursor()
        try:
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
            
            # First count what will be deleted
            cursor.execute("""
                SELECT COUNT(*) FROM regional_atm_counts 
                WHERE date_creation < %s
            """, (cutoff_time,))
            count_to_delete = cursor.fetchone()[0]
            
            if count_to_delete == 0:
                log.info(f"No records older than {hours_old} hours found")
                return True
            
            log.info(f"Deleting {count_to_delete} records older than {hours_old} hours (before {cutoff_time})...")
            
            cursor.execute("""
                DELETE FROM regional_atm_counts 
                WHERE date_creation < %s
            """, (cutoff_time,))
            
            conn.commit()
            
            log.info(f"Successfully deleted {count_to_delete} old records")
            
            return True
            
        except Exception as e:
            conn.rollback()
            log.error(f"Error deleting old records: {str(e)}")
            return False
        finally:
            cursor.close()
    
    def delete_duplicates(self, confirm: bool = False) -> bool:
        """Delete duplicate records, keeping only the latest per region"""
        if not confirm:
            log.warning("Delete duplicates operation requires --confirm flag")
            return False
        
        conn = self.get_connection()
        if not conn:
            log.error("Cannot connect to database")
            return False
        
        cursor = conn.cursor()
        try:
            # First count duplicates
            cursor.execute("""
                WITH ranked_records AS (
                    SELECT unique_request_id,
                           ROW_NUMBER() OVER (PARTITION BY region_code ORDER BY date_creation DESC) as rn
                    FROM regional_atm_counts
                )
                SELECT COUNT(*) FROM ranked_records WHERE rn > 1
            """)
            
            duplicate_count = cursor.fetchone()[0]
            
            if duplicate_count == 0:
                log.info("No duplicate records found")
                return True
            
            log.info(f"Deleting {duplicate_count} duplicate records (keeping latest per region)...")
            
            # Delete duplicates
            cursor.execute("""
                DELETE FROM regional_atm_counts 
                WHERE unique_request_id IN (
                    SELECT unique_request_id FROM (
                        SELECT unique_request_id,
                               ROW_NUMBER() OVER (PARTITION BY region_code ORDER BY date_creation DESC) as rn
                        FROM regional_atm_counts
                    ) ranked 
                    WHERE rn > 1
                )
            """)
            
            conn.commit()
            
            log.info(f"Successfully deleted {duplicate_count} duplicate records")
            
            return True
            
        except Exception as e:
            conn.rollback()
            log.error(f"Error deleting duplicates: {str(e)}")
            return False
        finally:
            cursor.close()
    
    def delete_region_records(self, region_code: str, confirm: bool = False) -> bool:
        """Delete all records for a specific region"""
        if not confirm:
            log.warning("Delete region records operation requires --confirm flag")
            return False
        
        conn = self.get_connection()
        if not conn:
            log.error("Cannot connect to database")
            return False
        
        cursor = conn.cursor()
        try:
            # First count records for this region
            cursor.execute("""
                SELECT COUNT(*) FROM regional_atm_counts 
                WHERE region_code = %s
            """, (region_code,))
            
            count_to_delete = cursor.fetchone()[0]
            
            if count_to_delete == 0:
                log.info(f"No records found for region {region_code}")
                return True
            
            log.info(f"Deleting {count_to_delete} records for region {region_code}...")
            
            cursor.execute("""
                DELETE FROM regional_atm_counts 
                WHERE region_code = %s
            """, (region_code,))
            
            conn.commit()
            
            log.info(f"Successfully deleted {count_to_delete} records for region {region_code}")
            
            return True
            
        except Exception as e:
            conn.rollback()
            log.error(f"Error deleting region records: {str(e)}")
            return False
        finally:
            cursor.close()
    
    def backup_before_cleanup(self) -> bool:
        """Create a backup of current data before cleanup"""
        conn = self.get_connection()
        if not conn:
            log.error("Cannot connect to database")
            return False
        
        cursor = conn.cursor()
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"regional_atm_backup_{timestamp}.sql"
            
            log.info(f"Creating backup: {backup_filename}")
            
            # This is a simple approach - in production, use pg_dump
            cursor.execute("SELECT * FROM regional_atm_counts ORDER BY date_creation")
            records = cursor.fetchall()
            
            with open(backup_filename, 'w') as f:
                f.write("-- Regional ATM Counts Backup\n")
                f.write(f"-- Created: {datetime.now()}\n")
                f.write(f"-- Total records: {len(records)}\n\n")
                
                for record in records:
                    f.write(f"INSERT INTO regional_atm_counts VALUES {record};\n")
            
            log.info(f"Backup created successfully: {backup_filename}")
            return True
            
        except Exception as e:
            log.error(f"Error creating backup: {str(e)}")
            return False
        finally:
            cursor.close()

def display_records_summary(data: Dict[str, Any]):
    """Display a summary of current records"""
    if not data:
        print("No data available")
        return
    
    print("\n" + "=" * 80)
    print("CURRENT REGIONAL_ATM_COUNTS DATABASE STATUS")
    print("=" * 80)
    
    total_count = data.get('total_count', 0)
    print(f"Total records: {total_count}")
    
    if total_count == 0:
        print("Database is empty")
        return
    
    # Region breakdown
    region_breakdown = data.get('region_breakdown', [])
    if region_breakdown:
        print(f"\nBreakdown by region:")
        for row in region_breakdown:
            region, count, oldest, newest = row
            print(f"  {region}: {count} records (from {oldest} to {newest})")
    
    # Recent records
    recent_records = data.get('recent_records', [])
    if recent_records:
        print(f"\nMost recent records:")
        print(f"{'Region':<8} {'Date':<20} {'Available':<10} {'Warning':<8} {'Zombie':<7} {'Wounded':<8} {'Out/Svc':<8} {'Total':<6}")
        print("-" * 80)
        for record in recent_records[:5]:
            uid, region, date_creation, avail, warn, zombie, wound, out, total = record
            date_str = date_creation.strftime("%Y-%m-%d %H:%M:%S")
            print(f"{region:<8} {date_str:<20} {avail:<10} {warn:<8} {zombie:<7} {wound:<8} {out:<8} {total:<6}")
    
    # Oldest records
    oldest_records = data.get('oldest_records', [])
    if oldest_records and len(oldest_records) > 0:
        print(f"\nOldest records:")
        print(f"{'Region':<8} {'Date':<20} {'Available':<10} {'Warning':<8} {'Zombie':<7} {'Wounded':<8} {'Out/Svc':<8} {'Total':<6}")
        print("-" * 80)
        for record in oldest_records[:5]:
            uid, region, date_creation, avail, warn, zombie, wound, out, total = record
            date_str = date_creation.strftime("%Y-%m-%d %H:%M:%S")
            print(f"{region:<8} {date_str:<20} {avail:<10} {warn:<8} {zombie:<7} {wound:<8} {out:<8} {total:<6}")

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Clean up regional_atm_counts database table",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clean_regional_database.py --action view
  python clean_regional_database.py --action delete-all --confirm
  python clean_regional_database.py --action delete-old --hours 24 --confirm
  python clean_regional_database.py --action delete-duplicates --confirm
  python clean_regional_database.py --action delete-region --region TL-DL --confirm
  python clean_regional_database.py --action backup
        """
    )
    
    parser.add_argument('--action', 
                      choices=['view', 'delete-all', 'delete-old', 'delete-duplicates', 'delete-region', 'backup'],
                      default='view',
                      help='Action to perform (default: view)')
    
    parser.add_argument('--region', 
                      help='Region code for region-specific operations')
    
    parser.add_argument('--hours', 
                      type=int, 
                      default=24,
                      help='Hours for delete-old operation (default: 24)')
    
    parser.add_argument('--confirm', 
                      action='store_true',
                      help='Confirm destructive operations')
    
    args = parser.parse_args()
    
    if not DB_AVAILABLE:
        log.error("Database connector not available")
        return 1
    
    cleaner = RegionalDatabaseCleaner()
    
    try:
        if args.action == 'view':
            log.info("Viewing current database records...")
            data = cleaner.view_current_records()
            display_records_summary(data)
            
        elif args.action == 'backup':
            log.info("Creating database backup...")
            success = cleaner.backup_before_cleanup()
            if success:
                print("✅ Backup created successfully")
            else:
                print("❌ Backup failed")
                return 1
                
        elif args.action == 'delete-all':
            if not args.confirm:
                print("❌ WARNING: This will delete ALL records!")
                print("Use --confirm flag to proceed")
                return 1
            
            log.info("Deleting all records...")
            success = cleaner.delete_all_records(confirm=args.confirm)
            if success:
                print("✅ All records deleted successfully")
            else:
                print("❌ Failed to delete records")
                return 1
                
        elif args.action == 'delete-old':
            if not args.confirm:
                print(f"❌ WARNING: This will delete records older than {args.hours} hours!")
                print("Use --confirm flag to proceed")
                return 1
            
            log.info(f"Deleting records older than {args.hours} hours...")
            success = cleaner.delete_old_records(args.hours, confirm=args.confirm)
            if success:
                print(f"✅ Old records deleted successfully")
            else:
                print("❌ Failed to delete old records")
                return 1
                
        elif args.action == 'delete-duplicates':
            if not args.confirm:
                print("❌ WARNING: This will delete duplicate records!")
                print("Use --confirm flag to proceed")
                return 1
            
            log.info("Deleting duplicate records...")
            success = cleaner.delete_duplicates(confirm=args.confirm)
            if success:
                print("✅ Duplicate records deleted successfully")
            else:
                print("❌ Failed to delete duplicates")
                return 1
                
        elif args.action == 'delete-region':
            if not args.region:
                print("❌ --region parameter required for delete-region action")
                return 1
            
            if not args.confirm:
                print(f"❌ WARNING: This will delete all records for region {args.region}!")
                print("Use --confirm flag to proceed")
                return 1
            
            log.info(f"Deleting records for region {args.region}...")
            success = cleaner.delete_region_records(args.region, confirm=args.confirm)
            if success:
                print(f"✅ Records for region {args.region} deleted successfully")
            else:
                print(f"❌ Failed to delete records for region {args.region}")
                return 1
        
        return 0
        
    except KeyboardInterrupt:
        log.info("Operation cancelled by user")
        return 1
    except Exception as e:
        log.error(f"Unexpected error: {str(e)}")
        return 1
    finally:
        cleaner.close_connection()

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
