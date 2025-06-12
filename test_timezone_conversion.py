#!/usr/bin/env python3
"""
Test the timezone conversion logic to identify the issue
"""

from datetime import datetime
import pytz

# Replicate the backend logic
DILI_TZ = pytz.timezone('Asia/Dili')  # UTC+9
UTC_TZ = pytz.UTC

def convert_to_dili_time(utc_timestamp: datetime) -> datetime:
    """
    Convert a UTC timestamp to Dili local time (UTC+9).
    Same function as in the backend.
    """
    try:
        # If the timestamp is timezone-naive, assume it's UTC
        if utc_timestamp.tzinfo is None:
            utc_timestamp = UTC_TZ.localize(utc_timestamp)
        
        # Convert to Dili time
        dili_timestamp = utc_timestamp.astimezone(DILI_TZ)
        
        # Return as timezone-naive datetime for JSON serialization
        return dili_timestamp.replace(tzinfo=None)
        
    except Exception as e:
        print(f"Error converting timestamp to Dili time: {e}")
        # Fallback: return original timestamp
        return utc_timestamp.replace(tzinfo=None) if utc_timestamp.tzinfo else utc_timestamp

def main():
    print("=" * 70)
    print("TIMEZONE CONVERSION ANALYSIS")
    print("=" * 70)
    
    # Current time scenario
    current_utc = datetime.now(UTC_TZ)
    current_dili_expected = current_utc.astimezone(DILI_TZ)
    
    print(f"Current UTC time: {current_utc}")
    print(f"Expected Dili time: {current_dili_expected}")
    print()
    
    # Test the conversion function
    print("Testing convert_to_dili_time function:")
    print("-" * 40)
    
    # Test 1: Current UTC time
    utc_naive = current_utc.replace(tzinfo=None)
    converted = convert_to_dili_time(utc_naive)
    print(f"Input (UTC naive): {utc_naive}")
    print(f"Output (Dili naive): {converted}")
    print(f"Expected: {current_dili_expected.replace(tzinfo=None)}")
    print(f"Match: {converted == current_dili_expected.replace(tzinfo=None)}")
    print()
    
    # Test 2: Simulate database timestamp that would show 17:11
    # If current Dili time is 16:50, what UTC time would produce 17:11 Dili?
    dili_1711 = DILI_TZ.localize(datetime(2025, 6, 12, 17, 11, 0))
    utc_for_1711 = dili_1711.astimezone(UTC_TZ)
    
    print("Scenario: What would cause 17:11 Dili display?")
    print("-" * 50)
    print(f"If database has: {utc_for_1711.replace(tzinfo=None)} (UTC)")
    print(f"Backend converts to: {convert_to_dili_time(utc_for_1711.replace(tzinfo=None))}")
    print(f"This would show as: 17:11 in Dili time")
    print()
    
    # Test 3: Check if there's a timezone offset issue
    print("Potential Issues:")
    print("-" * 20)
    
    # Issue 1: Database has wrong timezone data
    print("1. Database might contain future timestamps")
    print("2. Database might contain timestamps already in Dili time")
    print("3. Data retrieval script might be setting wrong timestamps")
    print()
    
    # Test what happens if data is already in Dili time
    dili_now = datetime.now()  # Local system time
    print(f"If database contains local time: {dili_now}")
    print(f"Backend would convert to: {convert_to_dili_time(dili_now)}")
    print("This would show as Dili time + 9 hours!")

if __name__ == "__main__":
    main()
