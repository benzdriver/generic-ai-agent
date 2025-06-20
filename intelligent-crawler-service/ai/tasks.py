"""
AI Worker Tasks
"""

from celery import Celery
import logging
from typing import Dict, Any, List
import asyncio

from .evaluator import ContentEvaluator
from .extractor import IntelligentExtractor
from core.models import PageContent

logger = logging.getLogger(__name__)

# Initialize Celery
app = Celery('ai_tasks')
app.config_from_object('core.celery_config')

@app.task(name='ai.evaluate_content')
def evaluate_content(content_data: Dict[str, Any], job_id: str) -> Dict[str, Any]:
    """
    Evaluate content quality using AI
    """
    try:
        # Convert dict to PageContent model
        content = PageContent(**content_data)
        
        # Evaluate
        evaluator = ContentEvaluator()
        evaluation = asyncio.run(evaluator.evaluate_content(content))
        
        # Add evaluation scores to content data
        enriched_content = {
            **content_data,
            'ai_scores': evaluation.dict()
        }
        
        # Send to vectorizer if evaluation passes threshold
        if evaluation.overall_score >= 0.5:  # Configurable threshold
            app.send_task(
                'vectorizer.process_crawled_content',
                args=[enriched_content, job_id],
                queue='vectorizer_tasks'
            )
            logger.info(f"Content from {content.url} sent to vectorizer (score: {evaluation.overall_score})")
        else:
            logger.info(f"Content from {content.url} rejected due to low score: {evaluation.overall_score}")
        
        return {
            'success': True,
            'evaluation': evaluation.dict(),
            'sent_to_vectorizer': evaluation.overall_score >= 0.5
        }
        
    except Exception as e:
        logger.error(f"Error evaluating content: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.task(name='ai.extract_structured_data')
def extract_structured_data(content_data: Dict[str, Any], schema: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Extract structured data from content
    """
    try:
        content = PageContent(**content_data)
        
        extractor = IntelligentExtractor()
        # Note: This is simplified - in production would need page object
        structured_data = {
            'main_content': content.text[:1000],
            'metadata': {
                'title': content.title,
                'url': content.url
            }
        }
        
        return {
            'success': True,
            'structured_data': structured_data
        }
        
    except Exception as e:
        logger.error(f"Error extracting data: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.task(name='ai.batch_evaluate')
def batch_evaluate_content(contents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Batch evaluate multiple contents
    """
    try:
        evaluator = ContentEvaluator()
        results = []
        
        for content_data in contents:
            content = PageContent(**content_data)
            evaluation = asyncio.run(evaluator.evaluate_content(content))
            results.append(evaluation.dict())
        
        return {
            'success': True,
            'evaluations': results
        }
        
    except Exception as e:
        logger.error(f"Error in batch evaluation: {e}")
        return {
            'success': False,
            'error': str(e)
        }