"""
Email service configuration for password reset functionality
"""

from mailjet_rest import Client
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Mailjet configuration
MAILJET_API_KEY = os.getenv('MAILJET_API_KEY', '')
MAILJET_SECRET_KEY = os.getenv('MAILJET_SECRET_KEY', '')
FROM_EMAIL = os.getenv('MAILJET_FROM_EMAIL', 'noreply@atm-dashboard.com')
FROM_NAME = os.getenv('MAILJET_FROM_NAME', 'ATM Dashboard')

class EmailService:
    def __init__(self):
        if MAILJET_API_KEY and MAILJET_SECRET_KEY:
            self.mailjet = Client(auth=(MAILJET_API_KEY, MAILJET_SECRET_KEY), version='v3.1')
            self.enabled = True
            logger.info("Email service initialized with Mailjet")
        else:
            self.mailjet = None
            self.enabled = False
            logger.warning("Email service disabled - Mailjet credentials not found")
    
    async def send_password_reset_email(self, email: str, username: str, reset_link: str) -> bool:
        """Send password reset email"""
        if not self.enabled:
            logger.info(f"Email service disabled - would send reset email to {email}")
            logger.info(f"Reset link: {reset_link}")
            return True  # Return True for testing purposes
        
        try:
            data = {
                'Messages': [
                    {
                        "From": {
                            "Email": FROM_EMAIL,
                            "Name": FROM_NAME
                        },
                        "To": [
                            {
                                "Email": email,
                                "Name": username
                            }
                        ],
                        "Subject": "🔐 Password Reset Request - ATM Monitoring Dashboard",
                        "HTMLPart": self._get_password_reset_template(username, reset_link),
                        "TextPart": self._get_password_reset_text(username, reset_link)
                    }
                ]
            }
            
            result = self.mailjet.send.create(data=data)
            
            if result.status_code == 200:
                logger.info(f"Password reset email sent successfully to {email}")
                return True
            else:
                logger.error(f"Failed to send password reset email: Status {result.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            return False
    
    def _get_password_reset_template(self, username: str, reset_link: str) -> str:
        """Get HTML template for password reset email"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset Request - ATM Monitoring Dashboard</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; 
                    line-height: 1.6; 
                    color: #333; 
                    margin: 0; 
                    padding: 0; 
                    background-color: #f5f5f5;
                }}
                .container {{ 
                    max-width: 600px; 
                    margin: 20px auto; 
                    background-color: white; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .header {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; 
                    padding: 30px 20px; 
                    text-align: center; 
                }}
                .header h1 {{ 
                    margin: 0; 
                    font-size: 28px; 
                    font-weight: 300; 
                }}
                .header h2 {{ 
                    margin: 10px 0 0 0; 
                    font-size: 18px; 
                    font-weight: 400; 
                    opacity: 0.9; 
                }}
                .content {{ 
                    padding: 40px 30px; 
                    background-color: white; 
                }}
                .content p {{ 
                    margin: 0 0 20px 0; 
                    font-size: 16px; 
                }}
                .button {{ 
                    display: inline-block; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white; 
                    padding: 15px 30px; 
                    text-decoration: none; 
                    border-radius: 6px; 
                    margin: 25px 0;
                    font-weight: 500;
                    font-size: 16px;
                    transition: all 0.3s ease;
                }}
                .button:hover {{ 
                    transform: translateY(-2px); 
                    box-shadow: 0 5px 15px rgba(102,126,234,0.4); 
                }}
                .link-box {{ 
                    word-break: break-all; 
                    background-color: #f8f9fa; 
                    padding: 15px; 
                    border-radius: 6px; 
                    border-left: 4px solid #667eea; 
                    font-family: 'Courier New', monospace; 
                    font-size: 14px; 
                    color: #495057;
                }}
                .warning {{ 
                    background-color: #fff3cd; 
                    border: 1px solid #ffeaa7; 
                    color: #856404; 
                    padding: 15px; 
                    border-radius: 6px; 
                    margin: 20px 0; 
                }}
                .warning strong {{ 
                    color: #d63031; 
                }}
                .security-info {{ 
                    background-color: #e3f2fd; 
                    border: 1px solid #bbdefb; 
                    padding: 15px; 
                    border-radius: 6px; 
                    margin: 20px 0; 
                    color: #0d47a1; 
                }}
                .footer {{ 
                    padding: 30px 20px; 
                    text-align: center; 
                    background-color: #f8f9fa; 
                    color: #6c757d; 
                    font-size: 14px; 
                    line-height: 1.5; 
                }}
                .footer p {{ 
                    margin: 5px 0; 
                }}
                .divider {{ 
                    height: 1px; 
                    background-color: #e9ecef; 
                    margin: 20px 0; 
                }}
                @media only screen and (max-width: 600px) {{
                    .container {{ margin: 10px; }}
                    .content {{ padding: 30px 20px; }}
                    .header {{ padding: 25px 15px; }}
                    .button {{ padding: 12px 25px; font-size: 15px; }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🏧 ATM Monitoring Dashboard</h1>
                    <h2>Secure Password Reset</h2>
                </div>
                <div class="content">
                    <p>Dear <strong>{username}</strong>,</p>
                    
                    <p>We received a request to reset your password for the <strong>ATM Monitoring Dashboard</strong> system. This secure system manages critical ATM infrastructure monitoring and requires verified access.</p>
                    
                    <p>To proceed with resetting your password, please click the button below:</p>
                    
                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">🔐 Reset My Password</a>
                    </p>
                    
                    <p>If the button doesn't work, you can copy and paste this secure link into your browser:</p>
                    <div class="link-box">{reset_link}</div>
                    
                    <div class="warning">
                        <strong>⏰ Important Security Notice:</strong><br>
                        • This link will expire in <strong>24 hours</strong> for security reasons<br>
                        • You can only use this link <strong>once</strong><br>
                        • The link is valid only for your account: <strong>{username}</strong>
                    </div>
                    
                    <div class="security-info">
                        <strong>🛡️ Security Information:</strong><br>
                        If you did <strong>not</strong> request this password reset:
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>Please ignore this email - your password remains secure</li>
                            <li>Consider changing your password if you suspect unauthorized access</li>
                            <li>Contact your system administrator if this continues</li>
                        </ul>
                    </div>
                    
                    <div class="divider"></div>
                    
                    <p style="font-size: 14px; color: #6c757d;">
                        <strong>Request Details:</strong><br>
                        • User Account: {username}<br>
                        • Service: ATM Monitoring Dashboard<br>
                        • Request Time: System generated timestamp<br>
                        • Expires: 24 hours from generation
                    </p>
                </div>
                <div class="footer">
                    <p><strong>ATM Monitoring Dashboard Team</strong></p>
                    <p>Timor-Leste Banking Infrastructure Monitoring</p>
                    <p style="margin-top: 15px; font-size: 12px; opacity: 0.8;">
                        This is an automated security email. Please do not reply to this message.<br>
                        For technical support, contact your system administrator.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_password_reset_text(self, username: str, reset_link: str) -> str:
        """Get plain text template for password reset email"""
        return f"""
==========================================================
🏧 ATM MONITORING DASHBOARD - PASSWORD RESET REQUEST
==========================================================

Dear {username},

We received a request to reset your password for the ATM Monitoring Dashboard system. This secure system manages critical ATM infrastructure monitoring and requires verified access.

RESET YOUR PASSWORD:
{reset_link}

⏰ IMPORTANT SECURITY NOTICE:
• This link will expire in 24 hours for security reasons
• You can only use this link once
• The link is valid only for your account: {username}

🛡️ SECURITY INFORMATION:
If you did NOT request this password reset:
- Please ignore this email - your password remains secure
- Consider changing your password if you suspect unauthorized access
- Contact your system administrator if this continues

REQUEST DETAILS:
• User Account: {username}
• Service: ATM Monitoring Dashboard
• Request Time: System generated timestamp
• Expires: 24 hours from generation

==========================================================
ATM Monitoring Dashboard Team
Timor-Leste Banking Infrastructure Monitoring

This is an automated security email. Please do not reply to this message.
For technical support, contact your system administrator.
==========================================================
        """

# Global email service instance
email_service = EmailService()
