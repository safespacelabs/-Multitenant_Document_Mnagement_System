import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
import os
from datetime import datetime


class EmailService:
    def __init__(self, company_name: Optional[str] = None):
        # Email configuration - you can set these as environment variables
        self.smtp_server = os.getenv("SMTP_SERVER") or "smtp.gmail.com"
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL") or "your-app@example.com"
        self.sender_password = os.getenv("SENDER_PASSWORD") or "your-app-password"
        self.sender_name = os.getenv("SENDER_NAME") or company_name or "Document Management System"
        self.app_url = os.getenv("APP_URL") or "http://localhost:3000"
        
        # Default company name for system-wide emails
        self.default_company_name = company_name or "Document Management System"
        
    async def send_invitation_email(
        self, 
        recipient_email: str,
        recipient_name: str,
        company_name: str,
        role: str,
        unique_id: str,
        expires_at: datetime,
        invited_by: str,
        app_url: Optional[str] = None
    ) -> bool:
        """Send invitation email to new user"""
        try:
            # Create the invitation link
            app_base_url = app_url or self.app_url
            setup_link = f"{app_base_url}/setup-password/{unique_id}"
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"You've been invited to join {company_name}!"
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = recipient_email
            
            # Create HTML email template
            html_content = self._create_invitation_html(
                recipient_name=recipient_name,
                company_name=company_name,
                role=role,
                setup_link=setup_link,
                expires_at=expires_at,
                invited_by=invited_by
            )
            
            # Create plain text version
            text_content = self._create_invitation_text(
                recipient_name=recipient_name,
                company_name=company_name,
                role=role,
                setup_link=setup_link,
                expires_at=expires_at,
                invited_by=invited_by
            )
            
            # Attach parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email with better error handling
            context = ssl.create_default_context()
            
            # Debug connection info
            print(f"📧 Attempting to send email via {self.smtp_server}:{self.smtp_port}")
            print(f"📧 From: {self.sender_email} to: {recipient_email}")
            
            server = None
            try:
                # Create SMTP connection
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                print(f"✅ SMTP connection established")
                
                # Start TLS
                server.starttls(context=context)
                print(f"✅ TLS started")
                
                # Login
                server.login(self.sender_email, self.sender_password)
                print(f"✅ SMTP login successful")
                
                # Send email
                server.sendmail(self.sender_email, recipient_email, message.as_string())
                print(f"✅ Email sent successfully")
                
                server.quit()
                print(f"✅ Invitation email sent to {recipient_email}")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                print(f"❌ SMTP Authentication failed: {str(e)}")
                print(f"💡 Check your email credentials in .env file")
                if server:
                    server.quit()
                return False
                
            except smtplib.SMTPConnectError as e:
                print(f"❌ SMTP Connection failed: {str(e)}")
                print(f"💡 Check your SMTP server settings: {self.smtp_server}:{self.smtp_port}")
                return False
                
            except smtplib.SMTPException as e:
                print(f"❌ SMTP Error: {str(e)}")
                if server:
                    server.quit()
                return False
            
        except Exception as e:
            print(f"❌ Failed to send invitation email to {recipient_email}: {str(e)}")
            print(f"💡 Full error: {type(e).__name__}: {str(e)}")
            return False
    
    def _create_invitation_html(
        self, 
        recipient_name: str,
        company_name: str, 
        role: str,
        setup_link: str,
        expires_at: datetime,
        invited_by: str
    ) -> str:
        """Create HTML email template"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Invitation to {company_name}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">🎉 You're Invited!</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px;">Join {company_name}</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                <p style="font-size: 18px; margin-bottom: 20px;">Hi <strong>{recipient_name}</strong>,</p>
                
                <p style="margin-bottom: 20px;">
                    Great news! <strong>{invited_by}</strong> has invited you to join <strong>{company_name}</strong> 
                    as a <strong>{role.replace('_', ' ').title()}</strong> in our Document Management System.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{setup_link}" 
                       style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; 
                              border-radius: 5px; font-size: 18px; font-weight: bold; display: inline-block;">
                        🚀 Set Up Your Account
                    </a>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #856404;">
                        ⏰ <strong>Important:</strong> This invitation expires on 
                        <strong>{expires_at.strftime('%B %d, %Y at %I:%M %p')}</strong>
                    </p>
                </div>
                
                <h3 style="color: #495057;">What's Next?</h3>
                <ol style="color: #6c757d;">
                    <li>Click the "Set Up Your Account" button above</li>
                    <li>Create your username and secure password</li>
                    <li>Start managing and collaborating on documents!</li>
                </ol>
                
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #6c757d;">
                    Having trouble with the button? Copy and paste this link into your browser:<br>
                    <a href="{setup_link}" style="color: #007bff;">{setup_link}</a>
                </p>
                
                <p style="font-size: 14px; color: #6c757d; margin-top: 30px;">
                    Best regards,<br>
                    The {company_name} Team
                </p>
            </div>
        </body>
        </html>
        """
    
    def _create_invitation_text(
        self,
        recipient_name: str,
        company_name: str,
        role: str,
        setup_link: str,
        expires_at: datetime,
        invited_by: str
    ) -> str:
        """Create plain text email template"""
        return f"""
Hi {recipient_name},

Great news! {invited_by} has invited you to join {company_name} as a {role.replace('_', ' ').title()} in our Document Management System.

TO SET UP YOUR ACCOUNT:
Visit this link: {setup_link}

IMPORTANT: This invitation expires on {expires_at.strftime('%B %d, %Y at %I:%M %p')}

What's Next?
1. Click the link above to set up your account
2. Create your username and secure password  
3. Start managing and collaborating on documents!

If you have any questions, please contact your administrator.

Best regards,
The {company_name} Team

---
Having trouble? Copy and paste this link into your browser:
{setup_link}
        """


# Create a global instance
email_service = EmailService()