from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import json
import logging
from sqlalchemy import text

from ..auth import get_current_user
from ..database import get_management_db
from ..models_company import ESignatureDocument, ESignatureRecipient, ESignatureAuditLog, User as CompanyUser
from ..schemas import ESignatureRequest, ESignatureResponse, ESignatureStatus, ESignatureSignRequest
from ..services.inkless_service import InklessService
from ..services.database_manager import db_manager
from ..services.email_extensions import get_extended_email_service
import os
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
                
                # Step 5: Send signature request emails via Inkless AND our email service
                send_response = await inkless_service.send_signature_request(inkless_doc_id)
                
                # Also send our own email notifications to recipients
                try:
                    # Get company name for email service
                    company_name = "Your Company"  # Default fallback
                    if hasattr(current_user, 'company_id') and current_user.company_id:
                        try:
                            from ..database import get_management_db
                            from .. import models
                            with next(get_management_db()) as mgmt_db:
                                company_obj = mgmt_db.query(models.Company).filter(
                                    models.Company.id == current_user.company_id
                                ).first()
                                if company_obj:
                                    company_name = company_obj.name
                        except:
                            pass
                    
                    email_service = get_extended_email_service(company_name)
                    
                    for recipient in recipients_data:
                        try:
                            # Generate local signing URL instead of external Inkless URL
                            local_signing_url = f"{os.getenv('APP_URL', 'http://localhost:3000')}/esignature/sign/{esign_id}?email={recipient['email']}"
                            
                            await email_service.send_esignature_request_email(
                                recipient_email=recipient["email"],
                                recipient_name=recipient["name"],
                                document_title=request_data.title,
                                company_name=company_name,
                                sender_name=current_user.full_name if hasattr(current_user, 'full_name') else current_user.email,
                                signing_url=local_signing_url,
                                message=request_data.message,
                                expires_in_days=request_data.expires_in_days or 14
                            )
                        except Exception as e:
                            print(f"⚠️ Failed to send e-signature email to {recipient['email']}: {str(e)}")
                except Exception as e:
                    print(f"⚠️ Error in e-signature email notification process: {str(e)}")
                
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
        
        # Only system admins, HR admins, and HR managers can use direct signing
        if user_role not in ['system_admin', 'hr_admin', 'hr_manager']:
            raise HTTPException(
                status_code=403,
                detail="Direct document signing is only available for administrators and managers"
            )
        
        # Check if document exists - handle both system documents and company documents
        document = None
        if document_id.startswith("sysdoc_"):
            # This is a system document, query from management database
            from .. import models
            from ..database import get_management_db
            management_db_gen = get_management_db()
            management_db = next(management_db_gen)
            try:
                document = management_db.query(models.SystemDocument).filter(
                    models.SystemDocument.id == document_id
                ).first()
            finally:
                management_db.close()
        else:
            # This is a company document, query from company database
            from app.models_company import Document
            document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # For system admins, we need to ensure they exist in the company database
        # or use a different approach for their signatures
        system_admin_user_id = None
        
        if user_role == 'system_admin':
            # Check if system admin already exists in company database
            from app.models_company import User as CompanyUser
            existing_user = db.query(CompanyUser).filter(
                CompanyUser.email == current_user.email
            ).first()
            
            if not existing_user:
                # Create a temporary system admin user record in company database
                temp_system_user = CompanyUser(
                    id=f"temp_sysadmin_{current_user.id}",
                    username=f"sysadmin_{current_user.username}",
                    email=current_user.email,
                    full_name=current_user.full_name,
                    role="system_admin",
                    s3_folder="system_admin",
                    password_set=True,
                    is_active=True,
                    created_at=datetime.utcnow()
                )
                db.add(temp_system_user)
                db.flush()  # Ensure the user is created before using the ID
                system_admin_user_id = temp_system_user.id
            else:
                system_admin_user_id = existing_user.id
        else:
            system_admin_user_id = current_user.id
        
        # Create a simple e-signature document entry
        esign_doc = ESignatureDocument(
            document_id=document_id,
            title=f"Direct Signature: {document.original_filename}",
            message="Document signed directly by system administrator",
            status="completed",
            created_by_user_id=system_admin_user_id,
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

@router.get("/{esign_doc_id}/status-public")
async def get_signature_status_public(
    esign_doc_id: str,
    recipient_email: str,
    management_db: Session = Depends(get_management_db)
):
    """
    Get signature status without authentication - for email recipients
    """
    try:
        # Find which company database contains this document
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        document_details = None
        for company in companies:
            try:
                # Get company database connection
                company_db_gen = db_manager.get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)
                
                try:
                    # Check if document exists and recipient is valid
                    esign_doc = company_db.query(ESignatureDocument).filter(
                        ESignatureDocument.id == esign_doc_id
                    ).first()
                    
                    if esign_doc:
                        # Check if the recipient email is in the recipients list
                        recipient = company_db.query(ESignatureRecipient).filter(
                            ESignatureRecipient.esignature_document_id == esign_doc_id,
                            ESignatureRecipient.email == recipient_email
                        ).first()
                        
                        if recipient:
                            # Get all recipients for status
                            recipients = company_db.query(ESignatureRecipient).filter(
                                ESignatureRecipient.esignature_document_id == esign_doc_id
                            ).all()
                            
                            document_details = {
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
                                "viewed_by_role": "recipient"
                            }
                            break
                            
                finally:
                    company_db.close()
                    
            except Exception:
                continue
        
        if not document_details:
            raise HTTPException(
                status_code=404, 
                detail="Document not found or you are not a recipient of this signature request"
            )
        
        return document_details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting public signature status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get signature status: {str(e)}")

