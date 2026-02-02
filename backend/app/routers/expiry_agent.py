"""
Expiry Agent Router - API endpoints for document expiry monitoring agent
Provides manual triggers, status checks, and configuration for the expiry agent
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import logging

from app.database import get_management_db, get_company_db
from app import models, auth
from app.models_company import User as CompanyUser
from app.models_document_analysis import ExpiryAgentRun, ExpiryAgentConfig, ExpiryNotification
from app.services.expiry_agent_service import expiry_agent_service
from app.scheduler import agent_scheduler

router = APIRouter()
logger = logging.getLogger(__name__)


# ===== HR ADMIN ENDPOINTS =====

@router.get("/status")
async def get_expiry_agent_status(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get the status of the expiry agent for the current company"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")

    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)

    try:
        status = await expiry_agent_service.get_agent_status(company_db, str(company_id))

        # Add scheduler status
        scheduler_status = agent_scheduler.get_status()

        return {
            'agent_status': status,
            'scheduler_status': scheduler_status,
            'company_id': str(company_id),
            'company_name': company.name
        }

    except Exception as e:
        logger.error(f"Error getting agent status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent status: {str(e)}")
    finally:
        company_db.close()


@router.post("/trigger")
async def trigger_expiry_check(
    background_tasks: BackgroundTasks,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Manually trigger an expiry check for all companies (HR Admin only)"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")

    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    try:
        # Run the expiry check
        result = await agent_scheduler.trigger_expiry_check_now(
            triggered_by=str(current_user.id)
        )

        return {
            'message': 'Expiry check triggered successfully',
            'run_id': result.get('run_id'),
            'status': result.get('status'),
            'triggered_by': current_user.username,
            'triggered_at': datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error triggering expiry check: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger expiry check: {str(e)}")


@router.get("/notifications")
async def get_expiry_notifications(
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    limit: int = 50,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get expiry notifications for the current company"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")

    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)

    try:
        query = company_db.query(ExpiryNotification)

        if status:
            query = query.filter(ExpiryNotification.notification_status == status)

        if urgency:
            query = query.filter(ExpiryNotification.urgency_level == urgency)

        notifications = query.order_by(
            ExpiryNotification.days_until_expiry.asc()
        ).limit(limit).all()

        return {
            'notifications': [
                {
                    'id': n.id,
                    'document_id': n.document_id,
                    'user_name': n.user_name,
                    'user_email': n.user_email,
                    'notification_type': n.notification_type,
                    'expiry_date': n.expiry_date.isoformat() if n.expiry_date else None,
                    'days_until_expiry': n.days_until_expiry,
                    'urgency_level': n.urgency_level,
                    'notification_status': n.notification_status,
                    'ai_generated_reasons': n.ai_generated_reasons,
                    'recommended_action': n.recommended_action,
                    'hr_notified': n.hr_notified,
                    'reminder_count': n.reminder_count,
                    'created_at': n.created_at.isoformat() if n.created_at else None
                }
                for n in notifications
            ],
            'total': len(notifications),
            'filters': {
                'status': status,
                'urgency': urgency,
                'limit': limit
            }
        }

    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get notifications: {str(e)}")
    finally:
        company_db.close()


@router.get("/runs")
async def get_agent_runs(
    limit: int = 20,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get history of agent runs for the current company"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")

    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)

    try:
        runs = company_db.query(ExpiryAgentRun).filter(
            ExpiryAgentRun.company_id == str(company_id)
        ).order_by(
            ExpiryAgentRun.run_date.desc()
        ).limit(limit).all()

        return {
            'runs': [
                {
                    'id': run.id,
                    'run_date': run.run_date.isoformat() if run.run_date else None,
                    'run_type': run.run_type,
                    'status': run.status,
                    'documents_scanned': run.documents_scanned,
                    'notifications_sent': run.notifications_sent,
                    'emails_sent': run.emails_sent,
                    'urgent_count': run.urgent_count,
                    'upcoming_count': run.upcoming_count,
                    'future_count': run.future_count,
                    'triggered_by': run.triggered_by,
                    'duration_seconds': run.duration_seconds,
                    'error_message': run.error_message,
                    'completed_at': run.completed_at.isoformat() if run.completed_at else None
                }
                for run in runs
            ],
            'total': len(runs)
        }

    except Exception as e:
        logger.error(f"Error getting agent runs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent runs: {str(e)}")
    finally:
        company_db.close()


@router.get("/config")
async def get_agent_config(
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Get expiry agent configuration for the current company"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")

    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)

    try:
        config = company_db.query(ExpiryAgentConfig).filter(
            ExpiryAgentConfig.company_id == str(company_id)
        ).first()

        if config:
            return {
                'id': config.id,
                'company_id': config.company_id,
                'is_enabled': config.is_enabled,
                'daily_run_time': config.daily_run_time,
                'timezone': config.timezone,
                'urgent_threshold_days': config.urgent_threshold_days,
                'upcoming_threshold_days': config.upcoming_threshold_days,
                'future_threshold_days': config.future_threshold_days,
                'send_user_emails': config.send_user_emails,
                'send_hr_summary': config.send_hr_summary,
                'send_weekly_digest': config.send_weekly_digest,
                'hr_admin_emails': config.hr_admin_emails,
                'last_run_at': config.last_run_at.isoformat() if config.last_run_at else None
            }
        else:
            # Return default config
            return {
                'company_id': str(company_id),
                'is_enabled': True,
                'daily_run_time': '08:00',
                'timezone': 'UTC',
                'urgent_threshold_days': 7,
                'upcoming_threshold_days': 30,
                'future_threshold_days': 90,
                'send_user_emails': True,
                'send_hr_summary': True,
                'send_weekly_digest': True,
                'hr_admin_emails': [],
                'last_run_at': None,
                'is_default': True
            }

    except Exception as e:
        logger.error(f"Error getting agent config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get agent config: {str(e)}")
    finally:
        company_db.close()


@router.put("/config")
async def update_agent_config(
    config_update: dict,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Update expiry agent configuration for the current company"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")

    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)

    try:
        config = company_db.query(ExpiryAgentConfig).filter(
            ExpiryAgentConfig.company_id == str(company_id)
        ).first()

        if not config:
            # Create new config
            import uuid
            config = ExpiryAgentConfig(
                id=str(uuid.uuid4()),
                company_id=str(company_id)
            )
            company_db.add(config)

        # Update fields
        allowed_fields = [
            'is_enabled', 'daily_run_time', 'timezone',
            'urgent_threshold_days', 'upcoming_threshold_days', 'future_threshold_days',
            'send_user_emails', 'send_hr_summary', 'send_weekly_digest', 'hr_admin_emails'
        ]

        for field in allowed_fields:
            if field in config_update:
                setattr(config, field, config_update[field])

        company_db.commit()
        company_db.refresh(config)

        return {
            'message': 'Configuration updated successfully',
            'config': {
                'id': config.id,
                'company_id': config.company_id,
                'is_enabled': config.is_enabled,
                'daily_run_time': config.daily_run_time,
                'timezone': config.timezone,
                'urgent_threshold_days': config.urgent_threshold_days,
                'upcoming_threshold_days': config.upcoming_threshold_days,
                'future_threshold_days': config.future_threshold_days,
                'send_user_emails': config.send_user_emails,
                'send_hr_summary': config.send_hr_summary,
                'send_weekly_digest': config.send_weekly_digest,
                'hr_admin_emails': config.hr_admin_emails
            }
        }

    except Exception as e:
        logger.error(f"Error updating agent config: {e}")
        company_db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update agent config: {str(e)}")
    finally:
        company_db.close()


@router.post("/notifications/{notification_id}/dismiss")
async def dismiss_notification(
    notification_id: int,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Dismiss an expiry notification"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")

    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)

    try:
        notification = company_db.query(ExpiryNotification).filter(
            ExpiryNotification.id == notification_id
        ).first()

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        notification.notification_status = 'dismissed'
        company_db.commit()

        return {
            'message': 'Notification dismissed successfully',
            'notification_id': notification_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error dismissing notification: {e}")
        company_db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to dismiss notification: {str(e)}")
    finally:
        company_db.close()


@router.post("/notifications/{notification_id}/resend")
async def resend_notification(
    notification_id: int,
    current_user: CompanyUser = Depends(auth.get_current_company_user),
    management_db: Session = Depends(get_management_db)
):
    """Resend an expiry notification email"""
    # Check if user is HR admin
    if current_user.role not in ['hr_admin', 'hr_manager']:
        raise HTTPException(status_code=403, detail="Access denied. HR admin role required.")

    company_id = getattr(current_user, 'company_id', None)
    if not company_id:
        raise HTTPException(status_code=400, detail="User not associated with a company")

    company = management_db.query(models.Company).filter(
        models.Company.id == company_id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get company database connection
    company_db_gen = get_company_db(str(company.id), str(company.database_url))
    company_db = next(company_db_gen)

    try:
        notification = company_db.query(ExpiryNotification).filter(
            ExpiryNotification.id == notification_id
        ).first()

        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")

        # Prepare document info for email
        doc_info = {
            'document_name': f"Document {notification.document_id}",
            'document_type': 'Document',
            'expiry_date': notification.expiry_date.isoformat() if notification.expiry_date else None,
            'days_until_expiry': notification.days_until_expiry,
            'recommended_action': notification.recommended_action
        }

        # Send email
        from app.services.email_service import email_service
        success = await email_service.send_expiry_alert(
            user_email=notification.user_email,
            user_name=notification.user_name,
            document=doc_info,
            reasons=notification.ai_generated_reasons or [],
            company_name=company.name
        )

        if success:
            notification.reminder_count = (notification.reminder_count or 0) + 1
            notification.last_reminder_at = datetime.utcnow()
            company_db.commit()

            return {
                'message': 'Notification resent successfully',
                'notification_id': notification_id,
                'reminder_count': notification.reminder_count
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to send email")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending notification: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to resend notification: {str(e)}")
    finally:
        company_db.close()


# ===== SYSTEM ADMIN ENDPOINTS =====

@router.get("/system/scheduler-status")
async def get_scheduler_status(
    current_user: models.SystemUser = Depends(auth.get_current_system_user)
):
    """Get the global scheduler status (System Admin only)"""
    try:
        status = agent_scheduler.get_status()
        return {
            'scheduler': status,
            'requested_by': current_user.username,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get scheduler status: {str(e)}")


@router.post("/system/start-scheduler")
async def start_scheduler(
    current_user: models.SystemUser = Depends(auth.get_current_system_user)
):
    """Start the background scheduler (System Admin only)"""
    try:
        agent_scheduler.start()
        status = agent_scheduler.get_status()

        return {
            'message': 'Scheduler started successfully',
            'scheduler': status,
            'started_by': current_user.username,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")


@router.post("/system/stop-scheduler")
async def stop_scheduler(
    current_user: models.SystemUser = Depends(auth.get_current_system_user)
):
    """Stop the background scheduler (System Admin only)"""
    try:
        agent_scheduler.stop()

        return {
            'message': 'Scheduler stopped successfully',
            'stopped_by': current_user.username,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")


@router.post("/system/trigger-all")
async def trigger_expiry_check_all(
    current_user: models.SystemUser = Depends(auth.get_current_system_user),
    management_db: Session = Depends(get_management_db)
):
    """Manually trigger expiry check for all companies (System Admin only)"""
    try:
        result = await agent_scheduler.trigger_expiry_check_now(
            triggered_by=f"system_admin:{current_user.id}"
        )

        return {
            'message': 'Expiry check triggered for all companies',
            'run_id': result.get('run_id'),
            'status': result.get('status'),
            'companies_processed': result.get('companies_processed', 0),
            'documents_scanned': result.get('documents_scanned', 0),
            'notifications_created': result.get('notifications_created', 0),
            'triggered_by': current_user.username,
            'timestamp': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error triggering expiry check: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger expiry check: {str(e)}")
