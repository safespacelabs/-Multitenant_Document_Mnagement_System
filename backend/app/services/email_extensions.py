"""
Extended email service functionality for e-signatures, notifications, and system admin
"""
from .email_service import EmailService
from typing import Optional, List, Dict, Any
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import ssl


class ExtendedEmailService(EmailService):
    """Extended email service with comprehensive functionality"""
    
    def _send_email_with_retry(self, recipient_email: str, message_obj, email_type: str = "email") -> bool:
        """Helper method to send email with proper error handling and debugging"""
        import ssl
        import smtplib
        
        context = ssl.create_default_context()
        
        # Debug connection info
        print(f"📧 Attempting to send {email_type} via {self.smtp_server}:{self.smtp_port}")
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
            server.sendmail(self.sender_email, recipient_email, message_obj.as_string())
            print(f"✅ Email sent successfully")
            
            server.quit()
            print(f"✅ {email_type} sent to {recipient_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ SMTP Authentication failed: {str(e)}")
            print(f"💡 Check your email credentials in .env file")
            if server:
                try:
                    server.quit()
                except:
                    pass
            return False
            
        except smtplib.SMTPConnectError as e:
            print(f"❌ SMTP Connection failed: {str(e)}")
            print(f"💡 Check your SMTP server settings: {self.smtp_server}:{self.smtp_port}")
            return False
            
        except smtplib.SMTPException as e:
            print(f"❌ SMTP Error: {str(e)}")
            if server:
                try:
                    server.quit()
                except:
                    pass
            return False
            
        except Exception as e:
            print(f"❌ Failed to send {email_type} to {recipient_email}: {str(e)}")
            print(f"💡 Full error: {type(e).__name__}: {str(e)}")
            return False
    
    async def send_esignature_completion_email(
        self,
        recipient_email: str,
        recipient_name: str,
        document_title: str,
        company_name: str,
        signer_name: str,
        signer_role: str,
        signed_document_url: str,
        completion_date: str,
        app_url: Optional[str] = None
    ) -> bool:
        """Send email notification when document is signed and completed"""
        try:
            app_base_url = app_url or self.app_url
            
            # Create message
            message_obj = MIMEMultipart("alternative")
            message_obj["Subject"] = f"✅ Document Signed: {document_title}"
            message_obj["From"] = f"{self.sender_name} <{self.sender_email}>"
            message_obj["To"] = recipient_email
            
            # Create HTML and text content
            html_content = self._create_esignature_completion_html(
                recipient_name=recipient_name,
                document_title=document_title,
                company_name=company_name,
                signer_name=signer_name,
                signer_role=signer_role,
                signed_document_url=signed_document_url,
                completion_date=completion_date
            )
            
            text_content = self._create_esignature_completion_text(
                recipient_name=recipient_name,
                document_title=document_title,
                company_name=company_name,
                signer_name=signer_name,
                signer_role=signer_role,
                signed_document_url=signed_document_url,
                completion_date=completion_date
            )
            
            # Attach parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message_obj.attach(text_part)
            message_obj.attach(html_part)
            
            # Send email using helper method
            return self._send_email_with_retry(recipient_email, message_obj, "e-signature completion email")
            
        except Exception as e:
            print(f"❌ Failed to send signature completion email to {recipient_email}: {str(e)}")
            return False

    async def send_esignature_request_email(
        self,
        recipient_email: str,
        recipient_name: str,
        document_title: str,
        company_name: str,
        sender_name: str,
        signing_url: str,
        message: Optional[str] = None,
        expires_in_days: int = 14,
        app_url: Optional[str] = None
    ) -> bool:
        """Send e-signature request email"""
        try:
            app_base_url = app_url or self.app_url
            
            # Create message
            message_obj = MIMEMultipart("alternative")
            message_obj["Subject"] = f"📝 Signature Required: {document_title}"
            message_obj["From"] = f"{self.sender_name} <{self.sender_email}>"
            message_obj["To"] = recipient_email
            
            # Create HTML and text content
            html_content = self._create_esignature_html(
                recipient_name=recipient_name,
                document_title=document_title,
                company_name=company_name,
                sender_name=sender_name,
                signing_url=signing_url,
                custom_message=message,
                expires_in_days=expires_in_days
            )
            
            text_content = self._create_esignature_text(
                recipient_name=recipient_name,
                document_title=document_title,
                company_name=company_name,
                sender_name=sender_name,
                signing_url=signing_url,
                custom_message=message,
                expires_in_days=expires_in_days
            )
            
            # Attach parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message_obj.attach(text_part)
            message_obj.attach(html_part)
            
            # Use the reliable send method with proper connection handling
            success = self._send_email_with_retry(recipient_email, message_obj, "E-signature request")
            
            if success:
                print(f"✅ E-signature request email sent to {recipient_email}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to send e-signature email to {recipient_email}: {str(e)}")
            return False

    async def send_document_notification_email(
        self,
        recipient_email: str,
        recipient_name: str,
        document_name: str,
        action: str,  # "uploaded", "shared", "updated", "deleted"
        company_name: str,
        sender_name: str,
        document_url: Optional[str] = None,
        app_url: Optional[str] = None
    ) -> bool:
        """Send document-related notification emails"""
        try:
            app_base_url = app_url or self.app_url
            
            # Create subject based on action
            action_subjects = {
                "uploaded": f"📄 New Document: {document_name}",
                "shared": f"📤 Document Shared: {document_name}",
                "updated": f"🔄 Document Updated: {document_name}",
                "deleted": f"🗑️ Document Deleted: {document_name}"
            }
            subject = action_subjects.get(action, f"📄 Document Notification: {document_name}")
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = recipient_email
            
            # Create content
            html_content = self._create_document_notification_html(
                recipient_name=recipient_name,
                document_name=document_name,
                action=action,
                company_name=company_name,
                sender_name=sender_name,
                document_url=document_url or f"{app_base_url}/dashboard"
            )
            
            text_content = self._create_document_notification_text(
                recipient_name=recipient_name,
                document_name=document_name,
                action=action,
                company_name=company_name,
                sender_name=sender_name,
                document_url=document_url or f"{app_base_url}/dashboard"
            )
            
            # Attach parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Use the reliable send method with proper connection handling
            success = self._send_email_with_retry(recipient_email, message, "Document notification")
            
            if success:
                print(f"✅ Document notification email sent to {recipient_email}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to send document notification to {recipient_email}: {str(e)}")
            return False

    async def send_system_admin_notification(
        self,
        recipient_email: str,
        recipient_name: str,
        subject: str,
        notification_type: str,  # "company_created", "user_registered", "system_alert"
        details: Dict[str, Any],
        app_url: Optional[str] = None
    ) -> bool:
        """Send system admin notifications"""
        try:
            app_base_url = app_url or self.app_url
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"🔧 System Admin: {subject}"
            message["From"] = f"{self.sender_name} <{self.sender_email}>"
            message["To"] = recipient_email
            
            # Create content
            html_content = self._create_system_admin_html(
                recipient_name=recipient_name,
                subject=subject,
                notification_type=notification_type,
                details=details,
                app_base_url=app_base_url
            )
            
            text_content = self._create_system_admin_text(
                recipient_name=recipient_name,
                subject=subject,
                notification_type=notification_type,
                details=details,
                app_base_url=app_base_url
            )
            
            # Attach parts
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Use the reliable send method with proper connection handling
            success = self._send_email_with_retry(recipient_email, message, "System admin notification")
            
            if success:
                print(f"✅ System admin notification sent to {recipient_email}")
            
            return success
            
        except Exception as e:
            print(f"❌ Failed to send system admin notification to {recipient_email}: {str(e)}")
            return False

    def _create_esignature_html(
        self,
        recipient_name: str,
        document_title: str,
        company_name: str,
        sender_name: str,
        signing_url: str,
        custom_message: Optional[str],
        expires_in_days: int
    ) -> str:
        """Create HTML template for e-signature requests"""
        custom_msg_html = f"""
        <div style="background: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin: 20px 0;">
            <p style="margin: 0; font-style: italic; color: #495057;">"{custom_message}"</p>
        </div>
        """ if custom_message else ""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Signature Request - {document_title}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">📝 Signature Required</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px;">{document_title}</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                <p style="font-size: 18px; margin-bottom: 20px;">Hi <strong>{recipient_name}</strong>,</p>
                
                <p style="margin-bottom: 20px;">
                    <strong>{sender_name}</strong> from <strong>{company_name}</strong> has requested your 
                    signature on the document: <strong>"{document_title}"</strong>
                </p>
                
                {custom_msg_html}
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{signing_url}" 
                       style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; 
                              border-radius: 5px; font-size: 18px; font-weight: bold; display: inline-block;">
                        ✍️ Sign Document
                    </a>
                </div>
                
                <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #856404;">
                        ⏰ <strong>Deadline:</strong> Please sign within <strong>{expires_in_days} days</strong>
                    </p>
                </div>
                
                <h3 style="color: #495057;">Next Steps:</h3>
                <ol style="color: #6c757d;">
                    <li>Click "Sign Document" to review the document</li>
                    <li>Verify the details are correct</li>
                    <li>Add your digital signature</li>
                    <li>Submit to complete the process</li>
                </ol>
                
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #6c757d;">
                    Having trouble with the button? Copy and paste this link into your browser:<br>
                    <a href="{signing_url}" style="color: #007bff;">{signing_url}</a>
                </p>
                
                <p style="font-size: 14px; color: #6c757d; margin-top: 30px;">
                    Best regards,<br>
                    {sender_name}<br>
                    {company_name}
                </p>
            </div>
        </body>
        </html>
        """

    def _create_esignature_text(
        self,
        recipient_name: str,
        document_title: str,
        company_name: str,
        sender_name: str,
        signing_url: str,
        custom_message: Optional[str],
        expires_in_days: int
    ) -> str:
        """Create plain text template for e-signature requests"""
        custom_msg_text = f'\n\nMessage from {sender_name}:\n"{custom_message}"\n' if custom_message else ""
        
        return f"""