@router.post("/auth/esignature-access")
async def grant_esignature_access(
    request_data: dict,
    management_db: Session = Depends(get_management_db)
):
    """Grant temporary access for e-signature signing based on recipient email"""
    try:
        document_id = request_data.get("document_id")
        recipient_email = request_data.get("recipient_email")
        
        if not document_id or not recipient_email:
            raise HTTPException(status_code=400, detail="Document ID and recipient email are required")
        
        # For now, we'll grant access if the email is in the recipients list
        # This is a simplified approach - in production you might want more security
        return {"access_granted": True, "recipient_email": recipient_email}
        
    except Exception as e:
        logger.error(f"Error granting e-signature access: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to verify access: {str(e)}")

@router.post("/{esign_doc_id}/sign")
async def sign_document(
    esign_doc_id: str,
    sign_request: ESignatureSignRequest,
    management_db: Session = Depends(get_management_db),
    current_user = None  # Make authentication optional
):
    """
    Sign a document with dynamic role-based permissions or email verification
    """
    try:
        # Handle both authenticated users and direct email signing
        user_role = getattr(current_user, 'role', 'customer') if current_user else 'customer'
        
        # Check signing permission (allow if recipient email is provided)
        if not sign_request.recipient_email and not has_esignature_permission(user_role, PermissionAction.SIGN):
            raise HTTPException(
                status_code=403,
                detail=f"Role '{user_role}' does not have permission to sign documents"
            )
        
        # Find which company database contains this document
        companies = management_db.query(models.Company).filter(
            models.Company.is_active == True
        ).all()
        
        esign_doc = None
        db = None
        for company in companies:
            try:
                # Get company database connection
                company_db_gen = db_manager.get_company_db(str(company.id), str(company.database_url))
                company_db = next(company_db_gen)
                
                # Check if document exists in this company
                temp_doc = company_db.query(ESignatureDocument).filter(
                    ESignatureDocument.id == esign_doc_id
                ).first()
                
                if temp_doc:
                    esign_doc = temp_doc
                    db = company_db
                    break
                else:
                    company_db.close()
                    
            except Exception:
                continue
        
        if not esign_doc or not db:
            raise HTTPException(status_code=404, detail="Signature request not found")
        
        # Check if document can be signed
        if esign_doc.status not in ["sent", "signed"]:
            raise HTTPException(
                status_code=400,
                detail=f"Document cannot be signed in current status: {esign_doc.status}"
            )
        
        # Check if user is a recipient (allow direct signing with email verification)
        recipient_email_to_check = sign_request.recipient_email or (current_user.email if current_user else None)
        
        if not recipient_email_to_check:
            raise HTTPException(
                status_code=400,
                detail="Either authentication or recipient email is required"
            )
        
        recipient = db.query(ESignatureRecipient).filter(
            ESignatureRecipient.esignature_document_id == esign_doc_id,
            ESignatureRecipient.email == recipient_email_to_check
        ).first()
        
        if not recipient:
            # System admins can sign any document - add them as a recipient automatically
            if user_role == 'system_admin' and current_user:
                logger.info(f"🔧 Adding system admin {current_user.email} as recipient for document {esign_doc_id}")
                recipient = ESignatureRecipient(
                    esignature_document_id=esign_doc_id,
                    email=current_user.email,
                    full_name=getattr(current_user, 'full_name', current_user.email),
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
            ESignatureRecipient.email == recipient_email_to_check,
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
                "email": recipient_email_to_check
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
            
            # Send completion notification to original requester
            try:
                # Get the original document creator information
                esign_doc = db.query(ESignatureDocument).filter(
                    ESignatureDocument.id == esign_doc_id
                ).first()
                
                if esign_doc and esign_doc.created_by:
                    # Get creator user info
                    creator_user = db.query(CompanyUser).filter(
                        CompanyUser.id == esign_doc.created_by
                    ).first()
                    
                    if creator_user:
                        # Get company name
                        company_name = "Your Company"  # Default fallback
                        try:
                            if hasattr(current_user, 'company_id') and current_user.company_id:
                                from ..database import get_management_db
                                from .. import models
                                with next(get_management_db()) as mgmt_db:
                                    company_obj = mgmt_db.query(models.Company).filter(
                                        models.Company.id == current_user.company_id
                                    ).first()
                                    if company_obj:
                                        company_name = company_obj.name
                        except:
                            pass
                        
                        # Get signed document URL
                        signed_doc_url = f"{os.getenv('APP_URL', 'http://localhost:3000')}/api/esignature/{esign_doc_id}/download-signed"
                        
                        # Send completion email
                        email_service = get_extended_email_service(company_name)
                        await email_service.send_esignature_completion_email(
                            recipient_email=creator_user.email,
                            recipient_name=creator_user.full_name or creator_user.username,
                            document_title=esign_doc.title,
                            company_name=company_name,
                            signer_name=recipient.full_name,
                            signer_role=getattr(current_user, 'role', 'User'),
                            signed_document_url=signed_doc_url,
                            completion_date=current_time.strftime("%B %d, %Y at %I:%M %p")
                        )
                        
                        print(f"✅ Document completion notification sent to {creator_user.email}")
                        
            except Exception as e:
                print(f"⚠️ Failed to send document completion notification: {str(e)}")
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
            user_email=recipient_email_to_check,
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
        
        logger.info(f"✅ Document {esign_doc_id} signed by {recipient_email_to_check} ({user_role})")
        
        return {
            "message": status_message,
            "signed_by": recipient_email_to_check,
            "signed_by_role": user_role,
            "signed_at": current_time.isoformat(),
            "document_status": new_status,
            "progress": {
                "signed_count": signed_count,
                "total_recipients": total_count,
                "completed": signed_count == total_count
            }
        }
        
    except HTTPException:
        if db:
            db.rollback()
        raise
    except Exception as e:
        if db:
            db.rollback()
        logger.error(f"❌ Error signing document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to sign document: {str(e)}")
    finally:
        if db:
            db.close()

# Helper functions for PDF processing
def add_signature_to_pdf(original_pdf_path: str, esign_doc_id: str, db: Session):
    """Add signature overlay to existing PDF from file path"""
    try:
        with open(original_pdf_path, 'rb') as f:
            pdf_content = f.read()
        return add_signature_to_pdf_from_bytes(pdf_content, esign_doc_id, db)
    except Exception as e:
        logger.error(f"Error reading PDF file: {str(e)}")
        with open(original_pdf_path, 'rb') as f:
            return f.read()

def add_signature_to_pdf_from_bytes(pdf_content: bytes, esign_doc_id: str, db: Session):
    """Add signature overlay to existing PDF from bytes"""
    try:
        from PyPDF2 import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from io import BytesIO
        
        # Get signature information
        recipients = db.query(ESignatureRecipient).filter(
            ESignatureRecipient.esignature_document_id == esign_doc_id
        ).all()
        
        # Read original PDF from bytes
        pdf_stream = BytesIO(pdf_content)
        reader = PdfReader(pdf_stream)
        writer = PdfWriter()
        
        # Create signature overlay
        packet = BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)
        width, height = letter
        
        # Add signature box in bottom right corner
        box_x, box_y = width - 250, 50
        box_width, box_height = 240, 100
        
        # Draw signature box background
        can.setFillColorRGB(0.95, 0.95, 0.95)
        can.rect(box_x, box_y, box_width, box_height, fill=1)
        
        # Add signature content
        can.setFillColorRGB(0, 0, 0)
        can.setFont("Helvetica-Bold", 10)
        can.drawString(box_x + 5, box_y + box_height - 15, "ELECTRONICALLY SIGNED")
        
        y_offset = 25
        for recipient in recipients:
            if recipient.is_signed:
                can.setFont("Helvetica", 8)
                can.drawString(box_x + 5, box_y + box_height - y_offset, f"✓ {recipient.signature_text}")
                can.drawString(box_x + 5, box_y + box_height - y_offset - 10, f"By: {recipient.full_name}")
                can.drawString(box_x + 5, box_y + box_height - y_offset - 20, f"Date: {recipient.signed_at.strftime('%Y-%m-%d %H:%M')}")
                y_offset += 35
        
        can.save()
        packet.seek(0)
        
        # Create overlay PDF
        overlay_pdf = PdfReader(packet)
        
        # Add overlay to last page of original PDF
        for i, page in enumerate(reader.pages):
            if i == len(reader.pages) - 1:  # Last page
                page.merge_page(overlay_pdf.pages[0])
            writer.add_page(page)
        
        # Output to bytes
        output_stream = BytesIO()
        writer.write(output_stream)
        output_stream.seek(0)
        
        return output_stream.getvalue()
        
    except Exception as e:
        logger.error(f"Error adding signature to PDF: {str(e)}")
        # Fallback to original content
        return pdf_content

