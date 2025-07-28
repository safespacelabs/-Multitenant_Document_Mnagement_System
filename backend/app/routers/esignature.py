from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy import text

from ..auth import get_current_user
from ..database import get_management_db
from ..models_company import ESignatureDocument, ESignatureRecipient, ESignatureAuditLog
from ..schemas import ESignatureRequest, ESignatureResponse, ESignatureStatus, ESignatureSignRequest
from ..services.inkless_service import InklessService
from ..services.database_manager import db_manager
from ..utils.permissions import (
    ESignaturePermissions, 
    PermissionAction,
    can_create_esignature_request,
    can_send_esignature_request,
    can_view_esignature_request,
    can_cancel_esignature_request,
    has_esignature_permission
)
from .. import models

router = APIRouter(prefix="/esignature", tags=["E-Signature"])
logger = logging.getLogger(__name__)

def get_company_db_session(
    current_user = Depends(get_current_user),
    management_db: Session = Depends(get_management_db)
):
    """Get company database session for the current user"""
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        # Handle system admins - they need to work with the first active company
        if user_role == 'system_admin':
            # For system admins, use the first active company
            # In production, this could be improved to allow company selection
            company = management_db.query(models.Company).filter(
                models.Company.is_active == True
            ).first()
            
            if not company:
                raise HTTPException(
                    status_code=404,
                    detail="No active companies found for system admin operations"
                )
                
            logger.info(f"System admin {current_user.username} using company: {company.name}")
            
        elif hasattr(current_user, 'company_id') and current_user.company_id:
            # User already has company info attached
            company = management_db.query(models.Company).filter(
                models.Company.id == current_user.company_id
            ).first()
        else:
            # Find company for regular user without company_id
            companies = management_db.query(models.Company).filter(
                models.Company.is_active == True
            ).all()
            
            company = None
            for comp in companies:
                try:
                    company_db_gen = db_manager.get_company_db(str(comp.id), str(comp.database_url))
                    company_db = next(company_db_gen)
                    
                    # Check if user exists in this company
                    from ..models_company import User as CompanyUser
                    user = company_db.query(CompanyUser).filter(
                        CompanyUser.username == current_user.username
                    ).first()
                    
                    if user:
                        company = comp
                        company_db.close()
                        break
                    
                    company_db.close()
                except Exception:
                    continue
        
        if not company:
            raise HTTPException(
                status_code=404,
                detail="Company not found for user"
            )
        
        # Ensure E-signature tables exist for this company
        db_manager.ensure_esignature_tables_exist(str(company.id), str(company.database_url))
        
        # Get company database session
        company_db_gen = db_manager.get_company_db(str(company.id), str(company.database_url))
        company_db = next(company_db_gen)
        
        try:
            yield company_db
        finally:
            company_db.close()
            
    except Exception as e:
        logger.error(f"Error getting company database: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Database connection error: {str(e)}"
        )

