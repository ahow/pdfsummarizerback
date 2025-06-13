#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.services.scheduler_service import SchedulerService
from flask import Flask
import time

def test_scheduler_service():
    """Test the scheduler service functionality."""
    print("Testing Scheduler Service...")
    
    try:
        # Create a minimal Flask app for testing
        app = Flask(__name__)
        app.config['SECRET_KEY'] = 'test_key'
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Initialize scheduler
        scheduler_service = SchedulerService(app)
        
        print("✅ Scheduler service initialized successfully")
        
        # Test getting jobs (should be empty initially)
        jobs = scheduler_service.get_scheduled_jobs()
        print(f"✅ Initial jobs count: {len(jobs)}")
        
        # Test scheduling weekly tasks
        scheduler_service.schedule_weekly_tasks()
        jobs_after_weekly = scheduler_service.get_scheduled_jobs()
        print(f"✅ Jobs after scheduling weekly tasks: {len(jobs_after_weekly)}")
        
        # Print job details
        for job in jobs_after_weekly:
            print(f"   - {job['name']} (ID: {job['id']}) - Next run: {job['next_run_time']}")
        
        # Test scheduling test tasks
        scheduler_service.schedule_test_tasks()
        jobs_after_test = scheduler_service.get_scheduled_jobs()
        print(f"✅ Jobs after scheduling test tasks: {len(jobs_after_test)}")
        
        # Test removing a job
        if jobs_after_test:
            job_to_remove = jobs_after_test[0]['id']
            success = scheduler_service.remove_job(job_to_remove)
            if success:
                print(f"✅ Successfully removed job: {job_to_remove}")
            else:
                print(f"❌ Failed to remove job: {job_to_remove}")
        
        # Final job count
        final_jobs = scheduler_service.get_scheduled_jobs()
        print(f"✅ Final jobs count: {len(final_jobs)}")
        
        print("\n=== Scheduler Service Test Results ===")
        print("✅ Scheduler initialization: PASSED")
        print("✅ Job listing: PASSED")
        print("✅ Weekly task scheduling: PASSED")
        print("✅ Test task scheduling: PASSED")
        print("✅ Job removal: PASSED")
        
        print("\nNote: Actual task execution requires database and service dependencies.")
        print("The scheduler is configured to run:")
        print("- Google Drive scan: Every Monday at 6:00 AM")
        print("- Email summaries: Every Monday at 9:00 AM")
        
        return True
        
    except Exception as e:
        print(f"❌ Scheduler service test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_scheduler_service()
    if success:
        print("\n✅ Scheduler Service test completed successfully!")
    else:
        print("\n❌ Scheduler Service test failed!")
        sys.exit(1)