📝 SIGNATURE REQUIRED: {document_title}

Hi {recipient_name},

{sender_name} from {company_name} has requested your signature on the document: "{document_title}"
{custom_msg_text}
TO SIGN THE DOCUMENT:
Visit: {signing_url}

⏰ DEADLINE: Please sign within {expires_in_days} days

Next Steps:
1. Click the link above to review the document
2. Verify the details are correct  
3. Add your digital signature
4. Submit to complete the process

If you have any questions, please contact {sender_name}.

Best regards,
{sender_name}
{company_name}

---
Having trouble? Copy and paste this link into your browser:
{signing_url}
        """

    def _create_document_notification_html(
        self,
        recipient_name: str,
        document_name: str,
        action: str,
        company_name: str,
        sender_name: str,
        document_url: str
    ) -> str:
        """Create HTML template for document notifications"""
        action_colors = {
            "uploaded": "#007bff",
            "shared": "#28a745", 
            "updated": "#ffc107",
            "deleted": "#dc3545"
        }
        
        action_icons = {
            "uploaded": "📄",
            "shared": "📤",
            "updated": "🔄", 
            "deleted": "🗑️"
        }
        
        color = action_colors.get(action, "#007bff")
        icon = action_icons.get(action, "📄")
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Document {action.title()}: {document_name}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: {color}; padding: 20px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">{icon} Document {action.title()}</h1>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                <p style="font-size: 18px; margin-bottom: 20px;">Hi <strong>{recipient_name}</strong>,</p>
                
                <p style="margin-bottom: 20px;">
                    <strong>{sender_name}</strong> has {action} the document: <strong>"{document_name}"</strong>
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{document_url}" 
                       style="background: {color}; color: white; padding: 12px 25px; text-decoration: none; 
                              border-radius: 5px; font-size: 16px; font-weight: bold; display: inline-block;">
                        📂 View Documents
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #6c757d; margin-top: 30px;">
                    Best regards,<br>
                    {company_name} Team
                </p>
            </div>
        </body>
        </html>
        """

    def _create_document_notification_text(
        self,
        recipient_name: str,
        document_name: str,
        action: str,
        company_name: str,
        sender_name: str,
        document_url: str
    ) -> str:
        """Create plain text template for document notifications"""
        return f"""
DOCUMENT {action.upper()}: {document_name}

Hi {recipient_name},

{sender_name} has {action} the document: "{document_name}"

To view your documents, visit: {document_url}

Best regards,
{company_name} Team
        """

    def _create_system_admin_html(
        self,
        recipient_name: str,
        subject: str,
        notification_type: str,
        details: Dict[str, Any],
        app_base_url: str
    ) -> str:
        """Create HTML template for system admin notifications"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>System Admin: {subject}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #6f42c1; padding: 20px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">🔧 System Admin Notification</h1>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                <p style="font-size: 18px; margin-bottom: 20px;">Hi <strong>{recipient_name}</strong>,</p>
                
                <h2 style="color: #495057;">{subject}</h2>
                
                <div style="background: white; border: 1px solid #dee2e6; border-radius: 5px; padding: 20px; margin: 20px 0;">
                    {"".join([f"<p><strong>{k}:</strong> {v}</p>" for k, v in details.items()])}
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{app_base_url}/system-dashboard" 
                       style="background: #6f42c1; color: white; padding: 12px 25px; text-decoration: none; 
                              border-radius: 5px; font-size: 16px; font-weight: bold; display: inline-block;">
                        🖥️ Go to System Dashboard
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #6c757d; margin-top: 30px;">
                    Best regards,<br>
                    System Administration
                </p>
            </div>
        </body>
        </html>
        """

    def _create_system_admin_text(
        self,
        recipient_name: str,
        subject: str,
        notification_type: str,
        details: Dict[str, Any],
        app_base_url: str
    ) -> str:
        """Create plain text template for system admin notifications"""
        details_text = "\n".join([f"{k}: {v}" for k, v in details.items()])
        
        return f"""
🔧 SYSTEM ADMIN NOTIFICATION

Hi {recipient_name},

{subject}

Details:
{details_text}

Go to System Dashboard: {app_base_url}/system-dashboard

Best regards,
System Administration
        """

    def _create_esignature_completion_html(
        self,
        recipient_name: str,
        document_title: str,
        company_name: str,
        signer_name: str,
        signer_role: str,
        signed_document_url: str,
        completion_date: str
    ) -> str:
        """Create HTML template for e-signature completion notifications"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Document Signed - {document_title}</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 30px; text-align: center; color: white; border-radius: 10px 10px 0 0;">
                <h1 style="margin: 0; font-size: 28px;">✅ Document Signed!</h1>
                <p style="margin: 10px 0 0 0; font-size: 18px;">{document_title}</p>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                <p style="font-size: 18px; margin-bottom: 20px;">Hi <strong>{recipient_name}</strong>,</p>
                
                <p style="margin-bottom: 20px;">
                    Great news! <strong>{signer_name}</strong> ({signer_role}) has successfully signed your document: 
                    <strong>"{document_title}"</strong>
                </p>
                
                <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 5px; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0; color: #155724;">
                        📅 <strong>Signed on:</strong> {completion_date}<br>
                        👤 <strong>Signed by:</strong> {signer_name} ({signer_role})<br>
                        🏢 <strong>Company:</strong> {company_name}
                    </p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{signed_document_url}" 
                       style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; 
                              border-radius: 5px; font-size: 18px; font-weight: bold; display: inline-block;">
                        📄 Download Signed Document
                    </a>
                </div>
                
                <h3 style="color: #495057;">What's Next?</h3>
                <ol style="color: #6c757d;">
                    <li>Download the signed document using the button above</li>
                    <li>Save it to your records</li>
                    <li>Share with relevant stakeholders if needed</li>
                    <li>The signing process is now complete!</li>
                </ol>
                
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #6c757d;">
                    Having trouble with the button? Copy and paste this link into your browser:<br>
                    <a href="{signed_document_url}" style="color: #007bff;">{signed_document_url}</a>
                </p>
                
                <p style="font-size: 14px; color: #6c757d; margin-top: 30px;">
                    Best regards,<br>
                    {company_name} Document Management Team
                </p>
            </div>
        </body>
        </html>
        """

    def _create_esignature_completion_text(
        self,
        recipient_name: str,
        document_title: str,
        company_name: str,
        signer_name: str,
        signer_role: str,
        signed_document_url: str,
        completion_date: str
    ) -> str:
        """Create plain text template for e-signature completion notifications"""
        return f"""
✅ DOCUMENT SIGNED: {document_title}

Hi {recipient_name},

Great news! {signer_name} ({signer_role}) has successfully signed your document: "{document_title}"

SIGNING DETAILS:
📅 Signed on: {completion_date}
👤 Signed by: {signer_name} ({signer_role})
🏢 Company: {company_name}

DOWNLOAD SIGNED DOCUMENT:
{signed_document_url}

What's Next?
1. Download the signed document using the link above
2. Save it to your records
3. Share with relevant stakeholders if needed
4. The signing process is now complete!

Best regards,
{company_name} Document Management Team

---
Having trouble? Copy and paste this link into your browser:
{signed_document_url}
        """


# Create factory function for different contexts
def get_extended_email_service(company_name: Optional[str] = None) -> ExtendedEmailService:
    """Get extended email service instance for specific company or system-wide"""
    return ExtendedEmailService(company_name)


# Create global instances
extended_email_service = ExtendedEmailService()