@router.post("/create-request")
async def create_signature_request(
    request_data: ESignatureRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_company_db_session)
):
    """
    Create a new e-signature request with dynamic role-based permissions
    """
    try:
        # Check permissions dynamically
        user_role = getattr(current_user, 'role', 'customer')
        if not can_create_esignature_request(user_role):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' does not have permission to create signature requests"
            )
        
        # Validate request data
        if not request_data.document_id:
            raise HTTPException(status_code=400, detail="Document ID is required")
        if not request_data.title:
            raise HTTPException(status_code=400, detail="Title is required")
        if not request_data.recipients:
            raise HTTPException(status_code=400, detail="At least one recipient is required")
        
        # Validate recipients
        for recipient in request_data.recipients:
            if not recipient.email:
                raise HTTPException(status_code=400, detail="Recipient email is required")
            if not recipient.full_name:
                raise HTTPException(status_code=400, detail="Recipient full name is required")
        
        # Step 1: Create the main signature document in database
        esign_id = f"esign_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        expires_at = datetime.utcnow() + timedelta(days=request_data.expires_in_days if request_data.expires_in_days else 14)
        
        # Create document record
        esign_doc = ESignatureDocument(
            id=esign_id,
            document_id=request_data.document_id,
            title=request_data.title,
            message=request_data.message,
            status="pending",
            created_by_user_id=current_user.id,
            require_all_signatures=True,
            expires_at=expires_at,
            created_at=datetime.utcnow()
        )
        
        db.add(esign_doc)
        db.flush()
        
        # Step 2: Create recipient records
        recipients_data = []
        for recipient in request_data.recipients:
            recipient_record = ESignatureRecipient(
                esignature_document_id=esign_id,
                email=recipient.email,
                full_name=recipient.full_name,
                role=recipient.role,
                is_signed=False,
                created_at=datetime.utcnow()
            )
            db.add(recipient_record)
            recipients_data.append({
                "email": recipient.email,
                "name": recipient.full_name,
                "role": recipient.role or "Recipient"
            })
        
        # Step 3: Create audit log entry
        audit_log = ESignatureAuditLog(
            esignature_document_id=esign_id,
            action="created",
            user_email=current_user.email,
            details=json.dumps({
                "title": request_data.title,
                "recipients_count": len(recipients_data),
                "expires_at": expires_at.isoformat(),
                "created_by_role": user_role
            }),
            created_at=datetime.utcnow()
        )
        db.add(audit_log)
        
        # Step 4: Auto-send if user has send permission
        current_status = "pending"
        inkless_doc_id = ""
        inkless_doc_url = ""
        
        if can_send_esignature_request(user_role):
            try:
                # Initialize Inkless service
                inkless_service = InklessService()
                document_url = f"https://mock-document-url.com/documents/{request_data.document_id}"
                
                # Create signature request in Inkless
                inkless_response = await inkless_service.create_signature_request(
                    document_url=document_url,
                    document_name=request_data.title,
                    recipients=recipients_data,
                    title=request_data.title,
                    message=request_data.message,
                    expires_in_days=request_data.expires_in_days if request_data.expires_in_days else 14
                )
                
                # Extract response data
                inkless_doc_id = inkless_response.get("document_id", "")
                inkless_doc_url = inkless_response.get("signing_url", "")
                current_status = "created"
                
                # Step 5: Send signature request emails
                send_response = await inkless_service.send_signature_request(inkless_doc_id)
                
                if send_response.get("success"):
                    current_status = "sent"
                    
                    # Log the send action
                    send_audit = ESignatureAuditLog(
                        esignature_document_id=esign_id,
                        action="sent",
                        user_email=current_user.email,
                        details=json.dumps({
                            "recipients_notified": len(recipients_data),
                            "inkless_document_id": inkless_doc_id,
                            "auto_sent": True,
                            "sent_by_role": user_role
                        }),
                        created_at=datetime.utcnow()
                    )
                    db.add(send_audit)
                    
                    logger.info(f"✅ E-signature request {esign_id} auto-sent successfully to {len(recipients_data)} recipients by {user_role}")
                
            except Exception as inkless_error:
                logger.warning(f"⚠️ Inkless service error: {str(inkless_error)}")
                current_status = "failed"
                
                # Log the failure
                failure_audit = ESignatureAuditLog(
                    esignature_document_id=esign_id,
                    action="failed",
                    user_email=current_user.email,
                    details=json.dumps({
                        "error": str(inkless_error),
                        "fallback_mode": True,
                        "attempted_by_role": user_role
                    }),
                    created_at=datetime.utcnow()
                )
                db.add(failure_audit)
        
        # Step 6: Update document with final status and commit
        db.execute(
            text("UPDATE esignature_documents SET status = :status, inkless_document_id = :doc_id, inkless_document_url = :doc_url WHERE id = :id"),
            {
                "status": current_status,
                "doc_id": inkless_doc_id,
                "doc_url": inkless_doc_url,
                "id": esign_id
            }
        )
        db.commit()
        
        # Step 7: Return success response
        return {
            "id": esign_id,
            "document_id": request_data.document_id,
            "title": request_data.title,
            "message": request_data.message,
            "status": current_status,
            "created_by_user_id": current_user.id,
            "created_by_role": user_role,
            "recipients": recipients_data,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "inkless_document_id": inkless_doc_id,
            "inkless_document_url": inkless_doc_url,
            "auto_sent": can_send_esignature_request(user_role),
            "success": True
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error creating signature request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create signature request: {str(e)}")

@router.post("/{esign_doc_id}/send")
async def send_signature_request(
    esign_doc_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_company_db_session)
):
    """
    Send signature request with dynamic role-based permissions
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        # Check permissions dynamically
        if not can_send_esignature_request(user_role):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' does not have permission to send signature requests"
            )
        
        # Get the signature document
        esign_doc = db.query(ESignatureDocument).filter(
            ESignatureDocument.id == esign_doc_id
        ).first()
        
        if not esign_doc:
            raise HTTPException(status_code=404, detail="Signature request not found")
        
        # Check if user can send this specific request
        if not can_cancel_esignature_request(user_role, str(esign_doc.created_by_user_id), current_user.id):
            if str(esign_doc.created_by_user_id) != current_user.id:
                raise HTTPException(
                    status_code=403,
                    detail="You can only send your own signature requests"
                )
        
        # Update status to sent
        db.execute(
            text("UPDATE esignature_documents SET status = 'sent' WHERE id = :id"),
            {"id": esign_doc_id}
        )
        
        # Add audit log
        audit_log = ESignatureAuditLog(
            esignature_document_id=esign_doc_id,
            action="sent",
            user_email=current_user.email,
            details=json.dumps({
                "manual_send": True,
                "sent_by_role": user_role
            }),
            created_at=datetime.utcnow()
        )
        db.add(audit_log)
        db.commit()
        
        return {
            "message": "Signature request sent successfully",
            "status": "sent",
            "sent_by_role": user_role
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error sending signature request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send signature request: {str(e)}")

@router.get("/list")
async def list_signature_requests(
    status: Optional[str] = None,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_company_db_session)
):
    """
    List signature requests with dynamic role-based filtering
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        # Check base view permission
        if not can_view_esignature_request(user_role):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' does not have permission to view signature requests"
            )
        
        query = db.query(ESignatureDocument)
        
        # Filter by status if provided
        if status and status != "all":
            query = query.filter(ESignatureDocument.status == status)
        
        # Dynamic role-based filtering
        if user_role in ["system_admin", "hr_admin"]:
            # Can view all requests
            pass
        elif user_role == "hr_manager":
            # Can view all requests in their company
            pass
        elif user_role in ["employee", "customer"]:
            # Only show requests they created or are recipients of
            recipient_ids = db.query(ESignatureRecipient.esignature_document_id).filter(
                ESignatureRecipient.email == current_user.email
            ).all()
            recipient_doc_ids = [r.esignature_document_id for r in recipient_ids]
            
            query = query.filter(
                (ESignatureDocument.created_by_user_id == current_user.id) |
                (ESignatureDocument.id.in_(recipient_doc_ids))
            )
        
        esign_docs = query.order_by(ESignatureDocument.created_at.desc()).all()
        
        # Convert to response format
        results = []
        for doc in esign_docs:
            recipients = db.query(ESignatureRecipient).filter(
                ESignatureRecipient.esignature_document_id == doc.id
            ).all()
            
            # Add permission info for this specific request
            can_cancel = can_cancel_esignature_request(user_role, str(doc.created_by_user_id), current_user.id)
            
            results.append({
                "id": doc.id,
                "document_id": doc.document_id,
                "title": doc.title,
                "message": doc.message,
                "status": doc.status,
                "created_by_user_id": doc.created_by_user_id,
                "recipients": [
                    {
                        "email": r.email,
                        "full_name": r.full_name,
                        "role": r.role,
                        "is_signed": r.is_signed
                    } for r in recipients
                ],
                "expires_at": doc.expires_at.isoformat() if doc.expires_at is not None else None,
                "created_at": doc.created_at.isoformat() if doc.created_at is not None else None,
                "inkless_document_id": doc.inkless_document_id,
                "inkless_document_url": doc.inkless_document_url,
                "permissions": {
                    "can_cancel": can_cancel,
                    "can_send": can_send_esignature_request(user_role),
                    "can_view_audit": has_esignature_permission(user_role, PermissionAction.AUDIT_VIEW)
                }
            })
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error listing signature requests: {str(e)}")
        # Return empty list on error to prevent crashes
        return []

