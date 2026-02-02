"""
Background Job Scheduler for Document Management System
Uses APScheduler for lightweight background task scheduling
"""

import logging
import asyncio
import os
from datetime import datetime
from typing import Optional

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    logging.warning("[SCHEDULER] APScheduler not installed. Background jobs disabled.")

from app.database import get_management_db

logger = logging.getLogger(__name__)


class AgentScheduler:
    """Manages background jobs for AI agents"""

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.is_running = False
        self.daily_run_hour = int(os.getenv('EXPIRY_AGENT_HOUR', '8'))
        self.daily_run_minute = int(os.getenv('EXPIRY_AGENT_MINUTE', '0'))
        self.weekly_run_day = os.getenv('EXPIRY_AGENT_WEEKLY_DAY', 'mon')

    def start(self):
        """Start the scheduler and register jobs"""
        if not SCHEDULER_AVAILABLE:
            logger.warning("[SCHEDULER] APScheduler not available. Install with: pip install apscheduler")
            return

        if self.is_running:
            logger.info("[SCHEDULER] Scheduler already running")
            return

        try:
            self.scheduler = AsyncIOScheduler()

            # Daily expiry check job - runs at configured time
            self.scheduler.add_job(
                self._run_daily_expiry_check,
                CronTrigger(
                    hour=self.daily_run_hour,
                    minute=self.daily_run_minute
                ),
                id='daily_expiry_check',
                name='Daily Document Expiry Check',
                replace_existing=True,
                misfire_grace_time=3600  # 1 hour grace time for missed jobs
            )

            # Weekly HR summary job - runs every Monday at 9 AM
            self.scheduler.add_job(
                self._run_weekly_hr_summary,
                CronTrigger(
                    day_of_week=self.weekly_run_day,
                    hour=9,
                    minute=0
                ),
                id='weekly_hr_summary',
                name='Weekly HR Expiry Summary',
                replace_existing=True,
                misfire_grace_time=3600
            )

            # Cleanup job - runs every night at 2 AM
            self.scheduler.add_job(
                self._cleanup_expired_actions,
                CronTrigger(hour=2, minute=0),
                id='cleanup_expired_actions',
                name='Cleanup Expired HR Actions',
                replace_existing=True,
                misfire_grace_time=3600
            )

            self.scheduler.start()
            self.is_running = True

            logger.info(f"[SCHEDULER] Started with jobs:")
            logger.info(f"  - Daily expiry check: {self.daily_run_hour}:{self.daily_run_minute:02d}")
            logger.info(f"  - Weekly HR summary: {self.weekly_run_day} 09:00")
            logger.info(f"  - Cleanup job: 02:00")

        except Exception as e:
            logger.error(f"[SCHEDULER] Failed to start: {e}")
            self.is_running = False

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            logger.info("[SCHEDULER] Stopped")

    async def _run_daily_expiry_check(self):
        """Execute daily expiry check for all companies"""
        logger.info("[SCHEDULER] Starting daily expiry check...")

        try:
            # Import here to avoid circular imports
            from app.services.expiry_agent_service import expiry_agent_service

            # Get management database
            db_gen = get_management_db()
            management_db = next(db_gen)

            try:
                result = await expiry_agent_service.run_expiry_check_for_all_companies(
                    management_db=management_db,
                    run_type='scheduled'
                )

                logger.info(f"[SCHEDULER] Daily expiry check completed: {result.get('status')}")
                logger.info(f"[SCHEDULER] Stats: {result.get('documents_scanned', 0)} docs scanned, "
                           f"{result.get('notifications_created', 0)} notifications, "
                           f"{result.get('emails_sent', 0)} emails")

            finally:
                management_db.close()

        except Exception as e:
            logger.error(f"[SCHEDULER] Daily expiry check failed: {e}")

    async def _run_weekly_hr_summary(self):
        """Execute weekly HR summary for all companies"""
        logger.info("[SCHEDULER] Starting weekly HR summary...")

        try:
            from app.services.expiry_agent_service import expiry_agent_service
            from app.models import Company

            db_gen = get_management_db()
            management_db = next(db_gen)

            try:
                companies = management_db.query(Company).filter(
                    Company.is_active == True
                ).all()

                for company in companies:
                    try:
                        from app.database import get_company_db

                        company_db_gen = get_company_db(str(company.id), str(company.database_url))
                        company_db = next(company_db_gen)

                        try:
                            # Get all expiring documents for weekly summary
                            expiring_docs = await expiry_agent_service.identify_expiring_documents(
                                company_db=company_db,
                                company_id=company.id,
                                days_thresholds=[7, 30, 60, 90]
                            )

                            all_expiring = (
                                expiring_docs.get('urgent', []) +
                                expiring_docs.get('upcoming', []) +
                                expiring_docs.get('future', [])
                            )

                            if all_expiring:
                                await expiry_agent_service.send_hr_summary(
                                    company_db=company_db,
                                    company_id=company.id,
                                    company_name=company.name,
                                    expiring_documents=all_expiring,
                                    summary_type='weekly'
                                )

                        finally:
                            company_db.close()

                    except Exception as e:
                        logger.error(f"[SCHEDULER] Weekly summary failed for company {company.id}: {e}")

                logger.info(f"[SCHEDULER] Weekly HR summary completed for {len(companies)} companies")

            finally:
                management_db.close()

        except Exception as e:
            logger.error(f"[SCHEDULER] Weekly HR summary failed: {e}")

    async def _cleanup_expired_actions(self):
        """Clean up expired HR chat actions that were never confirmed"""
        logger.info("[SCHEDULER] Starting cleanup of expired actions...")

        try:
            from app.models import Company
            from app.models_document_analysis import HRChatAction
            from datetime import datetime

            db_gen = get_management_db()
            management_db = next(db_gen)

            try:
                companies = management_db.query(Company).filter(
                    Company.is_active == True
                ).all()

                total_cleaned = 0

                for company in companies:
                    try:
                        from app.database import get_company_db

                        company_db_gen = get_company_db(str(company.id), str(company.database_url))
                        company_db = next(company_db_gen)

                        try:
                            # Find and mark expired pending actions
                            expired_actions = company_db.query(HRChatAction).filter(
                                HRChatAction.action_status == 'pending',
                                HRChatAction.expires_at < datetime.utcnow()
                            ).all()

                            for action in expired_actions:
                                action.action_status = 'expired'
                                total_cleaned += 1

                            company_db.commit()

                        finally:
                            company_db.close()

                    except Exception as e:
                        logger.error(f"[SCHEDULER] Cleanup failed for company {company.id}: {e}")

                logger.info(f"[SCHEDULER] Cleanup completed: {total_cleaned} expired actions marked")

            finally:
                management_db.close()

        except Exception as e:
            logger.error(f"[SCHEDULER] Cleanup failed: {e}")

    def get_status(self) -> dict:
        """Get scheduler status and job information"""
        if not self.scheduler or not self.is_running:
            return {
                'status': 'stopped',
                'jobs': []
            }

        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })

        return {
            'status': 'running',
            'jobs': jobs
        }

    async def trigger_expiry_check_now(self, triggered_by: str) -> dict:
        """Manually trigger an expiry check"""
        logger.info(f"[SCHEDULER] Manual expiry check triggered by {triggered_by}")

        try:
            from app.services.expiry_agent_service import expiry_agent_service

            db_gen = get_management_db()
            management_db = next(db_gen)

            try:
                result = await expiry_agent_service.run_expiry_check_for_all_companies(
                    management_db=management_db,
                    triggered_by=triggered_by,
                    run_type='manual'
                )
                return result

            finally:
                management_db.close()

        except Exception as e:
            logger.error(f"[SCHEDULER] Manual trigger failed: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }


# Create global scheduler instance
agent_scheduler = AgentScheduler()


def start_scheduler():
    """Start the background scheduler"""
    agent_scheduler.start()


def stop_scheduler():
    """Stop the background scheduler"""
    agent_scheduler.stop()
