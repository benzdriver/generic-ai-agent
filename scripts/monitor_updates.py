#!/usr/bin/env python3
"""
Website Update Monitor

This script monitors websites for updates using sitemaps and HTTP headers.
It's designed to be a lightweight, high-frequency "scout" that detects
potential changes and queues them for a more heavyweight processing script.
"""

import asyncio
import logging
import requests
import yaml
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from xml.etree import ElementTree as ET
from urllib.parse import urlparse

# --- Setup Paths and Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

project_root = Path(__file__).parent.parent
config_dir = project_root / "config" / "domains"
cache_dir = project_root / "cache"
cache_dir.mkdir(exist_ok=True)

MONITOR_STATE_FILE = cache_dir / "monitor_state.json"
UPDATE_QUEUE_FILE = cache_dir / "update_queue.json"

# --- Core Classes ---

class MonitorState:
    """Manages the state of monitored URLs."""
    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.urls_state: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if not self.state_file.exists():
            return {}
        with open(self.state_file, 'r') as f:
            return json.load(f)

    def save(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.urls_state, f, indent=2)

    def get_last_modified(self, url: str) -> Optional[datetime]:
        state = self.urls_state.get(url)
        if state and 'last_modified':
            return datetime.fromisoformat(state['last_modified'])
        return None

    def update_url_state(self, url: str, last_modified: datetime):
        self.urls_state[url] = {'last_modified': last_modified.isoformat()}

class UpdateMonitor:
    """Detects website changes and queues them for processing."""

    def __init__(self):
        self.state = MonitorState(MONITOR_STATE_FILE)
        self.update_queue: List[Dict[str, str]] = []

    def _find_sitemap(self, domain_url: str) -> Optional[str]:
        """Tries to find the sitemap URL."""
        robots_url = f"{domain_url.rstrip('/')}/robots.txt"
        try:
            res = requests.get(robots_url, timeout=10)
            if res.status_code == 200:
                for line in res.text.splitlines():
                    if line.lower().startswith("sitemap:"):
                        sitemap_url = line.split(":", 1)[1].strip()
                        logger.info(f"Sitemap found in robots.txt: {sitemap_url}")
                        return sitemap_url
        except requests.RequestException as e:
            logger.warning(f"Could not fetch or parse robots.txt at {robots_url}: {e}")
        
        # Fallback to common location
        sitemap_url = f"{domain_url.rstrip('/')}/sitemap.xml"
        logger.info(f"Trying common sitemap location: {sitemap_url}")
        return sitemap_url

    def _parse_sitemap(self, sitemap_url: str) -> Dict[str, datetime]:
        """Parses a sitemap and returns URLs with their last modification dates."""
        urls = {}
        try:
            res = requests.get(sitemap_url, timeout=20)
            if res.status_code != 200:
                logger.error(f"Failed to fetch sitemap {sitemap_url}, status: {res.status_code}")
                return {}

            tree = ET.fromstring(res.content)
            
            # Handle sitemap index files
            if tree.tag.endswith('sitemapindex'):
                for sitemap in tree.findall('{*}sitemap'):
                    loc = sitemap.find('{*}loc')
                    if loc is not None:
                        logger.info(f"Found nested sitemap: {loc.text}")
                        urls.update(self._parse_sitemap(loc.text))
                return urls

            # Handle regular sitemaps
            for url_element in tree.findall('{*}url'):
                loc = url_element.find('{*}loc')
                lastmod = url_element.find('{*}lastmod')
                if loc is not None and lastmod is not None:
                    try:
                        # Ensure timezone awareness
                        mod_time = datetime.fromisoformat(lastmod.text).astimezone(timezone.utc)
                        urls[loc.text] = mod_time
                    except ValueError:
                        logger.warning(f"Could not parse lastmod date '{lastmod.text}' for url {loc.text}")

        except Exception as e:
            logger.error(f"Error parsing sitemap {sitemap_url}: {e}")
        return urls

    async def check_source(self, source_name: str, base_url: str):
        """Checks a single source for updates using its sitemap."""
        logger.info(f"--- Checking source: {source_name} ---")
        domain_url = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
        
        sitemap_url = self._find_sitemap(domain_url)
        if not sitemap_url:
            logger.warning(f"No sitemap found for {domain_url}. Cannot perform sitemap-based monitoring.")
            return

        sitemap_urls = self._parse_sitemap(sitemap_url)
        if not sitemap_urls:
            logger.warning(f"Sitemap for {source_name} at {sitemap_url} is empty or failed to parse.")
            return

        for url, last_modified in sitemap_urls.items():
            previous_mod_time = self.state.get_last_modified(url)
            
            if previous_mod_time is None or last_modified > previous_mod_time:
                logger.info(f"CHANGE DETECTED for {url} (New: {last_modified}, Old: {previous_mod_time})")
                self.update_queue.append({'url': url, 'source_name': source_name})
                self.state.update_url_state(url, last_modified)

    async def run(self):
        """Runs the monitoring process for all configured domains."""
        logger.info("Starting website update monitor...")
        
        for config_file in config_dir.glob("*.yaml"):
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                
                if not config.get('enabled', True):
                    logger.info(f"Skipping disabled domain: {config.get('name', config_file.stem)}")
                    continue
                
                for source in config.get('sources', []):
                    if source.get('type') == 'website':
                        await self.check_source(source['name'], source['url'])
            
            except Exception as e:
                logger.error(f"Failed to process config file {config_file}: {e}")

        if self.update_queue:
            logger.info(f"Found {len(self.update_queue)} updated pages. Writing to queue.")
            with open(UPDATE_QUEUE_FILE, 'w') as f:
                json.dump(self.update_queue, f, indent=2)
        else:
            logger.info("No updates detected.")

        self.state.save()
        logger.info("Monitoring run finished.")

async def main():
    monitor = UpdateMonitor()
    await monitor.run()

if __name__ == "__main__":
    asyncio.run(main()) 