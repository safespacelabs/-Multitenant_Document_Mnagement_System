"""
Document Analysis Service for AI-powered document processing
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.services.anthropic_service import anthropic_service
from app.services.email_service import email_service
from app.models_document_analysis import DocumentAnalysis, ExpiryNotification
from app.models_company import User as CompanyUser, Document as CompanyDocument
from app.config import ANTHROPIC_API_KEY

class DocumentAnalysisService:
    def __init__(self):
        self.has_anthropic_key = bool(ANTHROPIC_API_KEY)
    
    async def process_document_upload(self, document_id: int, file_content: bytes, filename: str, folder_name: str, user_id: int, user_name: str, user_email: str, company_db: Session) -> Dict[str, Any]:
        """Process document upload with AI analysis"""
        try:
            # Check API key dynamically
            if not ANTHROPIC_API_KEY:
                return {
                    "success": False,
                    "error": "Anthropic API key not configured",
                    "analysis_id": None
                }
            
            # Extract metadata using Anthropic AI
            metadata = await anthropic_service.extract_document_metadata(
                file_content, filename, folder_name
            )
            
            # Debug: Print the metadata we're about to store
            print(f"🔍 Metadata to store: {metadata}")
            
            # Store analysis in database
            analysis = DocumentAnalysis(
                document_id=document_id,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                title=metadata.get('title'),
                summary=metadata.get('summary'),
                document_type=metadata.get('document_type'),
                folder_name=metadata.get('folder_name'),
                key_topics=metadata.get('key_topics', []),
                entities=metadata.get('entities', {}),
                keywords=metadata.get('keywords', []),
                language=metadata.get('language'),
                word_count=metadata.get('word_count'),
                sentiment=metadata.get('sentiment'),
                expiry_detected=metadata.get('expiry_detected', False),
                expiry_date=datetime.strptime(metadata['expiry_date'], '%Y-%m-%d').date() if metadata.get('expiry_date') else None,
                expiry_type=metadata.get('expiry_type'),
                urgency_level=metadata.get('urgency_level', 'low'),
                extracted_text=metadata.get('extracted_text'),
                important_notes=metadata.get('important_notes', []),
                compliance_requirements=metadata.get('compliance_requirements', []),
                document_sections=metadata.get('document_sections', []),
                key_findings=metadata.get('key_findings', []),
                data_points=metadata.get('data_points', []),
                action_items=metadata.get('action_items', []),
                extracted_at=datetime.utcnow(),
                ai_model=metadata.get('ai_model'),
                processing_status='success' if metadata.get('processing_status') == 'success' else 'failed',
                error_message=metadata.get('error')
            )
            
            print(f"🔍 Analysis object created with ai_model: {analysis.ai_model}")
            print(f"🔍 Analysis object created with processing_status: {analysis.processing_status}")
            
            company_db.add(analysis)
            company_db.commit()
            company_db.refresh(analysis)
            
            # Check for expiry and create notification if needed
            if metadata.get('expiry_detected') and metadata.get('expiry_date'):
                await self._create_expiry_notification(analysis, company_db)
            
            return {
                "success": True,
                "analysis_id": analysis.id,
                "metadata": metadata,
                "expiry_detected": metadata.get('expiry_detected', False)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "analysis_id": None
            }
    
    async def _create_expiry_notification(self, analysis: DocumentAnalysis, company_db: Session):
        """Create expiry notification for HR admins"""
        try:
            if not analysis.expiry_date:
                return
            
            # Some company schemas use string IDs (e.g., 'hrdoc_...').
            # Skip notification if the documents table expects an integer ID.
            try:
                # Attempt a lightweight cast check; if it fails, skip gracefully
                _ = int(str(analysis.document_id))
            except Exception:
                print("Skipping expiry notification: non-integer document_id detected; schema may require INT.")
                return
            
            # Calculate days until expiry
            today = date.today()
            days_until_expiry = (analysis.expiry_date - today).days
            
            # Only create notification if expiry is within 90 days
            if days_until_expiry > 90:
                return
            
            # Check if notification already exists
            existing_notification = company_db.query(ExpiryNotification).filter(
                and_(
                    ExpiryNotification.document_analysis_id == analysis.id,
                    ExpiryNotification.notification_status.in_(['pending', 'sent'])
                )
            ).first()
            
            if existing_notification:
                return  # Notification already exists
            
            # Create new notification
            notification = ExpiryNotification(
                document_analysis_id=analysis.id,
                document_id=analysis.document_id,
                user_id=analysis.user_id,
                user_name=analysis.user_name,
                user_email=analysis.user_email,
                notification_type='expiry_warning',
                expiry_date=analysis.expiry_date,
                days_until_expiry=days_until_expiry,
                urgency_level=analysis.urgency_level,
                notification_status='pending'
            )
            
            company_db.add(notification)
            company_db.commit()
            
            # Send notification email
            await self._send_expiry_notification(notification, analysis, company_db)
            
        except Exception as e:
            # Ensure failed insert does not poison the outer transaction
            try:
                company_db.rollback()
            except Exception:
                pass
            print(f"Error creating expiry notification: {str(e)}")
    
    async def _send_expiry_notification(self, notification: ExpiryNotification, analysis: DocumentAnalysis, company_db: Session):
        """Send expiry notification email to HR admins"""
        try:
            # Get HR admins for this company
            hr_admins = company_db.query(CompanyUser).filter(
                and_(
                    CompanyUser.role.in_(['hr_admin', 'hr_manager']),
                    CompanyUser.is_active == True
                )
            ).all()
            
            if not hr_admins:
                notification.notification_status = 'failed'
                notification.notification_message = "No HR admins found"
                company_db.commit()
                return
            
            # Prepare email content
            urgency_emoji = "🚨" if notification.urgency_level == "high" else "⚠️" if notification.urgency_level == "medium" else "ℹ️"
            
            subject = f"{urgency_emoji} Document Expiry Alert - {analysis.title}"
            
            body = f"""
            <h2>Document Expiry Alert</h2>
            
            <p><strong>Document:</strong> {analysis.title}</p>
            <p><strong>Type:</strong> {analysis.document_type}</p>
            <p><strong>Folder:</strong> {analysis.folder_name}</p>
            <p><strong>Expiry Date:</strong> {analysis.expiry_date}</p>
            <p><strong>Days Until Expiry:</strong> {notification.days_until_expiry}</p>
            <p><strong>Urgency Level:</strong> {notification.urgency_level.upper()}</p>
            
            <h3>Summary:</h3>
            <p>{analysis.summary}</p>
            
            <h3>Important Notes:</h3>
            <ul>
            {"".join([f"<li>{note}</li>" for note in analysis.important_notes])}
            </ul>
            
            <p><em>This is an automated notification from the Document Management System.</em></p>
            """
            
            # Send email to all HR admins
            recipient_emails = [admin.email for admin in hr_admins]
            
            email_sent = await email_service.send_email(
                to_emails=recipient_emails,
                subject=subject,
                body=body,
                is_html=True
            )
            
            if email_sent:
                notification.notification_status = 'sent'
                notification.notification_sent_at = datetime.utcnow()
                notification.notification_recipients = recipient_emails
                notification.notification_message = f"Email sent to {len(recipient_emails)} HR admins"
            else:
                notification.notification_status = 'failed'
                notification.notification_message = "Failed to send email"
            
            company_db.commit()
            
        except Exception as e:
            notification.notification_status = 'failed'
            notification.notification_message = f"Error: {str(e)}"
            company_db.commit()
            print(f"Error sending expiry notification: {str(e)}")
    
    def get_document_analysis(self, document_id: int, company_db: Session) -> Optional[DocumentAnalysis]:
        """Get document analysis by document ID"""
        return company_db.query(DocumentAnalysis).filter(
            DocumentAnalysis.document_id == document_id
        ).first()
    
    def search_documents_by_content(self, query: str, company_db: Session, limit: int = 10) -> List[DocumentAnalysis]:
        """Search documents by content using AI-extracted data"""
        try:
            # Search in extracted text, summary, and keywords
            results = company_db.query(DocumentAnalysis).filter(
                or_(
                    DocumentAnalysis.extracted_text.ilike(f"%{query}%"),
                    DocumentAnalysis.summary.ilike(f"%{query}%"),
                    DocumentAnalysis.title.ilike(f"%{query}%")
                )
            ).limit(limit).all()
            
            return results
            
        except Exception as e:
            print(f"Error searching documents: {str(e)}")
            return []
    
    def get_expiring_documents(self, company_db: Session, days_ahead: int = 30) -> List[DocumentAnalysis]:
        """Get documents expiring within specified days"""
        try:
            future_date = date.today() + timedelta(days=days_ahead)
            
            results = company_db.query(DocumentAnalysis).filter(
                and_(
                    DocumentAnalysis.expiry_detected == True,
                    DocumentAnalysis.expiry_date <= future_date,
                    DocumentAnalysis.expiry_date >= date.today()
                )
            ).order_by(DocumentAnalysis.expiry_date).all()
            
            return results
            
        except Exception as e:
            print(f"Error getting expiring documents: {str(e)}")
            return []
    
    def get_documents_by_folder(self, folder_name: str, company_db: Session) -> List[DocumentAnalysis]:
        """Get all analyzed documents in a specific folder"""
        try:
            results = company_db.query(DocumentAnalysis).filter(
                DocumentAnalysis.folder_name == folder_name
            ).order_by(DocumentAnalysis.created_at.desc()).all()
            
            return results
            
        except Exception as e:
            print(f"Error getting documents by folder: {str(e)}")
            return []
    
    def get_documents_by_type(self, document_type: str, company_db: Session) -> List[DocumentAnalysis]:
        """Get all analyzed documents of a specific type"""
        try:
            results = company_db.query(DocumentAnalysis).filter(
                DocumentAnalysis.document_type == document_type
            ).order_by(DocumentAnalysis.created_at.desc()).all()
            
            return results
            
        except Exception as e:
            print(f"Error getting documents by type: {str(e)}")
            return []
    
    def get_documents_by_user(self, user_id: int, company_db: Session) -> List[DocumentAnalysis]:
        """Get all analyzed documents uploaded by a specific user"""
        try:
            results = company_db.query(DocumentAnalysis).filter(
                DocumentAnalysis.user_id == user_id
            ).order_by(DocumentAnalysis.created_at.desc()).all()
            
            return results
            
        except Exception as e:
            print(f"Error getting documents by user: {str(e)}")
            return []
    
    def get_user_expiring_documents(self, user_id: int, company_db: Session, days_ahead: int = 30) -> List[DocumentAnalysis]:
        """Get documents expiring within specified days for a specific user"""
        try:
            future_date = date.today() + timedelta(days=days_ahead)
            
            results = company_db.query(DocumentAnalysis).filter(
                and_(
                    DocumentAnalysis.user_id == user_id,
                    DocumentAnalysis.expiry_detected == True,
                    DocumentAnalysis.expiry_date <= future_date,
                    DocumentAnalysis.expiry_date >= date.today()
                )
            ).order_by(DocumentAnalysis.expiry_date).all()
            
            return results
            
        except Exception as e:
            print(f"Error getting user expiring documents: {str(e)}")
            return []
    
    async def chat_with_document(self, document_id: int, query: str, company_db: Session) -> str:
        """Chat with a specific document using AI"""
        try:
            analysis = self.get_document_analysis(document_id, company_db)
            
            if not analysis:
                return "Document analysis not found. Please ensure the document has been processed."
            
            if not self.has_anthropic_key:
                return "AI service not available. Please contact your administrator."
            
            # Convert analysis to metadata format for chat
            metadata = {
                'title': analysis.title,
                'summary': analysis.summary,
                'document_type': analysis.document_type,
                'folder_name': analysis.folder_name,
                'extracted_text': analysis.extracted_text,
                'expiry_detected': analysis.expiry_detected,
                'expiry_date': analysis.expiry_date.isoformat() if analysis.expiry_date else None
            }
            
            response = await anthropic_service.chat_with_document(query, metadata)
            return response
            
        except Exception as e:
            return f"Error processing your question: {str(e)}"

# Create a global instance
document_analysis_service = DocumentAnalysisService()
