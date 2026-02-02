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

    async def send_user_invitation(
        self,
        to_email: str,
        company_name: str,
        inviter_name: str,
        role: str,
        invitation_link: str
    ) -> bool:
        """
        Send user invitation email (simplified interface)
        This method matches the signature used in user_management.py
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"You've been invited to join {company_name}!"
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = to_email

            # Create HTML email template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Invitation to {company_name}</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">You're Invited!</h1>
                    <p style="margin: 10px 0 0 0; font-size: 18px;">Join {company_name}</p>
                </div>

                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <p style="font-size: 18px; margin-bottom: 20px;">Hello!</p>

                    <p style="margin-bottom: 20px;">
                        <strong>{inviter_name}</strong> has invited you to join <strong>{company_name}</strong>
                        as a <strong>{role.replace('_', ' ').title()}</strong> in the Document Management System.
                    </p>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{invitation_link}"
                           style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none;
                                  border-radius: 5px; font-size: 18px; font-weight: bold; display: inline-block;">
                            Set Up Your Account
                        </a>
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
                        <a href="{invitation_link}" style="color: #007bff;">{invitation_link}</a>
                    </p>

                    <p style="font-size: 14px; color: #6c757d; margin-top: 30px;">
                        Best regards,<br>
                        The {company_name} Team
                    </p>
                </div>
            </body>
            </html>
            """

            # Create plain text version
            text_content = f"""
Hello!

{inviter_name} has invited you to join {company_name} as a {role.replace('_', ' ').title()} in the Document Management System.

TO SET UP YOUR ACCOUNT:
Visit this link: {invitation_link}

What's Next?
1. Click the link above to set up your account
2. Create your username and secure password
3. Start managing and collaborating on documents!

If you have any questions, please contact your administrator.

Best regards,
The {company_name} Team

---
Having trouble? Copy and paste this link into your browser:
{invitation_link}
            """

            # Attach parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")

            message.attach(text_part)
            message.attach(html_part)

            # Send email with better error handling
            context = ssl.create_default_context()

            # Debug connection info
            print(f"[EMAIL] Attempting to send invitation via {self.smtp_server}:{self.smtp_port}")
            print(f"[EMAIL] From: {self.sender_email} to: {to_email}")

            server = None
            try:
                # Create SMTP connection
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                print(f"[OK] SMTP connection established")

                # Start TLS
                server.starttls(context=context)
                print(f"[OK] TLS started")

                # Login
                server.login(self.sender_email, self.sender_password)
                print(f"[OK] SMTP login successful")

                # Send email
                server.sendmail(self.sender_email, to_email, message.as_string())
                print(f"[OK] Email sent successfully to {to_email}")

                server.quit()
                return True

            except smtplib.SMTPAuthenticationError as e:
                print(f"[ERROR] SMTP Authentication failed: {str(e)}")
                print(f"[INFO] Check your email credentials in .env file")
                if server:
                    server.quit()
                return False

            except smtplib.SMTPConnectError as e:
                print(f"[ERROR] SMTP Connection failed: {str(e)}")
                print(f"[INFO] Check your SMTP server settings: {self.smtp_server}:{self.smtp_port}")
                return False

            except smtplib.SMTPException as e:
                print(f"[ERROR] SMTP Error: {str(e)}")
                if server:
                    server.quit()
                return False

        except Exception as e:
            print(f"[ERROR] Failed to send invitation email to {to_email}: {str(e)}")
            print(f"[INFO] Full error: {type(e).__name__}: {str(e)}")
            return False


    async def send_expiry_alert(
        self,
        user_email: str,
        user_name: str,
        document: Dict[str, Any],
        reasons: List[Dict[str, Any]],
        company_name: str = "Document Management System"
    ) -> bool:
        """Send urgent expiry alert for documents expiring within 7 days"""
        try:
            days_until_expiry = document.get('days_until_expiry', 0)
            expiry_date = document.get('expiry_date', 'Unknown')
            document_name = document.get('document_name', 'Unknown Document')
            document_type = document.get('document_type', 'Document')

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"URGENT: Your {document_type} expires in {days_until_expiry} days!"
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = user_email

            # Build reasons HTML
            reasons_html = ""
            for reason in reasons:
                reason_type = reason.get('type', 'info')
                reason_msg = reason.get('message', '')
                icon = "⚠️" if reason_type == 'compliance' else "⚡" if reason_type == 'legal' else "📝"
                reasons_html += f"<li style='margin: 10px 0;'>{icon} {reason_msg}</li>"

            recommended_action = document.get('recommended_action', 'Please take action to renew this document.')

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Document Expiry Alert</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">🚨 Urgent: Document Expiring Soon</h1>
                    <p style="margin: 10px 0 0 0; font-size: 18px;">{days_until_expiry} days remaining</p>
                </div>

                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <p style="font-size: 18px; margin-bottom: 20px;">Hi <strong>{user_name}</strong>,</p>

                    <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 20px; margin: 20px 0;">
                        <p style="margin: 0; font-size: 16px;">
                            <strong>📄 Document:</strong> {document_name}<br>
                            <strong>📋 Type:</strong> {document_type}<br>
                            <strong>📅 Expiry Date:</strong> {expiry_date}
                        </p>
                    </div>

                    <h3 style="color: #dc3545;">Why This Matters:</h3>
                    <ul style="color: #6c757d; padding-left: 20px;">
                        {reasons_html}
                    </ul>

                    <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
                        <p style="margin: 0; color: #155724;">
                            <strong>💡 Recommended Action:</strong><br>
                            {recommended_action}
                        </p>
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{self.app_url}/documents"
                           style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none;
                                  border-radius: 5px; font-size: 18px; font-weight: bold; display: inline-block;">
                            📂 View My Documents
                        </a>
                    </div>

                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">

                    <p style="font-size: 14px; color: #6c757d; margin-top: 30px;">
                        Best regards,<br>
                        The {company_name} HR Team
                    </p>
                </div>
            </body>
            </html>
            """

            text_content = f"""
