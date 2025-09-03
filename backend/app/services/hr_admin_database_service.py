"""
HR Admin Database Service - Comprehensive database access for HR administrators
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from app.models_company import (
    User as CompanyUser, Document as CompanyDocument, ChatHistory as CompanyChatHistory,
    ESignatureDocument, ESignatureRecipient, ESignatureAuditLog,
    DocumentCategory, DocumentFolder, DocumentAccess, DocumentAuditLog,
    UserLoginHistory, UserCredentials, UserActivity, DocumentAnalytics,
    ComplianceRule, ComplianceViolation, DocumentWorkflow, WorkflowStep,
    DocumentNotification, DocumentTag, DocumentTagMapping, DocumentVersion,
    UserFolder, HRManagedDocument, UserFolderAccess, UserFolderAuditLog,
    UserInvitation
)
from app.models_document_analysis import DocumentAnalysis, ExpiryNotification
from app.services.anthropic_service import anthropic_service
from app.config import ANTHROPIC_API_KEY

class HRAdminDatabaseService:
    def __init__(self):
        self.has_anthropic_key = bool(ANTHROPIC_API_KEY)
    
    def get_company_overview(self, company_db: Session) -> Dict[str, Any]:
        """Get comprehensive company overview for HR admins"""
        try:
            # User statistics
            total_users = company_db.query(CompanyUser).count()
            active_users = company_db.query(CompanyUser).filter(CompanyUser.is_active == True).count()
            hr_admins = company_db.query(CompanyUser).filter(CompanyUser.role.in_(['hr_admin', 'hr_manager'])).count()
            employees = company_db.query(CompanyUser).filter(CompanyUser.role == 'employee').count()
            
            # Document statistics
            total_documents = company_db.query(CompanyDocument).count()
            processed_documents = company_db.query(DocumentAnalysis).count()
            expiring_documents = company_db.query(DocumentAnalysis).filter(
                and_(
                    DocumentAnalysis.expiry_detected == True,
                    DocumentAnalysis.expiry_date <= date.today() + timedelta(days=30),
                    DocumentAnalysis.expiry_date >= date.today()
                )
            ).count()
            
            # Recent activity
            recent_uploads = company_db.query(CompanyDocument).filter(
                CompanyDocument.created_at >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            recent_logins = company_db.query(UserLoginHistory).filter(
                UserLoginHistory.login_timestamp >= datetime.utcnow() - timedelta(days=7)
            ).count()
            
            # E-signature statistics
            pending_signatures = company_db.query(ESignatureDocument).filter(
                ESignatureDocument.status == 'pending'
            ).count()
            
            completed_signatures = company_db.query(ESignatureDocument).filter(
                ESignatureDocument.status == 'completed'
            ).count()
            
            return {
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "hr_admins": hr_admins,
                    "employees": employees
                },
                "documents": {
                    "total": total_documents,
                    "processed": processed_documents,
                    "expiring_soon": expiring_documents
                },
                "activity": {
                    "recent_uploads": recent_uploads,
                    "recent_logins": recent_logins
                },
                "esignatures": {
                    "pending": pending_signatures,
                    "completed": completed_signatures
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to get company overview: {str(e)}"}
    
    def search_users(self, query: str, company_db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Search users by name, email, or role"""
        try:
            users = company_db.query(CompanyUser).filter(
                or_(
                    CompanyUser.full_name.ilike(f"%{query}%"),
                    CompanyUser.email.ilike(f"%{query}%"),
                    CompanyUser.username.ilike(f"%{query}%"),
                    CompanyUser.role.ilike(f"%{query}%")
                )
            ).limit(limit).all()
            
            result = []
            for user in users:
                # Get user statistics
                doc_count = company_db.query(CompanyDocument).filter(
                    CompanyDocument.user_id == user.id
                ).count()
                
                last_login = company_db.query(UserLoginHistory).filter(
                    UserLoginHistory.user_id == user.id
                ).order_by(desc(UserLoginHistory.login_timestamp)).first()
                
                result.append({
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at,
                    "document_count": doc_count,
                    "last_login": last_login.login_timestamp if last_login else None
                })
            
            return result
            
        except Exception as e:
            return [{"error": f"Failed to search users: {str(e)}"}]
    
    def get_user_details(self, user_id: str, company_db: Session) -> Dict[str, Any]:
        """Get detailed information about a specific user"""
        try:
            user = company_db.query(CompanyUser).filter(CompanyUser.id == user_id).first()
            if not user:
                return {"error": "User not found"}
            
            # Get user documents
            documents = company_db.query(CompanyDocument).filter(
                CompanyDocument.user_id == user_id
            ).order_by(desc(CompanyDocument.created_at)).limit(10).all()
            
            # Get analyzed documents
            analyzed_docs = company_db.query(DocumentAnalysis).filter(
                DocumentAnalysis.user_id == user_id
            ).order_by(desc(DocumentAnalysis.created_at)).limit(10).all()
            
            # Get login history
            login_history = company_db.query(UserLoginHistory).filter(
                UserLoginHistory.user_id == user_id
            ).order_by(desc(UserLoginHistory.login_timestamp)).limit(10).all()
            
            # Get user activity
            recent_activity = company_db.query(UserActivity).filter(
                UserActivity.user_id == user_id
            ).order_by(desc(UserActivity.timestamp)).limit(10).all()
            
            # Get expiring documents
            expiring_docs = company_db.query(DocumentAnalysis).filter(
                and_(
                    DocumentAnalysis.user_id == user_id,
                    DocumentAnalysis.expiry_detected == True,
                    DocumentAnalysis.expiry_date <= date.today() + timedelta(days=90),
                    DocumentAnalysis.expiry_date >= date.today()
                )
            ).order_by(DocumentAnalysis.expiry_date).all()
            
            return {
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role,
                    "is_active": user.is_active,
                    "created_at": user.created_at,
                    "password_set": user.password_set
                },
                "documents": [
                    {
                        "id": doc.id,
                        "filename": doc.filename,
                        "folder_name": doc.folder_name,
                        "file_type": doc.file_type,
                        "file_size": doc.file_size,
                        "created_at": doc.created_at
                    } for doc in documents
                ],
                "analyzed_documents": [
                    {
                        "id": doc.id,
                        "title": doc.title,
                        "document_type": doc.document_type,
                        "summary": doc.summary,
                        "expiry_detected": doc.expiry_detected,
                        "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
                        "created_at": doc.created_at
                    } for doc in analyzed_docs
                ],
                "login_history": [
                    {
                        "login_timestamp": login.login_timestamp,
                        "ip_address": login.ip_address,
                        "success": login.success,
                        "failure_reason": login.failure_reason
                    } for login in login_history
                ],
                "recent_activity": [
                    {
                        "activity_type": activity.activity_type,
                        "activity_details": activity.activity_details,
                        "timestamp": activity.timestamp
                    } for activity in recent_activity
                ],
                "expiring_documents": [
                    {
                        "title": doc.title,
                        "document_type": doc.document_type,
                        "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
                        "urgency_level": doc.urgency_level
                    } for doc in expiring_docs
                ]
            }
            
        except Exception as e:
            return {"error": f"Failed to get user details: {str(e)}"}
    
    def get_document_analytics(self, company_db: Session, days: int = 30) -> Dict[str, Any]:
        """Get document analytics and insights"""
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            # Document upload trends
            upload_trends = company_db.query(
                func.date(CompanyDocument.created_at).label('date'),
                func.count(CompanyDocument.id).label('count')
            ).filter(
                CompanyDocument.created_at >= start_date
            ).group_by(
                func.date(CompanyDocument.created_at)
            ).order_by('date').all()
            
            # Document types distribution
            doc_types = company_db.query(
                DocumentAnalysis.document_type,
                func.count(DocumentAnalysis.id).label('count')
            ).filter(
                DocumentAnalysis.document_type.isnot(None)
            ).group_by(
                DocumentAnalysis.document_type
            ).order_by(desc('count')).all()
            
            # Folder distribution
            folder_distribution = company_db.query(
                DocumentAnalysis.folder_name,
                func.count(DocumentAnalysis.id).label('count')
            ).filter(
                DocumentAnalysis.folder_name.isnot(None)
            ).group_by(
                DocumentAnalysis.folder_name
            ).order_by(desc('count')).all()
            
            # Expiry analysis
            expiry_analysis = company_db.query(
                DocumentAnalysis.urgency_level,
                func.count(DocumentAnalysis.id).label('count')
            ).filter(
                DocumentAnalysis.expiry_detected == True
            ).group_by(
                DocumentAnalysis.urgency_level
            ).all()
            
            # Top users by document count
            top_users = company_db.query(
                DocumentAnalysis.user_name,
                func.count(DocumentAnalysis.id).label('count')
            ).group_by(
                DocumentAnalysis.user_name
            ).order_by(desc('count')).limit(10).all()
            
            return {
                "upload_trends": [{"date": str(trend.date), "count": trend.count} for trend in upload_trends],
                "document_types": [{"type": doc_type.document_type, "count": doc_type.count} for doc_type in doc_types],
                "folder_distribution": [{"folder": folder.folder_name, "count": folder.count} for folder in folder_distribution],
                "expiry_analysis": [{"urgency": expiry.urgency_level, "count": expiry.count} for expiry in expiry_analysis],
                "top_users": [{"user": user.user_name, "count": user.count} for user in top_users]
            }
            
        except Exception as e:
            return {"error": f"Failed to get document analytics: {str(e)}"}
    
    def get_compliance_status(self, company_db: Session) -> Dict[str, Any]:
        """Get compliance status and violations"""
        try:
            # Get compliance rules
            rules = company_db.query(ComplianceRule).filter(
                ComplianceRule.is_active == True
            ).all()
            
            # Get violations
            violations = company_db.query(ComplianceViolation).filter(
                ComplianceViolation.resolved == False
            ).order_by(desc(ComplianceViolation.created_at)).all()
            
            # Get resolved violations
            resolved_violations = company_db.query(ComplianceViolation).filter(
                ComplianceViolation.resolved == True
            ).order_by(desc(ComplianceViolation.resolved_at)).limit(10).all()
            
            return {
                "rules": [
                    {
                        "id": rule.id,
                        "name": rule.name,
                        "description": rule.description,
                        "rule_type": rule.rule_type,
                        "retention_period_days": rule.retention_period_days
                    } for rule in rules
                ],
                "active_violations": [
                    {
                        "id": violation.id,
                        "violation_type": violation.violation_type,
                        "severity": violation.severity,
                        "description": violation.description,
                        "created_at": violation.created_at
                    } for violation in violations
                ],
                "resolved_violations": [
                    {
                        "id": violation.id,
                        "violation_type": violation.violation_type,
                        "severity": violation.severity,
                        "resolved_at": violation.resolved_at
                    } for violation in resolved_violations
                ]
            }
            
        except Exception as e:
            return {"error": f"Failed to get compliance status: {str(e)}"}
    
    def get_esignature_status(self, company_db: Session) -> Dict[str, Any]:
        """Get e-signature status and pending items"""
        try:
            # Get pending signatures
            pending_signatures = company_db.query(ESignatureDocument).filter(
                ESignatureDocument.status == 'pending'
            ).order_by(desc(ESignatureDocument.created_at)).all()
            
            # Get completed signatures
            completed_signatures = company_db.query(ESignatureDocument).filter(
                ESignatureDocument.status == 'completed'
            ).order_by(desc(ESignatureDocument.completed_at)).limit(10).all()
            
            # Get signature statistics
            total_signatures = company_db.query(ESignatureDocument).count()
            pending_count = company_db.query(ESignatureDocument).filter(
                ESignatureDocument.status == 'pending'
            ).count()
            completed_count = company_db.query(ESignatureDocument).filter(
                ESignatureDocument.status == 'completed'
            ).count()
            
            return {
                "statistics": {
                    "total": total_signatures,
                    "pending": pending_count,
                    "completed": completed_count
                },
                "pending_signatures": [
                    {
                        "id": sig.id,
                        "title": sig.title,
                        "status": sig.status,
                        "created_at": sig.created_at,
                        "expires_at": sig.expires_at,
                        "recipients": [
                            {
                                "email": recipient.email,
                                "full_name": recipient.full_name,
                                "is_signed": recipient.is_signed
                            } for recipient in sig.recipients
                        ]
                    } for sig in pending_signatures
                ],
                "recent_completed": [
                    {
                        "id": sig.id,
                        "title": sig.title,
                        "completed_at": sig.completed_at
                    } for sig in completed_signatures
                ]
            }
            
        except Exception as e:
            return {"error": f"Failed to get e-signature status: {str(e)}"}
    
    async def process_hr_admin_query(self, query: str, company_db: Session) -> str:
        """Process HR admin queries with comprehensive database access"""
        try:
            if not self.has_anthropic_key:
                return "AI service not available. Please contact your administrator."
            
            # Get comprehensive company data
            company_overview = self.get_company_overview(company_db)
            document_analytics = self.get_document_analytics(company_db)
            compliance_status = self.get_compliance_status(company_db)
            esignature_status = self.get_esignature_status(company_db)
            
            # Prepare context for AI
            context = {
                "company_overview": company_overview,
                "document_analytics": document_analytics,
                "compliance_status": compliance_status,
                "esignature_status": esignature_status,
                "query": query
            }
            
            # Use Anthropic to process the query with full database context
            response = await anthropic_service.process_hr_admin_query(query, context)
            return response
            
        except Exception as e:
            return f"Error processing your query: {str(e)}"
    
    def search_documents(self, query: str, company_db: Session, limit: int = 20) -> List[Dict[str, Any]]:
        """Search documents across all tables"""
        try:
            results = []
            
            # Search in regular documents
            documents = company_db.query(CompanyDocument).filter(
                or_(
                    CompanyDocument.filename.ilike(f"%{query}%"),
                    CompanyDocument.original_filename.ilike(f"%{query}%"),
                    CompanyDocument.folder_name.ilike(f"%{query}%")
                )
            ).limit(limit).all()
            
            for doc in documents:
                results.append({
                    "type": "document",
                    "id": doc.id,
                    "filename": doc.filename,
                    "folder_name": doc.folder_name,
                    "file_type": doc.file_type,
                    "file_size": doc.file_size,
                    "created_at": doc.created_at,
                    "user_id": doc.user_id
                })
            
            # Search in analyzed documents
            analyzed_docs = company_db.query(DocumentAnalysis).filter(
                or_(
                    DocumentAnalysis.title.ilike(f"%{query}%"),
                    DocumentAnalysis.summary.ilike(f"%{query}%"),
                    DocumentAnalysis.document_type.ilike(f"%{query}%"),
                    DocumentAnalysis.extracted_text.ilike(f"%{query}%")
                )
            ).limit(limit).all()
            
            for doc in analyzed_docs:
                results.append({
                    "type": "analyzed_document",
                    "id": doc.id,
                    "title": doc.title,
                    "document_type": doc.document_type,
                    "summary": doc.summary,
                    "folder_name": doc.folder_name,
                    "expiry_detected": doc.expiry_detected,
                    "expiry_date": doc.expiry_date.isoformat() if doc.expiry_date else None,
                    "created_at": doc.created_at,
                    "user_name": doc.user_name
                })
            
            return results[:limit]
            
        except Exception as e:
            return [{"error": f"Failed to search documents: {str(e)}"}]

# Create a global instance
hr_admin_database_service = HRAdminDatabaseService()
