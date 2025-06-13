#!/usr/bin/env python3
"""
Database Timestamp Audit and UTC Conversion Tool

This script performs a comprehensive audit of all timestamp columns in the database
and converts any non-UTC timestamps to proper UTC format.

Features:
1. Identifies all tables and timestamp columns
2. Analyzes current timezone formats
3. Detects future timestamps (indicating timezone issues)
4. Converts timestamps to UTC format where needed
5. Provides detailed reports before and after conversion

Author: ATM Monitoring System
Created: 2025-06-13
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
import pytz
import json
from typing import Dict, List, Any, Optional, Tuple
import argparse
import sys

# Database configuration
DB_CONFIG = {
    'host': '88.222.214.26',
    'port': 5432,
    'database': 'development_db',
    'user': 'timlesdev',
    'password': 'timlesdev'
}

# Timezone configuration
DILI_TZ = pytz.timezone('Asia/Dili')  # UTC+9
UTC_TZ = pytz.UTC

class DatabaseTimestampAuditor:
    """Comprehensive database timestamp auditor and converter"""
    
    def __init__(self):
        self.conn = None
        self.audit_results = {}
        self.conversion_log = []
        
    def connect(self) -> bool:
        """Connect to the database"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
            print("✅ Connected to database successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            self.conn.close()
            print("✅ Disconnected from database")
    
    def get_all_tables_with_timestamps(self) -> List[Dict[str, Any]]:
        """Get all tables with timestamp columns"""
        cursor = self.conn.cursor()
        
        query = """
            SELECT 
                t.table_name,
                array_agg(
                    json_build_object(
                        'column_name', c.column_name,
                        'data_type', c.data_type,
                        'is_nullable', c.is_nullable
                    ) ORDER BY c.column_name
                ) as timestamp_columns
            FROM information_schema.tables t
            JOIN information_schema.columns c ON t.table_name = c.table_name
            WHERE t.table_schema = 'public'
                AND t.table_type = 'BASE TABLE'
                AND (
                    c.data_type IN ('timestamp with time zone', 'timestamp without time zone', 'date')
                    OR c.column_name ILIKE '%time%'
                    OR c.column_name ILIKE '%date%'
                    OR c.column_name ILIKE '%created%'
                    OR c.column_name ILIKE '%updated%'
                )
            GROUP BY t.table_name
            ORDER BY t.table_name
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        
        return [dict(row) for row in results]
    
    def analyze_table_timestamps(self, table_name: str, timestamp_columns: List[Dict]) -> Dict[str, Any]:
        """Analyze timestamp columns in a specific table"""
        cursor = self.conn.cursor()
        analysis = {
            'table_name': table_name,
            'total_records': 0,
            'columns': {},
            'issues_found': []
        }
        
        try:
            # Get total record count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            analysis['total_records'] = cursor.fetchone()[0]
            
            if analysis['total_records'] == 0:
                analysis['issues_found'].append("Table is empty")
                return analysis
            
            current_utc = datetime.now(UTC_TZ)
            current_dili = current_utc.astimezone(DILI_TZ)
            
            for col_info in timestamp_columns:
                col_name = col_info['column_name']
                data_type = col_info['data_type']
                
                column_analysis = {
                    'column_name': col_name,
                    'data_type': data_type,
                    'sample_values': [],
                    'future_count': 0,
                    'null_count': 0,
                    'timezone_pattern': 'unknown',
                    'needs_conversion': False
                }
                
                # Get sample values and stats
                cursor.execute(f"""
                    SELECT 
                        {col_name} as timestamp_value,
                        COUNT(*) as count
                    FROM {table_name} 
                    WHERE {col_name} IS NOT NULL
                    GROUP BY {col_name}
                    ORDER BY {col_name} DESC 
                    LIMIT 10
                """)
                
                sample_results = cursor.fetchall()
                for row in sample_results:
                    timestamp_value = row[0]
                    count = row[1]
                    
                    if timestamp_value:
                        column_analysis['sample_values'].append({
                            'value': str(timestamp_value),
                            'count': count,
                            'is_future': timestamp_value > current_utc if timestamp_value.tzinfo else timestamp_value > current_utc.replace(tzinfo=None)
                        })
                
                # Count future timestamps
                if 'timestamp' in data_type.lower() or 'date' in data_type.lower():
                    if 'with time zone' in data_type:
                        cursor.execute(f"""
                            SELECT COUNT(*) 
                            FROM {table_name} 
                            WHERE {col_name} > NOW()
                        """)
                    else:
                        cursor.execute(f"""
                            SELECT COUNT(*) 
                            FROM {table_name} 
                            WHERE {col_name} > NOW()
                        """)
                    
                    column_analysis['future_count'] = cursor.fetchone()[0]
                
                # Count null values
                cursor.execute(f"""
                    SELECT COUNT(*) 
                    FROM {table_name} 
                    WHERE {col_name} IS NULL
                """)
                column_analysis['null_count'] = cursor.fetchone()[0]
                
                # Determine timezone pattern and if conversion is needed
                if column_analysis['future_count'] > 0:
                    column_analysis['timezone_pattern'] = 'likely_dili_stored_as_utc'
                    column_analysis['needs_conversion'] = True
                    analysis['issues_found'].append(f"Column {col_name} has {column_analysis['future_count']} future timestamps")
                elif sample_results:
                    # Check if timestamps look like UTC (reasonable compared to current time)
                    latest_timestamp = sample_results[0][0] if sample_results else None
                    if latest_timestamp:
                        if latest_timestamp.tzinfo:
                            # Timezone-aware timestamp
                            time_diff = current_utc - latest_timestamp
                        else:
                            # Timezone-naive timestamp - assume UTC for comparison
                            time_diff = current_utc.replace(tzinfo=None) - latest_timestamp
                        
                        if abs(time_diff.total_seconds()) < 86400:  # Within 24 hours
                            column_analysis['timezone_pattern'] = 'likely_utc'
                        elif time_diff.total_seconds() > 25200:  # More than 7 hours behind
                            column_analysis['timezone_pattern'] = 'possibly_dili_time'
                        else:
                            column_analysis['timezone_pattern'] = 'uncertain'
                
                analysis['columns'][col_name] = column_analysis
        
        except Exception as e:
            analysis['issues_found'].append(f"Error analyzing table: {str(e)}")
        
        cursor.close()
        return analysis
    
    def run_full_audit(self) -> Dict[str, Any]:
        """Run comprehensive audit of all timestamp columns"""
        print("=" * 80)
        print("🔍 STARTING COMPREHENSIVE DATABASE TIMESTAMP AUDIT")
        print("=" * 80)
        
        # Get current times for reference
        current_utc = datetime.now(UTC_TZ)
        current_dili = current_utc.astimezone(DILI_TZ)
        
        print(f"Current UTC time:  {current_utc}")
        print(f"Current Dili time: {current_dili}")
        print()
        
        # Get all tables with timestamp columns
        tables = self.get_all_tables_with_timestamps()
        print(f"Found {len(tables)} tables with timestamp columns:")
        
        audit_summary = {
            'audit_timestamp': current_utc.isoformat(),
            'tables_analyzed': len(tables),
            'total_issues': 0,
            'tables_needing_conversion': [],
            'detailed_results': {}
        }
        
        for table_info in tables:
            table_name = table_info['table_name']
            timestamp_columns = table_info['timestamp_columns']
            
            print(f"\n--- Analyzing {table_name} ---")
            print(f"Timestamp columns: {[col['column_name'] for col in timestamp_columns]}")
            
            analysis = self.analyze_table_timestamps(table_name, timestamp_columns)
            audit_summary['detailed_results'][table_name] = analysis
            
            # Check for issues
            needs_conversion = False
            for col_name, col_analysis in analysis['columns'].items():
                if col_analysis['needs_conversion']:
                    needs_conversion = True
                    print(f"  ⚠️  {col_name}: {col_analysis['future_count']} future timestamps ({col_analysis['timezone_pattern']})")
                else:
                    print(f"  ✅ {col_name}: {col_analysis['timezone_pattern']}")
            
            if needs_conversion:
                audit_summary['tables_needing_conversion'].append(table_name)
            
            audit_summary['total_issues'] += len(analysis['issues_found'])
        
        self.audit_results = audit_summary
        return audit_summary
    
    def convert_future_timestamps_to_utc(self, table_name: str, column_name: str, dry_run: bool = True) -> Dict[str, Any]:
        """Convert future timestamps to UTC by subtracting Dili offset"""
        cursor = self.conn.cursor()
        conversion_result = {
            'table_name': table_name,
            'column_name': column_name,
            'records_converted': 0,
            'dry_run': dry_run,
            'conversion_details': []
        }
        
        try:
            # Get all future timestamps
            cursor.execute(f"""
                SELECT id, {column_name}
                FROM {table_name}
                WHERE {column_name} > NOW()
                ORDER BY {column_name} DESC
            """)
            
            future_records = cursor.fetchall()
            print(f"Found {len(future_records)} future timestamps in {table_name}.{column_name}")
            
            for record in future_records:
                record_id = record[0]
                original_timestamp = record[1]
                
                # Calculate the correct UTC time (subtract 9 hours)
                if original_timestamp.tzinfo:
                    # If timezone-aware, first convert to UTC then subtract 9 hours
                    correct_utc = original_timestamp.astimezone(UTC_TZ) - timedelta(hours=9)
                else:
                    # If timezone-naive, assume it's in the wrong timezone and subtract 9 hours
                    correct_utc = original_timestamp - timedelta(hours=9)
                
                conversion_detail = {
                    'record_id': record_id,
                    'original_timestamp': str(original_timestamp),
                    'corrected_timestamp': str(correct_utc),
                    'offset_applied': '-9 hours'
                }
                conversion_result['conversion_details'].append(conversion_detail)
                
                print(f"Record {record_id}: {original_timestamp} → {correct_utc}")
                
                if not dry_run:
                    # Update the record
                    cursor.execute(f"""
                        UPDATE {table_name} 
                        SET {column_name} = %s 
                        WHERE id = %s
                    """, (correct_utc, record_id))
                    
                    conversion_result['records_converted'] += 1
            
            if not dry_run and conversion_result['records_converted'] > 0:
                self.conn.commit()
                print(f"✅ Successfully updated {conversion_result['records_converted']} records")
            elif dry_run:
                print("🔍 DRY RUN - No changes made to database")
        
        except Exception as e:
            if not dry_run:
                self.conn.rollback()
            conversion_result['error'] = str(e)
            print(f"❌ Error during conversion: {e}")
        
        cursor.close()
        return conversion_result
    
    def fix_all_timezone_issues(self, dry_run: bool = True) -> Dict[str, Any]:
        """Fix all identified timezone issues across all tables"""
        print("=" * 80)
        print(f"🔧 {'SIMULATING' if dry_run else 'EXECUTING'} TIMEZONE CORRECTIONS")
        print("=" * 80)
        
        if not self.audit_results:
            print("❌ No audit results available. Run full_audit() first.")
            return {}
        
        fix_summary = {
            'dry_run': dry_run,
            'tables_processed': 0,
            'total_records_converted': 0,
            'conversion_results': {}
        }
        
        for table_name in self.audit_results['tables_needing_conversion']:
            table_analysis = self.audit_results['detailed_results'][table_name]
            
            print(f"\n--- Processing {table_name} ---")
            
            for col_name, col_analysis in table_analysis['columns'].items():
                if col_analysis['needs_conversion']:
                    print(f"Converting {col_name} (has {col_analysis['future_count']} future timestamps)...")
                    
                    conversion_result = self.convert_future_timestamps_to_utc(
                        table_name, col_name, dry_run
                    )
                    
                    fix_summary['conversion_results'][f"{table_name}.{col_name}"] = conversion_result
                    fix_summary['total_records_converted'] += conversion_result['records_converted']
            
            fix_summary['tables_processed'] += 1
        
        return fix_summary
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate a comprehensive audit report"""
        if not self.audit_results:
            return "No audit results available. Run audit first."
        
        report = []
        report.append("=" * 80)
        report.append("DATABASE TIMESTAMP AUDIT REPORT")
        report.append("=" * 80)
        report.append(f"Audit Time: {self.audit_results['audit_timestamp']}")
        report.append(f"Tables Analyzed: {self.audit_results['tables_analyzed']}")
        report.append(f"Total Issues Found: {self.audit_results['total_issues']}")
        report.append(f"Tables Needing Conversion: {len(self.audit_results['tables_needing_conversion'])}")
        report.append("")
        
        # Summary of issues
        if self.audit_results['tables_needing_conversion']:
            report.append("TABLES REQUIRING TIMEZONE CONVERSION:")
            report.append("-" * 40)
            for table_name in self.audit_results['tables_needing_conversion']:
                table_analysis = self.audit_results['detailed_results'][table_name]
                report.append(f"• {table_name}")
                for col_name, col_analysis in table_analysis['columns'].items():
                    if col_analysis['needs_conversion']:
                        report.append(f"  - {col_name}: {col_analysis['future_count']} future timestamps")
            report.append("")
        
        # Detailed analysis
        report.append("DETAILED ANALYSIS:")
        report.append("-" * 20)
        for table_name, analysis in self.audit_results['detailed_results'].items():
            report.append(f"\n{table_name.upper()}:")
            report.append(f"  Total Records: {analysis['total_records']}")
            
            for col_name, col_analysis in analysis['columns'].items():
                report.append(f"  {col_name}:")
                report.append(f"    Data Type: {col_analysis['data_type']}")
                report.append(f"    Timezone Pattern: {col_analysis['timezone_pattern']}")
                report.append(f"    Future Timestamps: {col_analysis['future_count']}")
                report.append(f"    Null Values: {col_analysis['null_count']}")
                report.append(f"    Needs Conversion: {'Yes' if col_analysis['needs_conversion'] else 'No'}")
                
                if col_analysis['sample_values']:
                    report.append("    Sample Values:")
                    for sample in col_analysis['sample_values'][:3]:
                        status = " (FUTURE!)" if sample['is_future'] else ""
                        report.append(f"      {sample['value']}{status}")
            
            if analysis['issues_found']:
                report.append("  Issues Found:")
                for issue in analysis['issues_found']:
                    report.append(f"    - {issue}")
        
        report_text = "\n".join(report)
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report_text)
            print(f"📄 Report saved to {output_file}")
        
        return report_text

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Database Timestamp Audit and UTC Conversion Tool')
    parser.add_argument('--audit', action='store_true', help='Run timestamp audit')
    parser.add_argument('--fix', action='store_true', help='Fix timezone issues (requires --audit first)')
    parser.add_argument('--dry-run', action='store_true', default=True, help='Simulate fixes without changing data (default)')
    parser.add_argument('--apply', action='store_true', help='Actually apply fixes to database')
    parser.add_argument('--report', type=str, help='Generate report file (specify filename)')
    
    args = parser.parse_args()
    
    if not any([args.audit, args.fix]):
        print("Please specify --audit or --fix")
        return
    
    auditor = DatabaseTimestampAuditor()
    
    if not auditor.connect():
        return
    
    try:
        if args.audit or args.fix:
            print("Running timestamp audit...")
            audit_results = auditor.run_full_audit()
            
            if args.report:
                auditor.generate_report(args.report)
        
        if args.fix:
            dry_run = not args.apply
            if dry_run:
                print("\n⚠️  Running in DRY RUN mode. Use --apply to make actual changes.")
            else:
                print("\n⚠️  APPLYING ACTUAL CHANGES TO DATABASE!")
                response = input("Are you sure you want to proceed? (yes/no): ")
                if response.lower() != 'yes':
                    print("Aborted.")
                    return
            
            fix_results = auditor.fix_all_timezone_issues(dry_run)
            
            print(f"\n📊 CONVERSION SUMMARY:")
            print(f"Tables Processed: {fix_results['tables_processed']}")
            print(f"Records Converted: {fix_results['total_records_converted']}")
            print(f"Mode: {'DRY RUN' if dry_run else 'APPLIED'}")
    
    finally:
        auditor.disconnect()

if __name__ == "__main__":
    main()