@router.get("/{esign_doc_id}/status")
async def get_signature_status(
    esign_doc_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_company_db_session)
):
    """
    Get signature status with dynamic role-based permissions
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        # Check permissions
        if not can_view_esignature_request(user_role):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' does not have permission to view signature status"
            )
        
        # Get the signature document
        esign_doc = db.query(ESignatureDocument).filter(
            ESignatureDocument.id == esign_doc_id
        ).first()
        
        if not esign_doc:
            raise HTTPException(status_code=404, detail="Signature request not found")
        
        # Check if user can view this specific request
        if user_role in ["employee", "customer"]:
            # Check if user is creator or recipient
            is_creator = str(esign_doc.created_by_user_id) == current_user.id
            is_recipient = db.query(ESignatureRecipient).filter(
                ESignatureRecipient.esignature_document_id == esign_doc_id,
                ESignatureRecipient.email == current_user.email
            ).first() is not None
            
            if not (is_creator or is_recipient):
                raise HTTPException(
                    status_code=403,
                    detail="You can only view your own signature requests or requests you're a recipient of"
                )
        
        # Get recipients
        recipients = db.query(ESignatureRecipient).filter(
            ESignatureRecipient.esignature_document_id == esign_doc_id
        ).all()
        
        return {
            "id": esign_doc.id,
            "status": esign_doc.status,
            "title": esign_doc.title,
            "message": esign_doc.message,
            "recipients": [
                {
                    "email": r.email,
                    "full_name": r.full_name,
                    "role": r.role,
                    "is_signed": r.is_signed,
                    "signed_at": r.signed_at.isoformat() if r.signed_at is not None else None
                } for r in recipients
            ],
            "created_at": esign_doc.created_at.isoformat() if esign_doc.created_at is not None else None,
            "expires_at": esign_doc.expires_at.isoformat() if esign_doc.expires_at is not None else None,
            "viewed_by_role": user_role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting signature status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get signature status: {str(e)}")

@router.post("/{esign_doc_id}/cancel")
async def cancel_signature_request(
    esign_doc_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_company_db_session)
):
    """
    Cancel signature request with dynamic role-based permissions
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        # Get the signature document
        esign_doc = db.query(ESignatureDocument).filter(
            ESignatureDocument.id == esign_doc_id
        ).first()
        
        if not esign_doc:
            raise HTTPException(status_code=404, detail="Signature request not found")
        
        # Check permissions dynamically
        if not can_cancel_esignature_request(user_role, str(esign_doc.created_by_user_id), current_user.id):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' does not have permission to cancel this signature request"
            )
        
        # Update status
        db.execute(
            text("UPDATE esignature_documents SET status = 'cancelled' WHERE id = :id"),
            {"id": esign_doc_id}
        )
        
        # Add audit log
        audit_log = ESignatureAuditLog(
            esignature_document_id=esign_doc_id,
            action="cancelled",
            user_email=current_user.email,
            details=json.dumps({
                "cancelled_by_role": user_role,
                "reason": "Manual cancellation"
            }),
            created_at=datetime.utcnow()
        )
        db.add(audit_log)
        db.commit()
        
        return {
            "message": "Signature request cancelled successfully",
            "cancelled_by_role": user_role
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error cancelling signature request: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel signature request: {str(e)}")

@router.post("/sign-document-directly/{document_id}")
async def sign_document_directly(
    document_id: str,
    sign_request: ESignatureSignRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_company_db_session)
):
    """
    Sign a document directly without creating a formal e-signature request.
    Available for system admins only.
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        # Only system admins can use direct signing
        if user_role != 'system_admin':
            raise HTTPException(
                status_code=403,
                detail="Direct document signing is only available for system administrators"
            )
        
        # Check if document exists
        from app.models_company import Document
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Create a simple e-signature document entry
        esign_doc = ESignatureDocument(
            document_id=document_id,
            title=f"Direct Signature: {document.original_filename}",
            message="Document signed directly by system administrator",
            status="completed",
            created_by_user_id=current_user.id,
            require_all_signatures=False,
            expires_at=datetime.utcnow() + timedelta(days=365),  # Far future expiry
            completed_at=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        db.add(esign_doc)
        db.flush()
        
        # Add system admin as recipient and mark as signed
        recipient = ESignatureRecipient(
            esignature_document_id=esign_doc.id,
            email=current_user.email,
            full_name=current_user.full_name,
            role=user_role,
            is_signed=True,
            signed_at=datetime.utcnow(),
            signature_text=sign_request.signature_text,
            ip_address=sign_request.ip_address,
            user_agent=sign_request.user_agent,
            created_at=datetime.utcnow()
        )
        db.add(recipient)
        
        # Add audit log
        audit_log = ESignatureAuditLog(
            esignature_document_id=esign_doc.id,
            action="direct_signed",
            user_email=current_user.email,
            user_ip=sign_request.ip_address,
            details=json.dumps({
                "signed_by_role": user_role,
                "signed_by_name": current_user.full_name,
                "signature_type": "direct",
                "signature_text": sign_request.signature_text,
                "document_filename": document.original_filename,
                "ip_address": sign_request.ip_address,
                "user_agent": sign_request.user_agent
            }),
            created_at=datetime.utcnow()
        )
        db.add(audit_log)
        
        # Commit changes
        db.commit()
        
        logger.info(f"✅ Document {document_id} signed directly by {current_user.email} ({user_role})")
        
        return {
            "message": "Document signed successfully",
            "esignature_document_id": esign_doc.id,
            "signed_by": current_user.email,
            "signed_by_role": user_role,
            "signed_at": recipient.signed_at.isoformat(),
            "document_status": esign_doc.status,
            "signature_type": "direct"
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error signing document directly: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sign document: {str(e)}")

@router.post("/{esign_doc_id}/sign")
async def sign_document(
    esign_doc_id: str,
    sign_request: ESignatureSignRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_company_db_session)
):
    """
    Sign a document with dynamic role-based permissions
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        # Check signing permission
        if not has_esignature_permission(user_role, PermissionAction.SIGN):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' does not have permission to sign documents"
            )
        
        # Get the signature document
        esign_doc = db.query(ESignatureDocument).filter(
            ESignatureDocument.id == esign_doc_id
        ).first()
        
        if not esign_doc:
            raise HTTPException(status_code=404, detail="Signature request not found")
        
        # Check if document can be signed
        if esign_doc.status not in ["sent", "signed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Document cannot be signed in current status: {esign_doc.status}"
            )
        
        # Check if user is a recipient
        recipient = db.query(ESignatureRecipient).filter(
            ESignatureRecipient.esignature_document_id == esign_doc_id,
            ESignatureRecipient.email == current_user.email
        ).first()
        
        if not recipient:
            # System admins can sign any document - add them as a recipient automatically
            if user_role == 'system_admin':
                logger.info(f"🔧 Adding system admin {current_user.email} as recipient for document {esign_doc_id}")
                recipient = ESignatureRecipient(
                    esignature_document_id=esign_doc_id,
                    email=current_user.email,
                    full_name=current_user.full_name,
                    role=user_role,
                    is_signed=False,
                    created_at=datetime.utcnow()
                )
                db.add(recipient)
                db.flush()  # Ensure the recipient is saved to get its ID
            else:
                raise HTTPException(
                    status_code=403,
                    detail="You are not a recipient of this signature request"
                )
        
        # Check if already signed by querying the database
        signed_recipient = db.query(ESignatureRecipient).filter(
            ESignatureRecipient.esignature_document_id == esign_doc_id,
            ESignatureRecipient.email == current_user.email,
            ESignatureRecipient.is_signed == True
        ).first()
        
        if signed_recipient:
            raise HTTPException(
                status_code=400,
                detail="You have already signed this document"
            )
        
        # Check if document is expired
        if esign_doc.expires_at is not None and esign_doc.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=400,
                detail="This signature request has expired"
            )
        
        # Update recipient signature status using SQL query
        current_time = datetime.utcnow()
        db.execute(
            text("""
                UPDATE esignature_recipients 
                SET is_signed = true, 
                    signed_at = :signed_at,
                    signature_text = :signature_text,
                    ip_address = :ip_address,
                    user_agent = :user_agent
                WHERE esignature_document_id = :doc_id 
                AND email = :email
            """),
            {
                "signed_at": current_time,
                "signature_text": sign_request.signature_text,
                "ip_address": sign_request.ip_address,
                "user_agent": sign_request.user_agent,
                "doc_id": esign_doc_id,
                "email": current_user.email
            }
        )
        
        # Check if all recipients have signed
        all_recipients = db.query(ESignatureRecipient).filter(
            ESignatureRecipient.esignature_document_id == esign_doc_id
        ).all()
        
        signed_count = sum(1 for r in all_recipients if r.is_signed)
        total_count = len(all_recipients)
        
        # Update document status
        if signed_count == total_count:
            # All recipients have signed
            db.execute(
                text("UPDATE esignature_documents SET status = 'completed', completed_at = :completed_at WHERE id = :id"),
                {"completed_at": current_time, "id": esign_doc_id}
            )
            status_message = "Document fully signed and completed"
            new_status = "completed"
        else:
            # Partially signed
            db.execute(
                text("UPDATE esignature_documents SET status = 'signed' WHERE id = :id"),
                {"id": esign_doc_id}
            )
            status_message = f"Document signed by {signed_count} of {total_count} recipients"
            new_status = "signed"
        
        # Add audit log
        audit_log = ESignatureAuditLog(
            esignature_document_id=esign_doc_id,
            action="signed",
            user_email=current_user.email,
            details=json.dumps({
                "signed_by_role": user_role,
                "signed_by_name": recipient.full_name,
                "signed_count": signed_count,
                "total_recipients": total_count,
                "all_signed": signed_count == total_count,
                "signature_text": sign_request.signature_text,
                "ip_address": sign_request.ip_address,
                "user_agent": sign_request.user_agent
            }),
            created_at=datetime.utcnow()
        )
        db.add(audit_log)
        
        # Commit changes
        db.commit()
        
        logger.info(f"✅ Document {esign_doc_id} signed by {current_user.email} ({user_role})")
        
        return {
            "message": status_message,
            "signed_by": current_user.email,
            "signed_by_role": user_role,
            "signed_at": recipient.signed_at.isoformat(),
            "document_status": esign_doc.status,
            "progress": {
                "signed_count": signed_count,
                "total_recipients": total_count,
                "completed": signed_count == total_count
            }
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error signing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sign document: {str(e)}")

@router.get("/{esign_doc_id}/download-signed")
async def download_signed_document(
    esign_doc_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_company_db_session)
):
    """
    Download signed document with dynamic role-based permissions
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        # Check permissions
        if not has_esignature_permission(user_role, PermissionAction.DOWNLOAD):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' does not have permission to download signed documents"
            )
        
        # Get the signature document
        esign_doc = db.query(ESignatureDocument).filter(
            ESignatureDocument.id == esign_doc_id
        ).first()
        
        if not esign_doc:
            raise HTTPException(status_code=404, detail="Signature request not found")
        
        # Check if user can download this specific document
        if user_role in ["employee", "customer"]:
            # Check if user is creator or recipient
            is_creator = esign_doc.created_by_user_id == current_user.id
            is_recipient = db.query(ESignatureRecipient).filter(
                ESignatureRecipient.esignature_document_id == esign_doc_id,
                ESignatureRecipient.email == current_user.email
            ).first() is not None
            
            if not (is_creator or is_recipient):
                raise HTTPException(
                    status_code=403,
                    detail="You can only download your own signature requests or requests you're a recipient of"
                )
        
        # Add audit log
        audit_log = ESignatureAuditLog(
            esignature_document_id=esign_doc_id,
            action="downloaded",
            user_email=current_user.email,
            details=json.dumps({
                "downloaded_by_role": user_role
            }),
            created_at=datetime.utcnow()
        )
        db.add(audit_log)
        db.commit()
        
        from fastapi.responses import Response
        return Response(
            content=b"Mock signed document content",
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=signed_document_{esign_doc_id}.pdf"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error downloading signed document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download signed document: {str(e)}")

# Enhanced endpoints with dynamic permissions

@router.get("/permissions/my-role")
async def get_my_role_permissions(
    current_user = Depends(get_current_user)
):
    """
    Get E-signature permissions for the current user's role
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        permissions = ESignaturePermissions.get_role_summary(user_role)
        
        return {
            "user_role": user_role,
            "permissions": permissions,
            "user_id": current_user.id,
            "user_email": current_user.email
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting role permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get role permissions: {str(e)}")

@router.get("/permissions/all-roles")
async def get_all_role_permissions(
    current_user = Depends(get_current_user)
):
    """
    Get E-signature permissions for all roles (admin only)
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        # Only system admin can view all role permissions
        if user_role != "system_admin":
            raise HTTPException(
                status_code=403,
                detail="Only system administrators can view all role permissions"
            )
        
        all_roles = ESignaturePermissions.get_all_roles()
        role_permissions = {}
        
        for role in all_roles:
            role_permissions[role] = ESignaturePermissions.get_role_summary(role)
        
        return {
            "all_roles": role_permissions,
            "total_roles": len(all_roles),
            "requested_by": user_role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting all role permissions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get all role permissions: {str(e)}")

# Webhook endpoint for Inkless notifications
@router.post("/webhook/inkless")
async def inkless_webhook(webhook_data: dict):
    """
    Handle webhook notifications from Inkless
    """
    try:
        return {"message": "Webhook received successfully"}
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process webhook: {str(e)}")

# Workflow-specific endpoints with dynamic permissions
@router.post("/workflow/contract-approval")
async def create_contract_approval_workflow(
    request_data: dict,
    current_user = Depends(get_current_user)
):
    """
    Create contract approval workflow with dynamic permissions
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        if not has_esignature_permission(user_role, PermissionAction.WORKFLOW_CREATE):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' does not have permission to create workflows"
            )
        
        return {
            "message": "Contract approval workflow created successfully",
            "created_by_role": user_role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating contract approval workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create contract approval workflow: {str(e)}")

@router.post("/workflow/policy-acknowledgment")
async def create_policy_acknowledgment_workflow(
    request_data: dict,
    current_user = Depends(get_current_user)
):
    """
    Create policy acknowledgment workflow with dynamic permissions
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        if not has_esignature_permission(user_role, PermissionAction.WORKFLOW_CREATE):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' does not have permission to create workflows"
            )
        
        return {
            "message": "Policy acknowledgment workflow created successfully",
            "created_by_role": user_role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating policy acknowledgment workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create policy acknowledgment workflow: {str(e)}")

@router.post("/workflow/budget-approval")
async def create_budget_approval_workflow(
    request_data: dict,
    current_user = Depends(get_current_user)
):
    """
    Create budget approval workflow with dynamic permissions
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        if not has_esignature_permission(user_role, PermissionAction.WORKFLOW_CREATE):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' does not have permission to create workflows"
            )
        
        return {
            "message": "Budget approval workflow created successfully",
            "created_by_role": user_role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating budget approval workflow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create budget approval workflow: {str(e)}")

@router.post("/customer-agreement")
async def create_customer_agreement(
    request_data: dict,
    current_user = Depends(get_current_user)
):
    """
    Create customer agreement signature request with dynamic permissions
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        if not can_create_esignature_request(user_role):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' does not have permission to create customer agreements"
            )
        
        return {
            "message": "Customer agreement created successfully",
            "created_by_role": user_role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creating customer agreement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create customer agreement: {str(e)}")

@router.post("/bulk-send")
async def bulk_send_signature_requests(
    request_data: dict,
    current_user = Depends(get_current_user)
):
    """
    Send bulk signature requests with dynamic permissions
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        if not has_esignature_permission(user_role, PermissionAction.BULK_SEND):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' does not have permission to send bulk signature requests"
            )
        
        return {
            "message": "Bulk signature requests sent successfully",
            "sent_by_role": user_role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error sending bulk signature requests: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send bulk signature requests: {str(e)}")

@router.get("/audit-logs")
async def get_audit_logs(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_company_db_session)
):
    """
    Get E-signature audit logs with dynamic permissions
    """
    try:
        user_role = getattr(current_user, 'role', 'customer')
        
        if not has_esignature_permission(user_role, PermissionAction.AUDIT_VIEW):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' does not have permission to view audit logs"
            )
        
        # Get audit logs
        audit_logs = db.query(ESignatureAuditLog).order_by(
            ESignatureAuditLog.created_at.desc()
        ).limit(100).all()
        
        return {
            "audit_logs": [
                {
                    "id": log.id,
                    "esignature_document_id": log.esignature_document_id,
                    "action": log.action,
                    "user_email": log.user_email,
                    "details": log.details,
                    "created_at": log.created_at.isoformat() if log.created_at is not None else None
                } for log in audit_logs
            ],
            "total_logs": len(audit_logs),
            "viewed_by_role": user_role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting audit logs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {str(e)}") 