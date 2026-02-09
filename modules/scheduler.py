"""
Job Search Scheduler Module
Automated scheduling using APScheduler
"""

import json
import os
from datetime import datetime
from typing import Optional, Dict, List, Callable
from pathlib import Path

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    SCHEDULER_AVAILABLE = True
except ImportError:
    SCHEDULER_AVAILABLE = False
    print("⚠️ APScheduler not installed. Scheduling unavailable.")


class JobSearchScheduler:
    """
    Schedule automated job searches with notifications.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the scheduler.
        
        Args:
            data_dir: Directory for storing user profiles and schedules
        """
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"
        self.profiles_file = self.data_dir / "user_profiles.json"
        self.scheduler = None
        self.is_running = False
        
        # Callbacks
        self.on_search_complete: Optional[Callable] = None
        self.on_notification_sent: Optional[Callable] = None
        
        if SCHEDULER_AVAILABLE:
            self.scheduler = BackgroundScheduler()
    
    def start(self) -> bool:
        """Start the scheduler."""
        if not SCHEDULER_AVAILABLE or not self.scheduler:
            print("⚠️ Scheduler not available")
            return False
        
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            print("✅ Scheduler started")
        return True
    
    def stop(self):
        """Stop the scheduler."""
        if self.scheduler and self.is_running:
            self.scheduler.shutdown(wait=False)
            self.is_running = False
            print("⏹️ Scheduler stopped")
    
    def schedule_job_search(
        self,
        user_id: str,
        frequency: str = "daily",
        hour: int = 9,
        minute: int = 0,
        search_callback: Optional[Callable] = None,
        notification_callback: Optional[Callable] = None
    ) -> bool:
        """
        Schedule a recurring job search.
        
        Args:
            user_id: Unique identifier for the user
            frequency: "daily", "weekly", or "hourly"
            hour: Hour to run (0-23) for daily/weekly
            minute: Minute to run (0-59)
            search_callback: Function to call when search runs
            notification_callback: Function to call to send notifications
            
        Returns:
            True if scheduled successfully
        """
        if not self.scheduler:
            return False
        
        job_id = f"job_search_{user_id}"
        
        # Remove existing job if any
        try:
            self.scheduler.remove_job(job_id)
        except:
            pass
        
        # Create trigger based on frequency
        if frequency == "hourly":
            trigger = IntervalTrigger(hours=1)
        elif frequency == "weekly":
            trigger = CronTrigger(day_of_week="mon", hour=hour, minute=minute)
        else:  # daily
            trigger = CronTrigger(hour=hour, minute=minute)
        
        # Create job function
        def scheduled_search():
            print(f"🔍 Running scheduled search for user: {user_id}")
            
            if search_callback:
                results = search_callback(user_id)
                
                if notification_callback and results:
                    notification_callback(user_id, results)
                    
                if self.on_search_complete:
                    self.on_search_complete(user_id, results)
        
        # Add job to scheduler
        self.scheduler.add_job(
            scheduled_search,
            trigger=trigger,
            id=job_id,
            name=f"Job Search - {user_id}",
            replace_existing=True
        )
        
        # Save schedule to profile
        self._save_schedule(user_id, frequency, hour, minute)
        
        print(f"📅 Scheduled {frequency} job search at {hour:02d}:{minute:02d}")
        return True
    
    def cancel_schedule(self, user_id: str) -> bool:
        """Cancel a user's scheduled job search."""
        if not self.scheduler:
            return False
        
        job_id = f"job_search_{user_id}"
        try:
            self.scheduler.remove_job(job_id)
            self._remove_schedule(user_id)
            print(f"❌ Cancelled schedule for user: {user_id}")
            return True
        except:
            return False
    
    def get_next_run(self, user_id: str) -> Optional[datetime]:
        """Get the next scheduled run time for a user."""
        if not self.scheduler:
            return None
        
        job_id = f"job_search_{user_id}"
        job = self.scheduler.get_job(job_id)
        
        if job and job.next_run_time:
            return job.next_run_time
        return None
    
    def _save_schedule(self, user_id: str, frequency: str, hour: int, minute: int):
        """Save schedule to user profiles file."""
        profiles = self._load_profiles()
        
        if user_id not in profiles:
            profiles[user_id] = {}
        
        profiles[user_id]["schedule"] = {
            "frequency": frequency,
            "hour": hour,
            "minute": minute,
            "enabled": True,
            "updated_at": datetime.now().isoformat()
        }
        
        self._save_profiles(profiles)
    
    def _remove_schedule(self, user_id: str):
        """Remove schedule from user profiles."""
        profiles = self._load_profiles()
        
        if user_id in profiles and "schedule" in profiles[user_id]:
            profiles[user_id]["schedule"]["enabled"] = False
            self._save_profiles(profiles)
    
    def _load_profiles(self) -> Dict:
        """Load user profiles from file."""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, "r") as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_profiles(self, profiles: Dict):
        """Save user profiles to file."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.profiles_file, "w") as f:
            json.dump(profiles, f, indent=2)


class UserProfile:
    """
    Manage user preferences and notification settings.
    """
    
    def __init__(self, user_id: str, data_dir: Optional[Path] = None):
        self.user_id = user_id
        self.data_dir = data_dir or Path(__file__).parent.parent / "data"
        self.profiles_file = self.data_dir / "user_profiles.json"
        self.data: Dict = self._load()
    
    def _load(self) -> Dict:
        """Load user profile from file."""
        profiles = {}
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, "r") as f:
                    profiles = json.load(f)
            except:
                pass
        
        return profiles.get(self.user_id, {
            "email": None,
            "phone": None,
            "notification_channel": "email",
            "schedule": None,
            "resume_data": None,
            "preferences": {}
        })
    
    def save(self):
        """Save user profile to file."""
        profiles = {}
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, "r") as f:
                    profiles = json.load(f)
            except:
                pass
        
        profiles[self.user_id] = self.data
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.profiles_file, "w") as f:
            json.dump(profiles, f, indent=2)
    
    def set_notification_preferences(
        self,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        channel: str = "email"
    ):
        """Set notification preferences."""
        if email:
            self.data["email"] = email
        if phone:
            self.data["phone"] = phone
        self.data["notification_channel"] = channel
        self.save()
    
    def set_resume_data(self, resume_data: Dict):
        """Store parsed resume data."""
        self.data["resume_data"] = resume_data
        self.save()
    
    def get_resume_data(self) -> Optional[Dict]:
        """Get stored resume data."""
        return self.data.get("resume_data")


def create_scheduler(data_dir: Optional[Path] = None) -> JobSearchScheduler:
    """Factory function to create a scheduler."""
    return JobSearchScheduler(data_dir=data_dir)