Hi {user_name},

URGENT: Your document is expiring soon!

Document: {document_name}
Type: {document_type}
Expiry Date: {expiry_date}
Days Remaining: {days_until_expiry}

Recommended Action: {recommended_action}

Please log in to your account to take action: {self.app_url}/documents

Best regards,
The {company_name} HR Team
            """

            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")

            message.attach(text_part)
            message.attach(html_part)

            return await self._send_email(user_email, message)

        except Exception as e:
            print(f"[ERROR] Failed to send expiry alert to {user_email}: {str(e)}")
            return False

    async def send_expiry_digest(
        self,
        user_email: str,
        user_name: str,
        documents: List[Dict[str, Any]],
        company_name: str = "Document Management System"
    ) -> bool:
        """Send daily digest of documents expiring in 8-30 days"""
        try:
            if not documents:
                return True

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"Document Expiry Digest: {len(documents)} documents need attention"
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = user_email

            # Build documents table HTML
            docs_html = ""
            for doc in documents:
                days = doc.get('days_until_expiry', 0)
                urgency_color = "#dc3545" if days <= 14 else "#ffc107" if days <= 30 else "#28a745"
                docs_html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">{doc.get('document_name', 'Unknown')}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">{doc.get('document_type', 'Document')}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #dee2e6;">{doc.get('expiry_date', 'Unknown')}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #dee2e6; color: {urgency_color}; font-weight: bold;">{days} days</td>
                </tr>
                """

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Document Expiry Digest</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%); padding: 30px; text-align: center; color: #212529; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">📋 Document Expiry Digest</h1>
                    <p style="margin: 10px 0 0 0; font-size: 18px;">{len(documents)} documents need attention</p>
                </div>

                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <p style="font-size: 18px; margin-bottom: 20px;">Hi <strong>{user_name}</strong>,</p>

                    <p>The following documents are expiring soon and require your attention:</p>

                    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                        <thead>
                            <tr style="background: #e9ecef;">
                                <th style="padding: 10px; text-align: left;">Document</th>
                                <th style="padding: 10px; text-align: left;">Type</th>
                                <th style="padding: 10px; text-align: left;">Expiry Date</th>
                                <th style="padding: 10px; text-align: left;">Days Left</th>
                            </tr>
                        </thead>
                        <tbody>
                            {docs_html}
                        </tbody>
                    </table>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{self.app_url}/documents"
                           style="background: #007bff; color: white; padding: 15px 30px; text-decoration: none;
                                  border-radius: 5px; font-size: 18px; font-weight: bold; display: inline-block;">
                            📂 Manage Documents
                        </a>
                    </div>

                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">

                    <p style="font-size: 14px; color: #6c757d;">
                        Best regards,<br>
                        The {company_name} HR Team
                    </p>
                </div>
            </body>
            </html>
            """

            text_content = f"""
