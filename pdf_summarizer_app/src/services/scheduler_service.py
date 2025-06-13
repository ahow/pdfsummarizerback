from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import atexit
import logging
from src.models.user import User
from src.services.google_drive import GoogleDriveService
from src.services.pdf_processor import PDFProcessor
from src.services.email_service import EmailService
from src.models.pdf_summary import PDFSummary, db
import tempfile
import os

# Set up logging for the scheduler
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, app=None):
        self.scheduler = BackgroundScheduler()
        self.app = app
        
        # Configure scheduler
        self.scheduler.start()
        
        # Shut down the scheduler when exiting the app
        atexit.register(lambda: self.scheduler.shutdown())
        
    def init_app(self, app):
        """Initialize the scheduler with Flask app context."""
        self.app = app
        
    def scan_all_users_google_drive(self):
        """Scan Google Drive for all users and process new PDFs."""
        if not self.app:
            logger.error("Flask app not initialized")
            return
            
        with self.app.app_context():
            try:
                logger.info("Starting scheduled Google Drive scan for all users")
                
                users = User.query.all()
                total_processed = 0
                
                for user in users:
                    try:
                        processed_count = self._scan_user_google_drive(user)
                        total_processed += processed_count
                        logger.info(f"Processed {processed_count} files for user {user.username}")
                    except Exception as e:
                        logger.error(f"Error scanning Google Drive for user {user.username}: {e}")
                
                logger.info(f"Scheduled scan completed. Total files processed: {total_processed}")
                
            except Exception as e:
                logger.error(f"Error in scheduled Google Drive scan: {e}")
    
    def _scan_user_google_drive(self, user):
        """Scan Google Drive for a specific user."""
        try:
            # Initialize services
            drive_service = GoogleDriveService()
            pdf_processor = PDFProcessor()
            
            # Get user's Google Drive folder ID (if specified)
            folder_id = user.google_drive_folder_id
            
            # List new PDF files from the last week
            files = drive_service.list_files(folder_id=folder_id, days_back=7)
            
            processed_count = 0
            
            for file in files:
                try:
                    # Check if we've already processed this file
                    existing_summary = PDFSummary.query.filter_by(
                        user_id=user.id,
                        google_drive_link=file['webViewLink']
                    ).first()
                    
                    if existing_summary:
                        continue  # Skip already processed files
                    
                    # Download the file to a temporary location
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                        temp_path = temp_file.name
                    
                    if drive_service.download_file(file['id'], temp_path):
                        # Process the PDF
                        result = pdf_processor.process_pdf(temp_path, file['name'])
                        
                        # Create summary record
                        summary = PDFSummary(
                            user_id=user.id,
                            title=result['title'],
                            file_path=file['name'],
                            google_drive_link=file['webViewLink'],
                            summary=result['summary'],
                            key_messages='\n'.join(result['key_messages']) if result['key_messages'] else '',
                            date_added=datetime.fromisoformat(file['createdTime'].replace('Z', '+00:00')),
                            date_processed=datetime.utcnow()
                        )
                        
                        db.session.add(summary)
                        processed_count += 1
                    
                    # Clean up temporary file
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)
                        
                except Exception as e:
                    logger.error(f"Error processing file {file['name']} for user {user.username}: {e}")
            
            # Commit all changes for this user
            db.session.commit()
            
            return processed_count
            
        except Exception as e:
            logger.error(f"Error in _scan_user_google_drive for user {user.username}: {e}")
            return 0
    
    def send_weekly_summaries(self):
        """Send weekly summary emails to all users."""
        if not self.app:
            logger.error("Flask app not initialized")
            return
            
        with self.app.app_context():
            try:
                logger.info("Starting scheduled weekly summary email sending")
                
                email_service = EmailService()
                results = email_service.send_weekly_summaries_to_all_users()
                
                successful = sum(1 for r in results if r['success'])
                total = len(results)
                
                logger.info(f"Weekly summary emails sent to {successful}/{total} users")
                
                # Log any failures
                for result in results:
                    if not result['success']:
                        logger.error(f"Failed to send email to user {result['username']}: {result['message']}")
                
            except Exception as e:
                logger.error(f"Error in scheduled weekly summary sending: {e}")
    
    def schedule_weekly_tasks(self):
        """Schedule the weekly tasks."""
        try:
            # Schedule Google Drive scan every Monday at 6:00 AM
            self.scheduler.add_job(
                func=self.scan_all_users_google_drive,
                trigger=CronTrigger(day_of_week='mon', hour=6, minute=0),
                id='weekly_drive_scan',
                name='Weekly Google Drive Scan',
                replace_existing=True
            )
            
            # Schedule weekly summary emails every Monday at 9:00 AM
            self.scheduler.add_job(
                func=self.send_weekly_summaries,
                trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
                id='weekly_email_summary',
                name='Weekly Email Summary',
                replace_existing=True
            )
            
            logger.info("Weekly tasks scheduled successfully")
            logger.info("- Google Drive scan: Every Monday at 6:00 AM")
            logger.info("- Email summaries: Every Monday at 9:00 AM")
            
        except Exception as e:
            logger.error(f"Error scheduling weekly tasks: {e}")
    
    def schedule_test_tasks(self):
        """Schedule test tasks that run more frequently for testing purposes."""
        try:
            # Schedule Google Drive scan every 5 minutes for testing
            self.scheduler.add_job(
                func=self.scan_all_users_google_drive,
                trigger='interval',
                minutes=5,
                id='test_drive_scan',
                name='Test Google Drive Scan',
                replace_existing=True
            )
            
            # Schedule weekly summary emails every 10 minutes for testing
            self.scheduler.add_job(
                func=self.send_weekly_summaries,
                trigger='interval',
                minutes=10,
                id='test_email_summary',
                name='Test Email Summary',
                replace_existing=True
            )
            
            logger.info("Test tasks scheduled successfully")
            logger.info("- Google Drive scan: Every 5 minutes")
            logger.info("- Email summaries: Every 10 minutes")
            
        except Exception as e:
            logger.error(f"Error scheduling test tasks: {e}")
    
    def get_scheduled_jobs(self):
        """Get information about scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def remove_job(self, job_id):
        """Remove a scheduled job."""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Job {job_id} removed successfully")
            return True
        except Exception as e:
            logger.error(f"Error removing job {job_id}: {e}")
            return False
    
    def run_job_now(self, job_id):
        """Run a scheduled job immediately."""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.func()
                logger.info(f"Job {job_id} executed successfully")
                return True
            else:
                logger.error(f"Job {job_id} not found")
                return False
        except Exception as e:
            logger.error(f"Error running job {job_id}: {e}")
            return False