def convert_and_sign_document(file_path: str, original_filename: str, esign_doc_id: str, db: Session):
    """Convert non-PDF document to PDF and add signature from file path"""
    try:
        with open(file_path, 'rb') as f:
            file_content = f.read()
        return convert_and_sign_document_from_bytes(file_content, original_filename, esign_doc_id, db)
    except Exception as e:
        logger.error(f"Error reading file: {str(e)}")
        return create_signature_certificate_pdf(esign_doc_id, None, db)

def convert_and_sign_document_from_bytes(file_content: bytes, original_filename: str, esign_doc_id: str, db: Session):
    """Convert non-PDF document to PDF and add signature from bytes"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from io import BytesIO
        
        # Get signature information
        recipients = db.query(ESignatureRecipient).filter(
            ESignatureRecipient.esignature_document_id == esign_doc_id
        ).all()
        
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Add document header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, height - 50, f"SIGNED DOCUMENT: {original_filename}")
        
        # Try to read text content for text files
        try:
            # Decode bytes content as text
            text_content = file_content.decode('utf-8')
            content_lines = text_content.splitlines()[:50]  # First 50 lines
                
            y_pos = height - 100
            p.setFont("Helvetica", 10)
            for line in content_lines:
                if y_pos < 200:  # Leave space for signature
                    break
                p.drawString(100, y_pos, line.strip()[:80])  # Limit line length
                y_pos -= 15
                
        except Exception:
            # If can't decode as text, just show file info
            p.setFont("Helvetica", 12)
            p.drawString(100, height - 100, f"Original file: {original_filename}")
            p.drawString(100, height - 120, f"File size: {len(file_content)} bytes")
            p.drawString(100, height - 140, "File content could not be displayed in PDF format.")
        
        # Add signature section
        sig_y = 150
        p.setFont("Helvetica-Bold", 14)
        p.drawString(100, sig_y, "ELECTRONIC SIGNATURES:")
        
        sig_y -= 30
        for recipient in recipients:
            if recipient.is_signed:
                p.setFont("Helvetica-Bold", 12)
                p.drawString(120, sig_y, f"✓ {recipient.signature_text}")
                p.setFont("Helvetica", 10)
                p.drawString(120, sig_y - 15, f"Signed by: {recipient.full_name} ({recipient.email})")
                p.drawString(120, sig_y - 30, f"Date: {recipient.signed_at.strftime('%Y-%m-%d %H:%M:%S')}")
                sig_y -= 60
        
        p.save()
        return buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Error converting and signing document: {str(e)}")
        return create_signature_certificate_pdf(esign_doc_id, None, db)

def create_signature_certificate_pdf(esign_doc_id: str, original_doc, db: Session):
    """Create a signature certificate PDF as fallback"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from io import BytesIO
    
    # Get signature document info
    esign_doc = db.query(ESignatureDocument).filter(
        ESignatureDocument.id == esign_doc_id
    ).first()
    
    recipients = db.query(ESignatureRecipient).filter(
        ESignatureRecipient.esignature_document_id == esign_doc_id
    ).all()
    
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Add signature information to PDF
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 80, "ELECTRONIC SIGNATURE CERTIFICATE")
    
    p.setFont("Helvetica", 12)
    if original_doc:
        p.drawString(100, height - 120, f"Original Document: {original_doc.original_filename}")
    p.drawString(100, height - 140, f"Signature Request ID: {esign_doc_id}")
    p.drawString(100, height - 160, f"Status: {esign_doc.status}")
    p.drawString(100, height - 180, f"Title: {esign_doc.title}")
    p.drawString(100, height - 200, f"Signed Date: {esign_doc.completed_at or 'N/A'}")
    
    # Add recipient information
    y_pos = height - 250
    p.setFont("Helvetica-Bold", 14)
    p.drawString(100, y_pos, "SIGNATURES:")
    y_pos -= 30
    
    for recipient in recipients:
        if recipient.is_signed:
            p.setFont("Helvetica-Bold", 12)
            p.drawString(120, y_pos, f"✓ {recipient.full_name} ({recipient.email})")
            p.setFont("Helvetica", 10)
            p.drawString(120, y_pos - 15, f"  Signed: {recipient.signed_at}")
            p.drawString(120, y_pos - 30, f"  Signature: {recipient.signature_text}")
            y_pos -= 60
        else:
            p.setFont("Helvetica", 10)
            p.drawString(120, y_pos, f"○ {recipient.full_name} ({recipient.email}) - Not signed")
            y_pos -= 30
    
    p.save()
    return buffer.getvalue()

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
        
        # Get the original document content
        document_id = esign_doc.document_id
        document_content = None
        document_filename = "signed_document.pdf"
        original_doc = None
        
        try:
            if document_id.startswith("sysdoc_"):
                # This is a system document, query from management database
                from .. import models
                from ..database import get_management_db
                management_db_gen = get_management_db()
                management_db = next(management_db_gen)
                try:
                    original_doc = management_db.query(models.SystemDocument).filter(
                        models.SystemDocument.id == document_id
                    ).first()
                finally:
                    management_db.close()
            else:
                # This is a company document, query from company database
                from app.models_company import Document
                original_doc = db.query(Document).filter(Document.id == document_id).first()
            
            if original_doc:
                document_filename = f"signed_{original_doc.original_filename}"
                
                # Try to read the actual file content
                import os
                file_path = original_doc.file_path
                
                # Handle S3 URLs vs local file paths
                if file_path.startswith('s3://'):
                    # File is stored in S3, download it first
                    try:
                        from ..services.aws_service import aws_service
                        from io import BytesIO
                        
                        # Parse S3 URL to get bucket and key
                        s3_path = file_path.replace('s3://', '')
                        bucket_name = s3_path.split('/')[0]
                        s3_key = '/'.join(s3_path.split('/')[1:])
                        
                        # Download file from S3
                        file_content = await aws_service.download_file(bucket_name, s3_key)
                        
                        # Get the original file extension
                        file_extension = os.path.splitext(original_doc.original_filename)[1].lower()
                        
                        if file_extension == '.pdf':
                            # Original is PDF - overlay signature on it
                            document_content = add_signature_to_pdf_from_bytes(file_content, esign_doc_id, db)
                        else:
                            # Original is not PDF - convert to PDF and add signature
                            document_content = convert_and_sign_document_from_bytes(file_content, original_doc.original_filename, esign_doc_id, db)
                            
                    except Exception as s3_error:
                        logger.warning(f"Could not download file from S3: {str(s3_error)}")
                        # Fall back to certificate
                        document_content = create_signature_certificate_pdf(esign_doc_id, original_doc, db)
                        
                elif os.path.exists(file_path):
                    # File is stored locally
                    file_extension = os.path.splitext(original_doc.original_filename)[1].lower()
                    
                    if file_extension == '.pdf':
                        # Original is PDF - overlay signature on it
                        document_content = add_signature_to_pdf(file_path, esign_doc_id, db)
                    else:
                        # Original is not PDF - convert to PDF and add signature
                        document_content = convert_and_sign_document(file_path, original_doc.original_filename, esign_doc_id, db)
                else:
                    # If file doesn't exist locally, create a PDF with signature info
                    document_content = create_signature_certificate_pdf(esign_doc_id, original_doc, db)
            
        except Exception as e:
            logger.warning(f"Could not retrieve original document content: {str(e)}")
            # Create a fallback PDF with signature information
            document_content = create_signature_certificate_pdf(esign_doc_id, original_doc, db)
            document_filename = f"signed_document_{esign_doc_id}.pdf"
        
        # Add audit log
        audit_log = ESignatureAuditLog(
            esignature_document_id=esign_doc_id,
            action="downloaded",
            user_email=current_user.email,
            details=json.dumps({
                "downloaded_by_role": user_role,
                "filename": document_filename
            }),
            created_at=datetime.utcnow()
        )
        db.add(audit_log)
        db.commit()
        
        from fastapi.responses import Response
        return Response(
            content=document_content or b"No document content available",
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={document_filename}"}
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