Hi {user_name},

Document Expiry Digest - {len(documents)} documents need attention:

"""
            for doc in documents:
                text_content += f"- {doc.get('document_name')}: expires {doc.get('expiry_date')} ({doc.get('days_until_expiry')} days left)\n"

            text_content += f"""

Please log in to manage your documents: {self.app_url}/documents

Best regards,
The {company_name} HR Team
            """

            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")

            message.attach(text_part)
            message.attach(html_part)

            return await self._send_email(user_email, message)

        except Exception as e:
            print(f"[ERROR] Failed to send expiry digest to {user_email}: {str(e)}")
            return False

    async def send_hr_expiry_summary(
        self,
        hr_email: str,
        hr_name: str,
        company_expiries: List[Dict[str, Any]],
        company_name: str = "Document Management System",
        summary_type: str = "daily"
    ) -> bool:
        """Send HR admin summary of all company document expirations"""
        try:
            if not company_expiries:
                return True

            # Group by urgency
            urgent = [e for e in company_expiries if e.get('days_until_expiry', 0) <= 7]
            medium = [e for e in company_expiries if 7 < e.get('days_until_expiry', 0) <= 30]
            low = [e for e in company_expiries if e.get('days_until_expiry', 0) > 30]

            # Create message
            message = MIMEMultipart("alternative")
            subject_prefix = "Daily" if summary_type == "daily" else "Weekly"
            message["Subject"] = f"{subject_prefix} HR Expiry Summary: {len(urgent)} urgent, {len(medium)} upcoming"
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = hr_email

            # Build summary table
            def build_employee_rows(items):
                rows = ""
                for item in items[:20]:  # Limit to 20 per category
                    days = item.get('days_until_expiry', 0)
                    urgency_color = "#dc3545" if days <= 7 else "#ffc107" if days <= 30 else "#28a745"
                    rows += f"""
                    <tr>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{item.get('employee_name', 'Unknown')}</td>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{item.get('document_name', 'Unknown')}</td>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{item.get('document_type', 'Document')}</td>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6;">{item.get('expiry_date', 'Unknown')}</td>
                        <td style="padding: 8px; border-bottom: 1px solid #dee2e6; color: {urgency_color}; font-weight: bold;">{days} days</td>
                    </tr>
                    """
                return rows

            urgent_html = build_employee_rows(urgent) if urgent else "<tr><td colspan='5' style='padding: 10px; text-align: center; color: #28a745;'>No urgent expirations</td></tr>"
            medium_html = build_employee_rows(medium) if medium else "<tr><td colspan='5' style='padding: 10px; text-align: center; color: #6c757d;'>No upcoming expirations in this category</td></tr>"

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>HR Expiry Summary</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">📊 {subject_prefix} HR Expiry Summary</h1>
                    <p style="margin: 10px 0 0 0; font-size: 18px;">{company_name}</p>
                </div>

                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <p style="font-size: 18px; margin-bottom: 20px;">Hi <strong>{hr_name}</strong>,</p>

                    <div style="display: flex; gap: 20px; margin-bottom: 30px;">
                        <div style="flex: 1; background: #fff; border-radius: 10px; padding: 20px; text-align: center; border-left: 5px solid #dc3545;">
                            <h2 style="margin: 0; color: #dc3545; font-size: 36px;">{len(urgent)}</h2>
                            <p style="margin: 5px 0 0 0; color: #6c757d;">Urgent (≤7 days)</p>
                        </div>
                        <div style="flex: 1; background: #fff; border-radius: 10px; padding: 20px; text-align: center; border-left: 5px solid #ffc107;">
                            <h2 style="margin: 0; color: #ffc107; font-size: 36px;">{len(medium)}</h2>
                            <p style="margin: 5px 0 0 0; color: #6c757d;">Upcoming (8-30 days)</p>
                        </div>
                        <div style="flex: 1; background: #fff; border-radius: 10px; padding: 20px; text-align: center; border-left: 5px solid #28a745;">
                            <h2 style="margin: 0; color: #28a745; font-size: 36px;">{len(low)}</h2>
                            <p style="margin: 5px 0 0 0; color: #6c757d;">Future (31-90 days)</p>
                        </div>
                    </div>

                    <h3 style="color: #dc3545; border-bottom: 2px solid #dc3545; padding-bottom: 10px;">🚨 Urgent Actions Required (≤7 days)</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                        <thead>
                            <tr style="background: #e9ecef;">
                                <th style="padding: 8px; text-align: left;">Employee</th>
                                <th style="padding: 8px; text-align: left;">Document</th>
                                <th style="padding: 8px; text-align: left;">Type</th>
                                <th style="padding: 8px; text-align: left;">Expiry</th>
                                <th style="padding: 8px; text-align: left;">Days</th>
                            </tr>
                        </thead>
                        <tbody>
                            {urgent_html}
                        </tbody>
                    </table>

                    <h3 style="color: #ffc107; border-bottom: 2px solid #ffc107; padding-bottom: 10px;">⚠️ Upcoming Expirations (8-30 days)</h3>
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 30px;">
                        <thead>
                            <tr style="background: #e9ecef;">
                                <th style="padding: 8px; text-align: left;">Employee</th>
                                <th style="padding: 8px; text-align: left;">Document</th>
                                <th style="padding: 8px; text-align: left;">Type</th>
                                <th style="padding: 8px; text-align: left;">Expiry</th>
                                <th style="padding: 8px; text-align: left;">Days</th>
                            </tr>
                        </thead>
                        <tbody>
                            {medium_html}
                        </tbody>
                    </table>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{self.app_url}/hr-admin/expiry-dashboard"
                           style="background: #6c5ce7; color: white; padding: 15px 30px; text-decoration: none;
                                  border-radius: 5px; font-size: 18px; font-weight: bold; display: inline-block;">
                            📊 View Full Dashboard
                        </a>
                    </div>

                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">

                    <p style="font-size: 14px; color: #6c757d;">
                        This is an automated {summary_type} summary from your Document Management System.
                    </p>
                </div>
            </body>
            </html>
            """

            text_content = f"""
{subject_prefix} HR Expiry Summary - {company_name}

Hi {hr_name},

Summary:
- Urgent (≤7 days): {len(urgent)}
- Upcoming (8-30 days): {len(medium)}
- Future (31-90 days): {len(low)}

URGENT ACTIONS REQUIRED:
"""
            for item in urgent[:10]:
                text_content += f"- {item.get('employee_name')}: {item.get('document_name')} expires {item.get('expiry_date')}\n"

            text_content += f"""

View full dashboard: {self.app_url}/hr-admin/expiry-dashboard

Best regards,
Document Management System
            """

            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")

            message.attach(text_part)
            message.attach(html_part)

            return await self._send_email(hr_email, message)

        except Exception as e:
            print(f"[ERROR] Failed to send HR expiry summary to {hr_email}: {str(e)}")
            return False

    async def send_user_created_notification(
        self,
        user_email: str,
        user_name: str,
        created_by_name: str,
        company_name: str,
        role: str,
        temp_password: Optional[str] = None,
        setup_link: Optional[str] = None
    ) -> bool:
        """Send notification when HR creates a new user via chatbot"""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = f"Welcome to {company_name}! Your account has been created"
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = user_email

            setup_section = ""
            if setup_link:
                setup_section = f"""
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{setup_link}"
                       style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none;
                              border-radius: 5px; font-size: 18px; font-weight: bold; display: inline-block;">
                        🚀 Set Up Your Account
                    </a>
                </div>
                """
            elif temp_password:
                setup_section = f"""
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 20px; margin: 20px 0;">
                    <p style="margin: 0;">
                        <strong>Your temporary password:</strong> {temp_password}<br>
                        <small style="color: #856404;">Please change this password after your first login.</small>
                    </p>
                </div>
                """

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Welcome to {company_name}</title>
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
                <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                    <h1 style="margin: 0; font-size: 28px;">🎉 Welcome!</h1>
                    <p style="margin: 10px 0 0 0; font-size: 18px;">Your account has been created</p>
                </div>

                <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                    <p style="font-size: 18px; margin-bottom: 20px;">Hi <strong>{user_name}</strong>,</p>

                    <p>{created_by_name} has created an account for you at <strong>{company_name}</strong> as a <strong>{role.replace('_', ' ').title()}</strong>.</p>

                    <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 20px; margin: 20px 0;">
                        <p style="margin: 0;">
                            <strong>📧 Email:</strong> {user_email}<br>
                            <strong>👤 Role:</strong> {role.replace('_', ' ').title()}
                        </p>
                    </div>

                    {setup_section}

                    <p>You can now access the Document Management System and start managing your documents.</p>

                    <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">

                    <p style="font-size: 14px; color: #6c757d;">
                        Best regards,<br>
                        The {company_name} Team
                    </p>
                </div>
            </body>
            </html>
            """

            text_content = f"""
