"""
Expiry Agent Service - Proactive AI agent for document expiration monitoring
Monitors document expirations across all companies and sends notifications
"""

import uuid
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models import Company
from app.models_company import User, Document
from app.models_document_analysis import (
    DocumentAnalysis,
    ExpiryNotification,
    ExpiryAgentRun,
    ExpiryAgentConfig
)
from app.services.email_service import email_service
from app.services.database_manager import db_manager
from app.database import get_company_db

logger = logging.getLogger(__name__)


class ExpiryAgentService:
    """Proactive AI agent for document expiration monitoring"""

    def __init__(self):
        self.default_thresholds = {
            'urgent': 7,      # Days for urgent notifications
            'upcoming': 30,   # Days for upcoming notifications
            'future': 90      # Days for future planning notifications
        }

    async def run_expiry_check_for_all_companies(
        self,
        management_db: Session,
        triggered_by: Optional[str] = None,
        run_type: str = 'scheduled'
    ) -> Dict[str, Any]:
        """
        Main entry point - run expiry check across all active companies

        Args:
            management_db: Management database session
            triggered_by: User ID who triggered the run (for manual runs)
            run_type: 'scheduled' or 'manual'

        Returns:
            Summary of the agent run
        """
        run_id = f"expiry_run_{uuid.uuid4().hex[:12]}"
        start_time = datetime.utcnow()

        logger.info(f"[EXPIRY AGENT] Starting run {run_id} - Type: {run_type}")

        run_summary = {
            'run_id': run_id,
            'run_type': run_type,
            'triggered_by': triggered_by,
            'start_time': start_time.isoformat(),
            'companies_processed': 0,
            'documents_scanned': 0,
            'notifications_created': 0,
            'emails_sent': 0,
            'urgent_count': 0,
            'upcoming_count': 0,
            'future_count': 0,
            'errors': []
        }

        try:
            # Get all active companies
            companies = management_db.query(Company).filter(
                Company.is_active == True
            ).all()

            logger.info(f"[EXPIRY AGENT] Found {len(companies)} active companies")

            for company in companies:
                try:
                    company_result = await self.scan_company_documents(
                        company=company,
                        run_id=run_id
                    )

                    run_summary['companies_processed'] += 1
                    run_summary['documents_scanned'] += company_result.get('documents_scanned', 0)
                    run_summary['notifications_created'] += company_result.get('notifications_created', 0)
                    run_summary['emails_sent'] += company_result.get('emails_sent', 0)
                    run_summary['urgent_count'] += company_result.get('urgent_count', 0)
                    run_summary['upcoming_count'] += company_result.get('upcoming_count', 0)
                    run_summary['future_count'] += company_result.get('future_count', 0)

                except Exception as e:
                    error_msg = f"Error processing company {company.id}: {str(e)}"
                    logger.error(f"[EXPIRY AGENT] {error_msg}")
                    run_summary['errors'].append(error_msg)

            # Calculate duration
            end_time = datetime.utcnow()
            duration_seconds = int((end_time - start_time).total_seconds())
            run_summary['duration_seconds'] = duration_seconds
            run_summary['end_time'] = end_time.isoformat()
            run_summary['status'] = 'completed' if not run_summary['errors'] else 'completed_with_errors'

            logger.info(f"[EXPIRY AGENT] Run {run_id} completed in {duration_seconds}s")
            logger.info(f"[EXPIRY AGENT] Summary: {run_summary['documents_scanned']} docs scanned, "
                       f"{run_summary['notifications_created']} notifications, "
                       f"{run_summary['emails_sent']} emails sent")

            return run_summary

        except Exception as e:
            error_msg = f"Critical error in expiry agent: {str(e)}"
            logger.error(f"[EXPIRY AGENT] {error_msg}")
            run_summary['status'] = 'failed'
            run_summary['errors'].append(error_msg)
            return run_summary

    async def scan_company_documents(
        self,
        company: Company,
        run_id: str
    ) -> Dict[str, Any]:
        """
        Scan documents for a specific company and process expirations

        Args:
            company: Company model instance
            run_id: Current agent run ID

        Returns:
            Summary of company processing
        """
        logger.info(f"[EXPIRY AGENT] Scanning company: {company.name} ({company.id})")

        result = {
            'company_id': company.id,
            'company_name': company.name,
            'documents_scanned': 0,
            'notifications_created': 0,
            'emails_sent': 0,
            'urgent_count': 0,
            'upcoming_count': 0,
            'future_count': 0
        }

        try:
            # Get company database connection
            company_db_gen = get_company_db(str(company.id), str(company.database_url))
            company_db = next(company_db_gen)

            try:
                # Get expiring documents with different thresholds
                expiring_docs = await self.identify_expiring_documents(
                    company_db=company_db,
                    company_id=company.id,
                    days_thresholds=[7, 30, 60, 90]
                )

                result['documents_scanned'] = expiring_docs.get('total_scanned', 0)

                # Process urgent documents (<=7 days) - Individual emails
                urgent_docs = expiring_docs.get('urgent', [])
                result['urgent_count'] = len(urgent_docs)

                for doc in urgent_docs:
                    try:
                        # Generate AI reasons for expiry
                        reasons = await self.generate_expiry_reasons(doc)

                        # Create notification record
                        notification = await self.create_expiry_notification(
                            company_db=company_db,
                            document=doc,
                            reasons=reasons,
                            run_id=run_id,
                            urgency='urgent'
                        )

                        if notification:
                            result['notifications_created'] += 1

                        # Send individual email to user
                        email_sent = await self.notify_user(
                            document=doc,
                            reasons=reasons,
                            company_name=company.name
                        )

                        if email_sent:
                            result['emails_sent'] += 1

                    except Exception as e:
                        logger.error(f"[EXPIRY AGENT] Error processing urgent doc {doc.get('document_id')}: {e}")

                # Process upcoming documents (8-30 days) - Daily digest
                upcoming_docs = expiring_docs.get('upcoming', [])
                result['upcoming_count'] = len(upcoming_docs)

                # Group upcoming docs by user for digest
                user_upcoming = {}
                for doc in upcoming_docs:
                    user_id = doc.get('user_id')
                    if user_id not in user_upcoming:
                        user_upcoming[user_id] = []
                    user_upcoming[user_id].append(doc)

                for user_id, docs in user_upcoming.items():
                    try:
                        # Send digest email
                        email_sent = await self.send_user_digest(
                            user_email=docs[0].get('user_email'),
                            user_name=docs[0].get('user_name'),
                            documents=docs,
                            company_name=company.name
                        )
                        if email_sent:
                            result['emails_sent'] += 1

                    except Exception as e:
                        logger.error(f"[EXPIRY AGENT] Error sending digest to user {user_id}: {e}")

                # Process future documents (31-90 days)
                future_docs = expiring_docs.get('future', [])
                result['future_count'] = len(future_docs)

                # Send HR summary for all expiring documents
                all_expiring = urgent_docs + upcoming_docs + future_docs
                if all_expiring:
                    await self.send_hr_summary(
                        company_db=company_db,
                        company_id=company.id,
                        company_name=company.name,
                        expiring_documents=all_expiring
                    )
                    result['emails_sent'] += 1

            finally:
                company_db.close()

            logger.info(f"[EXPIRY AGENT] Company {company.name}: {result}")
            return result

        except Exception as e:
            logger.error(f"[EXPIRY AGENT] Error scanning company {company.id}: {e}")
            raise

    async def identify_expiring_documents(
        self,
        company_db: Session,
        company_id: str,
        days_thresholds: List[int] = [7, 30, 60, 90]
    ) -> Dict[str, Any]:
        """
        Identify documents with upcoming expiry dates

        Args:
            company_db: Company database session
            company_id: Company ID
            days_thresholds: List of day thresholds for categorization

        Returns:
            Categorized expiring documents
        """
        today = date.today()
        max_days = max(days_thresholds)
        future_date = today + timedelta(days=max_days)

        result = {
            'total_scanned': 0,
            'urgent': [],      # <=7 days
            'upcoming': [],    # 8-30 days
            'future': []       # 31-90 days
        }

        try:
            # Query DocumentAnalysis for documents with expiry dates
            expiring_analyses = company_db.query(DocumentAnalysis).filter(
                and_(
                    DocumentAnalysis.expiry_detected == True,
                    DocumentAnalysis.expiry_date != None,
                    DocumentAnalysis.expiry_date >= today,
                    DocumentAnalysis.expiry_date <= future_date
                )
            ).all()

            result['total_scanned'] = company_db.query(DocumentAnalysis).count()

            for analysis in expiring_analyses:
                days_until = (analysis.expiry_date - today).days

                # Get user information
                user = company_db.query(User).filter(
                    User.id == analysis.user_id
                ).first()

                doc_info = {
                    'document_id': analysis.document_id,
                    'document_analysis_id': analysis.id,
                    'document_name': analysis.title or 'Unknown Document',
                    'document_type': analysis.document_type or 'Document',
                    'folder_name': analysis.folder_name,
                    'expiry_date': analysis.expiry_date.isoformat() if analysis.expiry_date else None,
                    'days_until_expiry': days_until,
                    'urgency_level': analysis.urgency_level or 'low',
                    'user_id': analysis.user_id,
                    'user_name': analysis.user_name or (user.full_name if user else 'Unknown'),
                    'user_email': analysis.user_email or (user.email if user else None),
                    'summary': analysis.summary,
                    'expiry_type': analysis.expiry_type
                }

                # Categorize by days until expiry
                if days_until <= 7:
                    result['urgent'].append(doc_info)
                elif days_until <= 30:
                    result['upcoming'].append(doc_info)
                else:
                    result['future'].append(doc_info)

            logger.info(f"[EXPIRY AGENT] Found: {len(result['urgent'])} urgent, "
                       f"{len(result['upcoming'])} upcoming, {len(result['future'])} future")

            return result

        except Exception as e:
            logger.error(f"[EXPIRY AGENT] Error identifying expiring documents: {e}")
            return result

    async def generate_expiry_reasons(
        self,
        document: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Generate AI-powered reasons for document expiration importance

        Args:
            document: Document information dict

        Returns:
            List of reason dictionaries
        """
        doc_type = (document.get('document_type') or '').lower()
        expiry_type = (document.get('expiry_type') or '').lower()

        reasons = []

        # Type-specific reasons
        if 'passport' in doc_type or 'passport' in expiry_type:
            reasons.extend([
                {
                    'type': 'compliance',
                    'message': 'Valid passport is required for international travel and identity verification'
                },
                {
                    'type': 'legal',
                    'message': 'Expired passport may affect employment eligibility for I-9 purposes'
                },
                {
                    'type': 'action_required',
                    'message': 'Contact passport office to renew - processing can take 6-8 weeks'
                }
            ])

        elif 'driver' in doc_type or 'license' in doc_type or 'driver_license' in expiry_type:
            reasons.extend([
                {
                    'type': 'compliance',
                    'message': "Driver's license is required for vehicle operation authorization"
                },
                {
                    'type': 'legal',
                    'message': 'Expired license may void company vehicle insurance coverage'
                },
                {
                    'type': 'action_required',
                    'message': 'Visit DMV to renew license and upload new document'
                }
            ])

        elif 'green_card' in doc_type or 'permanent_resident' in doc_type or 'green_card' in expiry_type:
            reasons.extend([
                {
                    'type': 'compliance',
                    'message': 'Green card renewal is required for continued work authorization'
                },
                {
                    'type': 'legal',
                    'message': 'Expired green card affects I-9 reverification requirements'
                },
                {
                    'type': 'action_required',
                    'message': 'File Form I-90 with USCIS - processing can take 12-18 months'
                }
            ])

        elif 'military' in doc_type or 'military_id' in expiry_type:
            reasons.extend([
                {
                    'type': 'compliance',
                    'message': 'Military ID is required for access to military facilities and benefits'
                },
                {
                    'type': 'action_required',
                    'message': 'Contact personnel office to renew military ID card'
                }
            ])

        elif 'work_permit' in doc_type or 'ead' in doc_type or 'work_authorization' in expiry_type:
            reasons.extend([
                {
                    'type': 'compliance',
                    'message': 'Work authorization is required for continued employment eligibility'
                },
                {
                    'type': 'legal',
                    'message': 'Employment must cease if work authorization expires without valid extension'
                },
                {
                    'type': 'action_required',
                    'message': 'File renewal application at least 180 days before expiration'
                }
            ])

        elif 'certification' in doc_type or 'certificate' in doc_type:
            reasons.extend([
                {
                    'type': 'compliance',
                    'message': 'Professional certification may be required for job duties'
                },
                {
                    'type': 'action_required',
                    'message': 'Complete required continuing education and renew certification'
                }
            ])

        elif 'contract' in doc_type or 'agreement' in doc_type:
            reasons.extend([
                {
                    'type': 'legal',
                    'message': 'Contract terms and conditions may need review before expiration'
                },
                {
                    'type': 'action_required',
                    'message': 'Review contract and negotiate renewal terms if needed'
                }
            ])

        else:
            # Generic reasons
            reasons.extend([
                {
                    'type': 'compliance',
                    'message': 'This document is approaching its expiration date'
                },
                {
                    'type': 'action_required',
                    'message': 'Please review this document and take necessary action to renew'
                }
            ])

        return reasons

    def generate_recommended_action(self, document: Dict[str, Any], reasons: List[Dict[str, str]]) -> str:
        """Generate a recommended action based on document type and reasons"""
        doc_type = (document.get('document_type') or '').lower()

        action_recommendations = {
            'passport': 'Apply for passport renewal through the State Department. Processing time is typically 6-8 weeks for routine service.',
            'driver_license': 'Visit your local DMV to renew your license. Check if your state allows online renewal.',
            'green_card': 'File Form I-90 (Application to Replace Permanent Resident Card) with USCIS at least 6 months before expiration.',
            'military_id': 'Contact your unit personnel office or DEERS/ID card facility to schedule ID renewal.',
            'work_permit': 'Consult with your immigration attorney and file renewal application at least 180 days before expiration.',
            'ead': 'File Form I-765 for EAD renewal. Consider expedited processing if eligible.',
            'certification': 'Complete continuing education requirements and submit renewal application to certifying body.',
            'contract': 'Review contract terms and schedule renewal discussion with relevant parties.',
        }

        for key, action in action_recommendations.items():
            if key in doc_type:
                return action

        return 'Review this document and take appropriate action to ensure continued validity.'

    async def create_expiry_notification(
        self,
        company_db: Session,
        document: Dict[str, Any],
        reasons: List[Dict[str, str]],
        run_id: str,
        urgency: str
    ) -> Optional[ExpiryNotification]:
        """Create an expiry notification record in the database"""
        try:
            from datetime import datetime

            recommended_action = self.generate_recommended_action(document, reasons)

            notification = ExpiryNotification(
                document_analysis_id=document.get('document_analysis_id', 0),
                document_id=document.get('document_id', ''),
                user_id=document.get('user_id', ''),
                user_name=document.get('user_name'),
                user_email=document.get('user_email'),
                notification_type='expiry_warning',
                expiry_date=datetime.strptime(document.get('expiry_date'), '%Y-%m-%d').date() if document.get('expiry_date') else None,
                days_until_expiry=document.get('days_until_expiry', 0),
                urgency_level=urgency,
                notification_status='pending',
                ai_generated_reasons=reasons,
                recommended_action=recommended_action,
                agent_run_id=run_id
            )

            company_db.add(notification)
            company_db.commit()
            company_db.refresh(notification)

            return notification

        except Exception as e:
            logger.error(f"[EXPIRY AGENT] Error creating notification: {e}")
            company_db.rollback()
            return None

    async def notify_user(
        self,
        document: Dict[str, Any],
        reasons: List[Dict[str, str]],
        company_name: str
    ) -> bool:
        """Send expiry notification email to user"""
        user_email = document.get('user_email')
        user_name = document.get('user_name', 'User')

        if not user_email:
            logger.warning(f"[EXPIRY AGENT] No email for user {document.get('user_id')}")
            return False

        try:
            # Prepare document info for email
            doc_info = {
                'document_name': document.get('document_name'),
                'document_type': document.get('document_type'),
                'expiry_date': document.get('expiry_date'),
                'days_until_expiry': document.get('days_until_expiry'),
                'recommended_action': self.generate_recommended_action(document, reasons)
            }

            success = await email_service.send_expiry_alert(
                user_email=user_email,
                user_name=user_name,
                document=doc_info,
                reasons=reasons,
                company_name=company_name
            )

            return success

        except Exception as e:
            logger.error(f"[EXPIRY AGENT] Error sending email to {user_email}: {e}")
            return False

    async def send_user_digest(
        self,
        user_email: str,
        user_name: str,
        documents: List[Dict[str, Any]],
        company_name: str
    ) -> bool:
        """Send daily digest of expiring documents to user"""
        if not user_email:
            return False

        try:
            success = await email_service.send_expiry_digest(
                user_email=user_email,
                user_name=user_name,
                documents=documents,
                company_name=company_name
            )

            return success

        except Exception as e:
            logger.error(f"[EXPIRY AGENT] Error sending digest to {user_email}: {e}")
            return False

    async def send_hr_summary(
        self,
        company_db: Session,
        company_id: str,
        company_name: str,
        expiring_documents: List[Dict[str, Any]],
        summary_type: str = 'daily'
    ) -> bool:
        """Send expiry summary to HR admins"""
        try:
            # Get HR admins for the company
            hr_admins = company_db.query(User).filter(
                User.role.in_(['hr_admin', 'hr_manager']),
                User.is_active == True
            ).all()

            if not hr_admins:
                logger.info(f"[EXPIRY AGENT] No HR admins found for company {company_id}")
                return False

            # Prepare expiry data with employee info
            expiry_data = []
            for doc in expiring_documents:
                expiry_data.append({
                    'employee_name': doc.get('user_name', 'Unknown'),
                    'employee_id': doc.get('user_id'),
                    'document_name': doc.get('document_name'),
                    'document_type': doc.get('document_type'),
                    'expiry_date': doc.get('expiry_date'),
                    'days_until_expiry': doc.get('days_until_expiry')
                })

            # Send to each HR admin
            for hr_admin in hr_admins:
                try:
                    await email_service.send_hr_expiry_summary(
                        hr_email=hr_admin.email,
                        hr_name=hr_admin.full_name,
                        company_expiries=expiry_data,
                        company_name=company_name,
                        summary_type=summary_type
                    )
                except Exception as e:
                    logger.error(f"[EXPIRY AGENT] Error sending HR summary to {hr_admin.email}: {e}")

            return True

        except Exception as e:
            logger.error(f"[EXPIRY AGENT] Error sending HR summary: {e}")
            return False

    async def get_agent_status(
        self,
        company_db: Session,
        company_id: str
    ) -> Dict[str, Any]:
        """Get the status of the expiry agent for a company"""
        try:
            # Get last run
            last_run = company_db.query(ExpiryAgentRun).filter(
                ExpiryAgentRun.company_id == company_id
            ).order_by(ExpiryAgentRun.run_date.desc()).first()

            # Get pending notifications
            pending_count = company_db.query(ExpiryNotification).filter(
                ExpiryNotification.notification_status == 'pending'
            ).count()

            # Get config
            config = company_db.query(ExpiryAgentConfig).filter(
                ExpiryAgentConfig.company_id == company_id
            ).first()

            return {
                'last_run': {
                    'run_id': last_run.id if last_run else None,
                    'run_date': last_run.run_date.isoformat() if last_run else None,
                    'status': last_run.status if last_run else None,
                    'documents_scanned': last_run.documents_scanned if last_run else 0,
                    'notifications_sent': last_run.notifications_sent if last_run else 0
                } if last_run else None,
                'pending_notifications': pending_count,
                'config': {
                    'is_enabled': config.is_enabled if config else True,
                    'daily_run_time': config.daily_run_time if config else '08:00',
                    'timezone': config.timezone if config else 'UTC'
                } if config else {
                    'is_enabled': True,
                    'daily_run_time': '08:00',
                    'timezone': 'UTC'
                }
            }

        except Exception as e:
            logger.error(f"[EXPIRY AGENT] Error getting agent status: {e}")
            return {
                'error': str(e),
                'last_run': None,
                'pending_notifications': 0,
                'config': None
            }

    async def get_pending_notifications(
        self,
        company_db: Session,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get pending expiry notifications"""
        try:
            notifications = company_db.query(ExpiryNotification).filter(
                ExpiryNotification.notification_status == 'pending'
            ).order_by(
                ExpiryNotification.days_until_expiry.asc()
            ).limit(limit).all()

            return [
                {
                    'id': n.id,
                    'document_id': n.document_id,
                    'user_name': n.user_name,
                    'user_email': n.user_email,
                    'expiry_date': n.expiry_date.isoformat() if n.expiry_date else None,
                    'days_until_expiry': n.days_until_expiry,
                    'urgency_level': n.urgency_level,
                    'notification_status': n.notification_status,
                    'ai_generated_reasons': n.ai_generated_reasons,
                    'recommended_action': n.recommended_action,
                    'created_at': n.created_at.isoformat() if n.created_at else None
                }
                for n in notifications
            ]

        except Exception as e:
            logger.error(f"[EXPIRY AGENT] Error getting pending notifications: {e}")
            return []


# Create global service instance
expiry_agent_service = ExpiryAgentService()
