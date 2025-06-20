"""
Incremental Update Scheduler
"""

import asyncio
import logging
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Dict

from core.config import get_settings
from core.models import UpdateCheck
from .change_detector import ChangeDetector

logger = logging.getLogger(__name__)
settings = get_settings()

class UpdateScheduler:
    """
    Manages incremental update scheduling
    """
    
    def __init__(self):
        self.change_detector = ChangeDetector()
        self.monitored_urls = []
        
    async def initialize(self):
        """Initialize scheduler"""
        logger.info("Initializing update scheduler")
        
        # Load monitored URLs from database
        self.monitored_urls = await self.load_monitored_urls()
        
        # Schedule jobs
        self.schedule_jobs()
        
    async def load_monitored_urls(self) -> List[Dict]:
        """Load URLs to monitor from database"""
        # Simplified - in production would query database
        return [
            {
                'url': 'https://example.com/page1',
                'check_frequency': 'daily',
                'last_checked': datetime.now() - timedelta(days=1)
            }
        ]
    
    def schedule_jobs(self):
        """Schedule update jobs"""
        
        # Hourly checks
        schedule.every().hour.do(self.run_hourly_checks)
        
        # Daily checks
        schedule.every().day.at("02:00").do(self.run_daily_checks)
        
        # Weekly checks
        schedule.every().monday.at("03:00").do(self.run_weekly_checks)
        
        logger.info("Update jobs scheduled")
    
    def run_hourly_checks(self):
        """Run hourly update checks"""
        asyncio.run(self._run_checks('hourly'))
    
    def run_daily_checks(self):
        """Run daily update checks"""
        asyncio.run(self._run_checks('daily'))
    
    def run_weekly_checks(self):
        """Run weekly update checks"""
        asyncio.run(self._run_checks('weekly'))
    
    async def _run_checks(self, frequency: str):
        """Run update checks for given frequency"""
        logger.info(f"Running {frequency} update checks")
        
        urls_to_check = [
            url for url in self.monitored_urls
            if url.get('check_frequency') == frequency
        ]
        
        if not urls_to_check:
            return
        
        # Check for changes
        results = []
        for url_info in urls_to_check:
            result = await self.change_detector.check_url(url_info['url'])
            results.append(result)
        
        # Process results
        changed_urls = [r for r in results if r.has_changed]
        
        if changed_urls:
            logger.info(f"Found {len(changed_urls)} changed URLs")
            await self.queue_updates(changed_urls)
        else:
            logger.info("No changes detected")
    
    async def queue_updates(self, changes: List[UpdateCheck]):
        """Queue crawl jobs for changed URLs"""
        for change in changes:
            logger.info(f"Queueing update for {change.url}")
            # In production, would queue to Celery
            
    def run(self):
        """Run the scheduler"""
        logger.info("Update scheduler started")
        
        # Initialize
        asyncio.run(self.initialize())
        
        # Run schedule loop
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    scheduler = UpdateScheduler()
    
    try:
        scheduler.run()
    except KeyboardInterrupt:
        logger.info("Scheduler stopped")

if __name__ == "__main__":
    main()