#!/usr/bin/env python3
"""
Password Reset Token Validity Information
Shows how long tokens are valid and when they expire
"""

import jwt
import sys
from datetime import datetime, timezone
from user_management_api import PASSWORD_RESET_TOKEN_EXPIRE_HOURS, PASSWORD_RESET_SECRET

def check_token_validity(token=None):
    """Check token validity and expiration"""
    print("🔐 Password Reset Token Validity Information")
    print("=" * 55)
    
    # Configuration info
    print(f"⏰ Token Validity Duration: {PASSWORD_RESET_TOKEN_EXPIRE_HOURS} hours")
    print(f"📅 That's equivalent to: {PASSWORD_RESET_TOKEN_EXPIRE_HOURS // 24} day(s)")
    
    if token:
        print(f"\n🎫 Analyzing provided token...")
        try:
            # Decode without verification to see the payload
            decoded = jwt.decode(token, options={"verify_signature": False})
            
            # Get expiration timestamp
            exp_timestamp = decoded.get('exp')
            if exp_timestamp:
                exp_time = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
                current_time = datetime.now(timezone.utc)
                
                print(f"👤 User ID: {decoded.get('user_id', 'N/A')}")
                print(f"📧 Email: {decoded.get('email', 'N/A')}")
                print(f"🕐 Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                print(f"⏰ Token Expires: {exp_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                
                if current_time < exp_time:
                    remaining = exp_time - current_time
                    hours_remaining = remaining.total_seconds() / 3600
                    print(f"✅ Token Status: VALID")
                    print(f"⏳ Time Remaining: {hours_remaining:.1f} hours")
                    
                    if hours_remaining < 1:
                        minutes_remaining = remaining.total_seconds() / 60
                        print(f"⚠️  Warning: Only {minutes_remaining:.0f} minutes left!")
                else:
                    print(f"❌ Token Status: EXPIRED")
                    expired_by = current_time - exp_time
                    hours_expired = expired_by.total_seconds() / 3600
                    print(f"💔 Expired by: {hours_expired:.1f} hours")
            else:
                print("❌ No expiration timestamp found in token")
                
        except jwt.InvalidTokenError as e:
            print(f"❌ Invalid token format: {e}")
        except Exception as e:
            print(f"❌ Error analyzing token: {e}")
    
    print(f"\n📋 Password Reset Token Security Features:")
    print(f"• Single-use only (cannot be reused)")
    print(f"• {PASSWORD_RESET_TOKEN_EXPIRE_HOURS}-hour expiration for security")
    print(f"• User-specific (tied to specific account)")
    print(f"• Secure JWT format with signature validation")
    print(f"• Database tracking for additional security")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        token = sys.argv[1]
        check_token_validity(token)
    else:
        check_token_validity()
        
        print(f"\n💡 To check a specific token:")
        print(f"   python check_token_validity.py \"your_token_here\"")
        print(f"\n📧 Or paste a token to check:")
        
        user_token = input("🎫 Enter token (or press Enter to skip): ").strip()
        if user_token:
            print("\n" + "=" * 55)
            check_token_validity(user_token)

if __name__ == "__main__":
    main()
