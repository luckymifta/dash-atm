#!/usr/bin/env python3
"""
Quick Fix: Align Dashboard Cards with ATM Information Data

This script provides options to fix the data discrepancy by:
1. Making dashboard use terminal_details data (more accurate)
2. Making ATM info page use regional_data (faster)
3. Creating a unified data view
"""

import os
import sys

def get_user_choice():
    """Get user's choice for fix approach"""
    print("🔧 ATM CARD STATUS DATA ALIGNMENT TOOL")
    print("=" * 50)
    print()
    print("Choose how to fix the data discrepancy:")
    print()
    print("1. 📊 Make Dashboard Cards use Terminal Details data (RECOMMENDED)")
    print("   ✅ More accurate (shows actual terminal status)")
    print("   ⚠️  Slightly slower (calculates from individual terminals)")
    print()
    print("2. 🏃 Make ATM Information use Regional Data")
    print("   ✅ Faster (uses aggregated data)")
    print("   ⚠️  Less detailed (loses individual terminal information)")
    print()
    print("3. 🔍 Just run verification script first")
    print("   ✅ Analyze the issue before making changes")
    print()
    
    while True:
        choice = input("Enter your choice (1, 2, or 3): ").strip()
        if choice in ['1', '2', '3']:
            return choice
        print("❌ Invalid choice. Please enter 1, 2, or 3.")

def create_dashboard_fix():
    """Create a fix to make dashboard cards use terminal_details data"""
    print("\n🔧 Creating dashboard fix...")
    
    # Create a new API endpoint that calculates summary from terminal_details
    api_fix_content = '''
// Add this new endpoint to backend/api_option_2_fastapi_fixed.py

@app.get("/api/v1/atm/status/summary-from-terminals", response_model=ATMSummaryResponse, tags=["ATM Status"])
async def get_atm_summary_from_terminals(
    db_check: bool = Depends(validate_db_connection)
):
    """
    Get ATM summary calculated from individual terminal details
    This ensures consistency with ATM information page
    """
    conn = await get_db_connection()
    if not conn:
        raise HTTPException(status_code=503, detail="Database connection unavailable")
    
    try:
        # Get latest status for each terminal
        query = """
            WITH latest_terminals AS (
                SELECT DISTINCT ON (terminal_id)
                    terminal_id, 
                    fetched_status,
                    issue_state_name,
                    retrieved_date
                FROM terminal_details
                ORDER BY terminal_id, retrieved_date DESC
            ),
            status_mapping AS (
                SELECT 
                    terminal_id,
                    CASE 
                        WHEN fetched_status = 'AVAILABLE' THEN 'available'
                        WHEN fetched_status = 'WARNING' THEN 'warning'
                        WHEN fetched_status IN ('WOUNDED', 'HARD', 'CASH') THEN 'wounded'
                        WHEN fetched_status = 'ZOMBIE' THEN 'zombie'
                        WHEN fetched_status IN ('OUT_OF_SERVICE', 'UNAVAILABLE') THEN 'out_of_service'
                        ELSE 'out_of_service'
                    END as mapped_status
                FROM latest_terminals
            )
            SELECT 
                COUNT(*) FILTER (WHERE mapped_status = 'available') as total_available,
                COUNT(*) FILTER (WHERE mapped_status = 'warning') as total_warning,
                COUNT(*) FILTER (WHERE mapped_status = 'zombie') as total_zombie,
                COUNT(*) FILTER (WHERE mapped_status = 'wounded') as total_wounded,
                COUNT(*) FILTER (WHERE mapped_status = 'out_of_service') as total_out_of_service,
                COUNT(*) as total_atms
            FROM status_mapping
        """
        
        row = await conn.fetchrow(query)
        
        if not row:
            raise HTTPException(status_code=404, detail="No terminal data found")
        
        # Calculate totals
        available = row['total_available'] or 0
        warning = row['total_warning'] or 0
        zombie = row['total_zombie'] or 0
        wounded = row['total_wounded'] or 0
        out_of_service = row['total_out_of_service'] or 0
        total_atms = row['total_atms'] or 0
        
        # Calculate availability including both AVAILABLE and WARNING ATMs
        operational_atms = available + warning
        availability_percentage = (operational_atms / total_atms * 100) if total_atms > 0 else 0
        
        status_counts = ATMStatusCounts(
            available=available,
            warning=warning,
            zombie=zombie,
            wounded=wounded,
            out_of_service=out_of_service,
            total=total_atms
        )
        
        return ATMSummaryResponse(
            total_atms=total_atms,
            status_counts=status_counts,
            overall_availability=round(availability_percentage, 2),
            total_regions=1,  # Currently only TL-DL
            last_updated=datetime.utcnow().isoformat(),
            data_source="terminal_details"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ATM summary from terminals: {e}")
        raise HTTPException(status_code=500, detail="Failed to get ATM summary")
    finally:
        await release_db_connection(conn)
'''
    
    frontend_fix_content = '''
// Update frontend/src/app/dashboard/page.tsx
// Change the API call from:
const response = await atmApiService.getATMSummary();

// To:
const response = await fetch(`${API_CONFIG.BASE_URL}/v1/atm/status/summary-from-terminals`);
const data = await response.json();
'''
    
    print("📝 API Fix Content:")
    print(api_fix_content)
    print("\n📝 Frontend Fix Content:")
    print(frontend_fix_content)
    
    # Save to files
    with open('/Users/luckymifta/Documents/2. AREA/dash-atm/dashboard_fix_api.py', 'w') as f:
        f.write(api_fix_content)
    
    with open('/Users/luckymifta/Documents/2. AREA/dash-atm/dashboard_fix_frontend.js', 'w') as f:
        f.write(frontend_fix_content)
    
    print("\n✅ Fix files created:")
    print("  - dashboard_fix_api.py (add to backend)")
    print("  - dashboard_fix_frontend.js (modify frontend)")

