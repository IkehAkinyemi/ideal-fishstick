from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from typing import Callable, Dict, Any
import logging
import atexit
from datetime import datetime

class Scheduler:
    def __init__(self):
        """
        Initialize persistent scheduler with:
        - SQLite job store
        - Thread pool executor
        - Automatic shutdown handler
        """
        self.logger = self._setup_logging()
        self.scheduler = self._init_scheduler()
        atexit.register(self.shutdown)

    def _setup_logging(self) -> logging.Logger:
        """Configure scheduler-specific logging"""
        logger = logging.getLogger("scheduler")
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler("data/scheduler.log")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger

    def _init_scheduler(self) -> BackgroundScheduler:
        """Initialize scheduler with persistent storage"""
        jobstores = {
            'default': SQLAlchemyJobStore(
                url='sqlite:///data/scheduler.db',
                engine_options={'connect_args': {'check_same_thread': False}}
            )
        }
        
        executors = {
            'default': ThreadPoolExecutor(5)
        }
        
        scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            timezone="UTC",
            misfire_grace_time=3600  # 1 hour grace period
        )
        
        scheduler.start()
        self.logger.info("Scheduler initialized with SQLite backend")
        return scheduler

    def add_job(
        self,
        func: Callable,
        trigger_type: str = "date",
        run_date: datetime = None,
        interval: int = None,
        args: tuple = None,
        kwargs: Dict[str, Any] = None,
        job_id: str = None,
        replace_existing: bool = True
    ) -> str:
        """
        Schedule a new job with flexible triggering
        Args:
            func: Callable to execute
            trigger_type: "date"|"interval"|"cron"
            run_date: Specific datetime for "date" trigger
            interval: Seconds for "interval" trigger
            args: Positional arguments for func
            kwargs: Keyword arguments for func
            job_id: Unique identifier for job
            replace_existing: Whether to update existing job
        Returns:
            Job ID string
        """
        try:
            trigger_args = {}
            if trigger_type == "date" and run_date:
                trigger_args["run_date"] = run_date
            elif trigger_type == "interval" and interval:
                trigger_args["seconds"] = interval
            
            job = self.scheduler.add_job(
                func=func,
                trigger=trigger_type,
                id=job_id,
                args=args,
                kwargs=kwargs,
                replace_existing=replace_existing,
                **trigger_args
            )
            
            self.logger.info(
                f"Scheduled job {job.id} to run at {job.next_run_time}"
            )
            return job.id
            
        except Exception as e:
            self.logger.error(f"Failed to schedule job: {str(e)}")
            raise

    def modify_job(
        self,
        job_id: str,
        **changes: Dict[str, Any]
    ) -> bool:
        """
        Modify existing job parameters
        Args:
            job_id: ID of job to modify
            changes: Dictionary of parameters to update
        Returns:
            True if successful
        """
        try:
            self.scheduler.modify_job(job_id, **changes)
            self.logger.info(f"Modified job {job_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to modify job {job_id}: {str(e)}")
            return False

    def reschedule_job(
        self,
        job_id: str,
        trigger_type: str,
        **trigger_args: Dict[str, Any]
    ) -> bool:
        """
        Change when a job will run
        Args:
            job_id: ID of job to reschedule
            trigger_type: New trigger type
            trigger_args: New trigger parameters
        Returns:
            True if successful
        """
        try:
            self.scheduler.reschedule_job(
                job_id,
                trigger=trigger_type,
                **trigger_args
            )
            self.logger.info(f"Rescheduled job {job_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to reschedule job {job_id}: {str(e)}")
            return False

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a scheduled job
        Args:
            job_id: ID of job to cancel
        Returns:
            True if successful
        """
        try:
            self.scheduler.remove_job(job_id)
            self.logger.info(f"Cancelled job {job_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel job {job_id}: {str(e)}")
            return False

    def get_job(self, job_id: str) -> Dict[str, Any]:
        """
        Get job details
        Args:
            job_id: ID of job to retrieve
        Returns:
            Dictionary of job details
        """
        job = self.scheduler.get_job(job_id)
        if not job:
            return {}
            
        return {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time,
            "trigger": str(job.trigger)
        }

    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        Get all scheduled jobs
        Returns:
            List of job dictionaries
        """
        return [
            {
                "id": job.id,
                "next_run_time": job.next_run_time,
                "trigger": str(job.trigger)
            }
            for job in self.scheduler.get_jobs()
        ]

    def shutdown(self) -> None:
        """
        Gracefully shutdown scheduler
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self.logger.info("Scheduler shut down")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

# Example usage
if __name__ == "__main__":
    # Test job function
    def test_job(name: str):
        print(f"Hello {name} at {datetime.now()}")

    # Initialize scheduler
    scheduler = Scheduler()
    
    # Schedule some jobs
    job1_id = scheduler.add_job(
        func=test_job,
        trigger_type="date",
        run_date=datetime.now().replace(second=0, microsecond=0),
        args=("World",),
        job_id="test_job_1"
    )
    
    job2_id = scheduler.add_job(
        func=test_job,
        trigger_type="interval",
        interval=10,
        args=("Repeating",),
        job_id="test_job_2"
    )
    
    print(f"Scheduled jobs: {scheduler.list_jobs()}")
    
    # Modify a job
    scheduler.modify_job(job2_id, args=("Modified",))
    
    # Get job details
    print(f"Job 1 details: {scheduler.get_job(job1_id)}")
    
    # Let jobs run for demonstration
    import time
    time.sleep(15)
    
    # Cleanup
    scheduler.cancel_job(job2_id)
    print(f"Remaining jobs: {scheduler.list_jobs()}")