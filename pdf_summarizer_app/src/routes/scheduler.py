from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from src.services.scheduler_service import SchedulerService

scheduler_bp = Blueprint('scheduler', __name__)

# This will be initialized in main.py
scheduler_service = None

def init_scheduler_routes(scheduler):
    """Initialize the scheduler routes with the scheduler service."""
    global scheduler_service
    scheduler_service = scheduler

@scheduler_bp.route('/jobs', methods=['GET'])
@login_required
def get_scheduled_jobs():
    """Get information about all scheduled jobs."""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler not initialized'}), 500
        
        jobs = scheduler_service.get_scheduled_jobs()
        return jsonify({'jobs': jobs}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to get scheduled jobs: {str(e)}'}), 500

@scheduler_bp.route('/jobs/<job_id>/run', methods=['POST'])
@login_required
def run_job_now(job_id):
    """Run a scheduled job immediately."""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler not initialized'}), 500
        
        success = scheduler_service.run_job_now(job_id)
        
        if success:
            return jsonify({'message': f'Job {job_id} executed successfully'}), 200
        else:
            return jsonify({'error': f'Failed to run job {job_id}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to run job: {str(e)}'}), 500

@scheduler_bp.route('/jobs/<job_id>', methods=['DELETE'])
@login_required
def remove_job(job_id):
    """Remove a scheduled job."""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler not initialized'}), 500
        
        success = scheduler_service.remove_job(job_id)
        
        if success:
            return jsonify({'message': f'Job {job_id} removed successfully'}), 200
        else:
            return jsonify({'error': f'Failed to remove job {job_id}'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Failed to remove job: {str(e)}'}), 500

@scheduler_bp.route('/schedule-weekly', methods=['POST'])
@login_required
def schedule_weekly_tasks():
    """Schedule the weekly tasks (Google Drive scan and email summaries)."""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler not initialized'}), 500
        
        scheduler_service.schedule_weekly_tasks()
        return jsonify({'message': 'Weekly tasks scheduled successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to schedule weekly tasks: {str(e)}'}), 500

@scheduler_bp.route('/schedule-test', methods=['POST'])
@login_required
def schedule_test_tasks():
    """Schedule test tasks that run more frequently for testing purposes."""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler not initialized'}), 500
        
        scheduler_service.schedule_test_tasks()
        return jsonify({'message': 'Test tasks scheduled successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to schedule test tasks: {str(e)}'}), 500

@scheduler_bp.route('/scan-now', methods=['POST'])
@login_required
def scan_google_drive_now():
    """Manually trigger Google Drive scan for all users."""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler not initialized'}), 500
        
        scheduler_service.scan_all_users_google_drive()
        return jsonify({'message': 'Google Drive scan completed'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to scan Google Drive: {str(e)}'}), 500

@scheduler_bp.route('/send-summaries-now', methods=['POST'])
@login_required
def send_weekly_summaries_now():
    """Manually trigger weekly summary emails for all users."""
    try:
        if not scheduler_service:
            return jsonify({'error': 'Scheduler not initialized'}), 500
        
        scheduler_service.send_weekly_summaries()
        return jsonify({'message': 'Weekly summaries sent'}), 200
        
    except Exception as e:
        return jsonify({'error': f'Failed to send weekly summaries: {str(e)}'}), 500