def create_atm_info_fix():
    """Create a fix to make ATM info use regional data"""
    print("\n🔧 Creating ATM information page fix...")
    
    fix_content = '''
// Update frontend/src/app/atm-information/page.tsx
// Replace the fetchTerminalDetails function with:

const fetchTerminalDetails = async () => {
    try {
        setLoading(true);
        setError(null);
        
        // Use regional data instead of terminal details for consistency
        const response = await atmApiService.getRegionalData();
        
        // Convert regional data to terminal-like format
        const terminals: TerminalDetails[] = [];
        
        if (response.regional_data && response.regional_data.length > 0) {
            const regionData = response.regional_data[0]; // TL-DL region
            
            // Create mock terminals based on regional counts
            let terminalId = 1;
            
            // Add available terminals
            for (let i = 0; i < regionData.status_counts.available; i++) {
                terminals.push({
                    terminal_id: `${terminalId++}`,
                    external_id: `ATM-${terminalId}`,
                    location_str: `Available Terminal ${i + 1}`,
                    issue_state_name: 'AVAILABLE',
                    fetched_status: 'AVAILABLE',
                    city: 'Dili',
                    bank: 'Various'
                });
            }
            
            // Add warning terminals
            for (let i = 0; i < regionData.status_counts.warning; i++) {
                terminals.push({
                    terminal_id: `${terminalId++}`,
                    external_id: `ATM-${terminalId}`,
                    location_str: `Warning Terminal ${i + 1}`,
                    issue_state_name: 'WARNING',
                    fetched_status: 'WARNING',
                    city: 'Dili',
                    bank: 'Various'
                });
            }
            
            // Add wounded terminals
            for (let i = 0; i < regionData.status_counts.wounded; i++) {
                terminals.push({
                    terminal_id: `${terminalId++}`,
                    external_id: `ATM-${terminalId}`,
                    location_str: `Wounded Terminal ${i + 1}`,
                    issue_state_name: 'WOUNDED',
                    fetched_status: 'WOUNDED',
                    city: 'Dili',
                    bank: 'Various'
                });
            }
            
            // Add zombie terminals
            for (let i = 0; i < regionData.status_counts.zombie; i++) {
                terminals.push({
                    terminal_id: `${terminalId++}`,
                    external_id: `ATM-${terminalId}`,
                    location_str: `Zombie Terminal ${i + 1}`,
                    issue_state_name: 'ZOMBIE',
                    fetched_status: 'ZOMBIE',
                    city: 'Dili',
                    bank: 'Various'
                });
            }
            
            // Add out of service terminals
            for (let i = 0; i < regionData.status_counts.out_of_service; i++) {
                terminals.push({
                    terminal_id: `${terminalId++}`,
                    external_id: `ATM-${terminalId}`,
                    location_str: `Out of Service Terminal ${i + 1}`,
                    issue_state_name: 'OUT_OF_SERVICE',
                    fetched_status: 'OUT_OF_SERVICE',
                    city: 'Dili',
                    bank: 'Various'
                });
            }
        }
        
        setTerminalData(terminals);
    } catch (err) {
        console.error('Error fetching terminal details:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch terminal details');
    } finally {
        setLoading(false);
    }
};
'''
    
    print("📝 ATM Information Fix Content:")
    print(fix_content)
    
    # Save to file
    with open('/Users/luckymifta/Documents/2. AREA/dash-atm/atm_info_fix.js', 'w') as f:
        f.write(fix_content)
    
    print("\n✅ Fix file created:")
    print("  - atm_info_fix.js (replace function in frontend)")
    print("\n⚠️  Note: This approach loses individual terminal details!")

def run_verification():
    """Run the verification script"""
    print("\n🔍 Running verification script...")
    
    script_path = '/Users/luckymifta/Documents/2. AREA/dash-atm/verify_card_data_sources.py'
    
    if os.path.exists(script_path):
        print(f"📋 Executing: python {script_path}")
        os.system(f"python {script_path}")
    else:
        print("❌ Verification script not found!")
        print("Please run the verify_card_data_sources.py script manually.")

def main():
    """Main function"""
    choice = get_user_choice()
    
    if choice == '1':
        create_dashboard_fix()
        print("\n💡 NEXT STEPS:")
        print("1. Add the API endpoint code to backend/api_option_2_fastapi_fixed.py")
        print("2. Update the frontend dashboard to use the new endpoint")
        print("3. Test both pages to ensure they show the same data")
        
    elif choice == '2':
        create_atm_info_fix()
        print("\n💡 NEXT STEPS:")
        print("1. Replace the fetchTerminalDetails function in the frontend")
        print("2. Test the ATM information page")
        print("3. Note: You'll lose individual terminal details!")
        
    elif choice == '3':
        run_verification()
        print("\n💡 NEXT STEPS:")
        print("1. Review the verification results above")
        print("2. Decide on the best fix approach based on the analysis")
        print("3. Run this script again with option 1 or 2")

if __name__ == "__main__":
    main()