Welcome to {company_name}!

Hi {user_name},

{created_by_name} has created an account for you as a {role.replace('_', ' ').title()}.

Email: {user_email}
Role: {role}

"""
            if setup_link:
                text_content += f"Set up your account: {setup_link}\n"
            elif temp_password:
                text_content += f"Temporary password: {temp_password}\nPlease change this after your first login.\n"

            text_content += f"""

Best regards,
The {company_name} Team
            """

            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")

            message.attach(text_part)
            message.attach(html_part)

            return await self._send_email(user_email, message)

        except Exception as e:
            print(f"[ERROR] Failed to send user created notification to {user_email}: {str(e)}")
            return False

    async def _send_email(self, recipient_email: str, message: MIMEMultipart) -> bool:
        """Internal method to send email via SMTP"""
        context = ssl.create_default_context()

        print(f"[EMAIL] Attempting to send via {self.smtp_server}:{self.smtp_port}")
        print(f"[EMAIL] From: {self.sender_email} to: {recipient_email}")

        server = None
        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            print(f"[OK] SMTP connection established")

            server.starttls(context=context)
            print(f"[OK] TLS started")

            server.login(self.sender_email, self.sender_password)
            print(f"[OK] SMTP login successful")

            server.sendmail(self.sender_email, recipient_email, message.as_string())
            print(f"[OK] Email sent successfully to {recipient_email}")

            server.quit()
            return True

        except smtplib.SMTPAuthenticationError as e:
            print(f"[ERROR] SMTP Authentication failed: {str(e)}")
            if server:
                server.quit()
            return False

        except smtplib.SMTPConnectError as e:
            print(f"[ERROR] SMTP Connection failed: {str(e)}")
            return False

        except smtplib.SMTPException as e:
            print(f"[ERROR] SMTP Error: {str(e)}")
            if server:
                server.quit()
            return False


# Create a global instance
email_service = EmailService()