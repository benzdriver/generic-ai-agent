"""
Celery configuration
"""

from core.config import get_settings

settings = get_settings()

# Celery configuration
broker_url = settings.redis_url
result_backend = settings.redis_url

# Task settings
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# Worker settings
worker_prefetch_multiplier = 4
worker_max_tasks_per_child = 1000

# Task routing
task_routes = {
    'crawler.tasks.*': {'queue': 'crawler_tasks'},
    'ai.tasks.*': {'queue': 'ai_tasks'},
    'vectorizer.tasks.*': {'queue': 'vectorizer_tasks'},
}