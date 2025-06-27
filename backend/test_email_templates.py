#!/usr/bin/env python3
"""
Email Template Preview and Test Script
This script allows you to preview and test the password reset email templates
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_service import EmailService

def preview_email_content():
    """Preview the email content without sending"""
    print("=" * 60)
    print("EMAIL TEMPLATE PREVIEW")
    print("=" * 60)
    
    # Sample data for preview
    username = "john.doe"
    reset_link = "https://your-dashboard.com/reset-password?token=sample_token_here"
    
    email_service = EmailService()
    
    print("\n📧 SUBJECT LINE:")
    print("🔐 Password Reset Request - ATM Monitoring Dashboard")
    
    print("\n📝 PLAIN TEXT VERSION:")
    print("-" * 40)
    text_content = email_service._get_password_reset_text(username, reset_link)
    print(text_content)
    
    print("\n🌐 HTML VERSION:")
    print("-" * 40)
    html_content = email_service._get_password_reset_template(username, reset_link)
    
    # Save HTML to a file for browser preview
    with open('/tmp/email_preview.html', 'w') as f:
        f.write(html_content)
    
    print("HTML email saved to: /tmp/email_preview.html")
    print("You can open this file in your browser to see how the email looks.")
    
    print(f"\n✅ Email service status: {'Enabled' if email_service.enabled else 'Disabled'}")
    if email_service.enabled:
        print(f"📧 From Email: {os.getenv('MAILJET_FROM_EMAIL')}")
        print(f"👤 From Name: {os.getenv('MAILJET_FROM_NAME')}")
    
    return email_service

async def test_send_email(email_service, test_email=None):
    """Test sending an actual email"""
    if not email_service.enabled:
        print("\n❌ Email service is not enabled. Please check your Mailjet credentials.")
        return False
    
    if not test_email:
        test_email = input("\n📧 Enter your email address to receive a test password reset email: ").strip()
    
    if not test_email:
        print("❌ No email address provided.")
        return False
    
    print(f"\n📤 Sending test password reset email to: {test_email}")
    
    # Generate test data
    username = "test.user"
    reset_link = "https://your-dashboard.com/reset-password?token=test_token_12345"
    
    try:
        success = await email_service.send_password_reset_email(test_email, username, reset_link)
        
        if success:
            print("✅ Test email sent successfully!")
            print(f"📧 Check your inbox at: {test_email}")
            print("📋 The email should arrive within a few minutes.")
            return True
        else:
            print("❌ Failed to send test email. Check the logs for details.")
            return False
            
    except Exception as e:
        print(f"❌ Error sending test email: {e}")
        return False

def validate_mailjet_config():
    """Validate Mailjet configuration"""
    print("\n🔧 MAILJET CONFIGURATION CHECK:")
    print("-" * 40)
    
    api_key = os.getenv('MAILJET_API_KEY', '')
    secret_key = os.getenv('MAILJET_SECRET_KEY', '')
    from_email = os.getenv('MAILJET_FROM_EMAIL', '')
    from_name = os.getenv('MAILJET_FROM_NAME', '')
    
    print(f"API Key: {'✅ Set' if api_key else '❌ Missing'}")
    print(f"Secret Key: {'✅ Set' if secret_key else '❌ Missing'}")
    print(f"From Email: {from_email if from_email else '❌ Missing'}")
    print(f"From Name: {from_name if from_name else '❌ Missing'}")
    
    if api_key:
        print(f"API Key Preview: {api_key[:8]}...")
    if secret_key:
        print(f"Secret Key Preview: {secret_key[:8]}...")
    
    all_configured = all([api_key, secret_key, from_email, from_name])
    print(f"\nConfiguration Status: {'✅ Complete' if all_configured else '❌ Incomplete'}")
    
    return all_configured

def main():
    """Main function"""
    print("🏧 ATM Dashboard - Email Template Tester")
    print("=" * 60)
    
    # Validate configuration
    config_ok = validate_mailjet_config()
    
    # Preview email content
    email_service = preview_email_content()
    
    if not config_ok:
        print("\n⚠️  Mailjet configuration is incomplete. Please update your .env file.")
        return
    
    # Ask user what they want to do
    print("\n" + "=" * 60)
    print("What would you like to do?")
    print("1. Preview email templates only")
    print("2. Send a test email")
    print("3. Exit")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "2":
        asyncio.run(test_send_email(email_service))
    elif choice == "1":
        print("\n✅ Email templates previewed successfully!")
        print("📄 HTML preview saved to /tmp/email_preview.html")
    elif choice == "3":
        print("\n👋 Goodbye!")
    else:
        print("\n❌ Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
