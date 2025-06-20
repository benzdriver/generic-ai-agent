"""
AI Content Evaluator
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
import re

from core.models import PageContent, ContentEvaluation
from core.llm import LLMClient
from utils.text_utils import extract_key_sentences, calculate_text_similarity

logger = logging.getLogger(__name__)

class ContentEvaluator:
    """
    AI-powered content quality evaluator
    """
    
    def __init__(self):
        self.llm = LLMClient()
        self.evaluation_cache = {}
        
    async def evaluate_content(self, content: PageContent) -> ContentEvaluation:
        """
        Evaluate content quality and relevance
        """
        
        # Check cache first
        cache_key = content.content_hash
        if cache_key in self.evaluation_cache:
            logger.debug(f"Using cached evaluation for {content.url}")
            return self.evaluation_cache[cache_key]
        
        try:
            # Prepare content for evaluation
            content_preview = content.text[:3000]  # First 3000 chars
            
            # Get AI evaluation
            evaluation_prompt = f"""
            Evaluate this web page content for quality and relevance to knowledge extraction.
            
            URL: {content.url}
            Title: {content.title}
            Description: {content.description}
            Content Preview: {content_preview}
            
            Please evaluate based on:
            1. Information Quality (0-10): Is the content informative, accurate, and well-structured?
            2. Relevance (0-10): Is this content useful for building a knowledge base?
            3. Completeness (0-10): Does the page contain complete information or just snippets?
            4. Freshness (0-10): Does the content appear current and up-to-date?
            
            Also identify:
            - Main topics covered
            - Content type (guide, FAQ, reference, news, etc.)
            - Target audience
            - Any quality issues
            
            Return a structured evaluation.
            """
            
            response = await self.llm.evaluate(evaluation_prompt)
            
            # Parse response
            evaluation = ContentEvaluation(
                url=content.url,
                quality_score=self._normalize_score(response.get('information_quality', 5)),
                relevance_score=self._normalize_score(response.get('relevance', 5)),
                completeness_score=self._normalize_score(response.get('completeness', 5)),
                freshness_score=self._normalize_score(response.get('freshness', 5)),
                topics=response.get('topics', []),
                content_type=response.get('content_type', 'unknown'),
                target_audience=response.get('target_audience', 'general'),
                quality_issues=response.get('quality_issues', []),
                recommendation=response.get('recommendation', 'neutral'),
                evaluated_at=datetime.utcnow()
            )
            
            # Calculate overall score
            evaluation.overall_score = (
                evaluation.quality_score * 0.3 +
                evaluation.relevance_score * 0.3 +
                evaluation.completeness_score * 0.2 +
                evaluation.freshness_score * 0.2
            )
            
            # Cache the evaluation
            self.evaluation_cache[cache_key] = evaluation
            
            logger.info(f"Evaluated {content.url}: score={evaluation.overall_score:.2f}")
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating content: {e}")
            
            # Return default evaluation on error
            return ContentEvaluation(
                url=content.url,
                quality_score=0.5,
                relevance_score=0.5,
                completeness_score=0.5,
                freshness_score=0.5,
                overall_score=0.5,
                topics=[],
                content_type='unknown',
                quality_issues=['evaluation_failed'],
                evaluated_at=datetime.utcnow()
            )
    
    def _normalize_score(self, score: float) -> float:
        """Normalize score to 0-1 range"""
        if isinstance(score, (int, float)):
            return max(0, min(1, score / 10))
        return 0.5  # Default
    
    async def evaluate_batch(self, contents: List[PageContent]) -> List[ContentEvaluation]:
        """
        Evaluate multiple contents efficiently
        """
        evaluations = []
        
        # Group similar content for batch evaluation
        content_groups = self._group_similar_content(contents)
        
        for group in content_groups:
            if len(group) == 1:
                # Single content, evaluate normally
                evaluation = await self.evaluate_content(group[0])
                evaluations.append(evaluation)
            else:
                # Batch evaluate similar content
                batch_evaluations = await self._batch_evaluate(group)
                evaluations.extend(batch_evaluations)
        
        return evaluations
    
    def _group_similar_content(self, contents: List[PageContent]) -> List[List[PageContent]]:
        """Group similar content for efficient evaluation"""
        groups = []
        processed = set()
        
        for i, content in enumerate(contents):
            if i in processed:
                continue
                
            group = [content]
            processed.add(i)
            
            # Find similar content
            for j, other in enumerate(contents[i+1:], i+1):
                if j in processed:
                    continue
                    
                # Check similarity
                similarity = calculate_text_similarity(
                    content.text[:1000], 
                    other.text[:1000]
                )
                
                if similarity > 0.8:  # High similarity
                    group.append(other)
                    processed.add(j)
            
            groups.append(group)
        
        return groups
    
    async def _batch_evaluate(self, contents: List[PageContent]) -> List[ContentEvaluation]:
        """Evaluate a batch of similar content"""
        
        # Prepare batch prompt
        batch_prompt = "Evaluate these similar web pages for quality and relevance:\n\n"
        
        for i, content in enumerate(contents[:5]):  # Max 5 in a batch
            batch_prompt += f"""
            Page {i+1}:
            URL: {content.url}
            Title: {content.title}
            Preview: {content.text[:500]}
            
            """
        
        batch_prompt += """
        For each page, provide:
        1. Quality score (0-10)
        2. Relevance score (0-10)
        3. Main topics
        4. Content type
        5. Recommendation (keep/skip)
        """
        
        response = await self.llm.evaluate_batch(batch_prompt)
        
        # Parse batch response
        evaluations = []
        for i, content in enumerate(contents):
            page_eval = response.get(f'page_{i+1}', {})
            
            evaluation = ContentEvaluation(
                url=content.url,
                quality_score=self._normalize_score(page_eval.get('quality', 5)),
                relevance_score=self._normalize_score(page_eval.get('relevance', 5)),
                completeness_score=0.7,  # Default for batch
                freshness_score=0.7,  # Default for batch
                topics=page_eval.get('topics', []),
                content_type=page_eval.get('content_type', 'unknown'),
                recommendation=page_eval.get('recommendation', 'neutral'),
                evaluated_at=datetime.utcnow()
            )
            
            evaluation.overall_score = (
                evaluation.quality_score * 0.5 +
                evaluation.relevance_score * 0.5
            )
            
            evaluations.append(evaluation)
        
        return evaluations
    
    async def identify_key_content(self, content: PageContent) -> Dict:
        """
        Identify key information in the content
        """
        
        key_info = {
            'requirements': [],
            'processes': [],
            'fees': [],
            'timelines': [],
            'forms': [],
            'contacts': []
        }
        
        # Extract requirements
        req_patterns = [
            r'(?:must|need to|required to|should) (?:have|be|provide|submit)',
            r'eligibility (?:criteria|requirements)',
            r'qualify (?:for|if)'
        ]
        
        for pattern in req_patterns:
            matches = re.finditer(pattern, content.text, re.IGNORECASE)
            for match in matches:
                context = self._extract_context(content.text, match.start(), match.end())
                key_info['requirements'].append(context)
        
        # Extract fees
        fee_pattern = r'\$[\d,]+(?:\.\d{2})?|\d+\s*(?:dollars?|CAD|USD)'
        fee_matches = re.finditer(fee_pattern, content.text)
        for match in fee_matches:
            context = self._extract_context(content.text, match.start(), match.end(), window=50)
            key_info['fees'].append({
                'amount': match.group(),
                'context': context
            })
        
        # Extract timelines
        time_patterns = [
            r'\d+\s*(?:days?|weeks?|months?|years?)',
            r'processing time',
            r'wait (?:time|period)'
        ]
        
        for pattern in time_patterns:
            matches = re.finditer(pattern, content.text, re.IGNORECASE)
            for match in matches:
                context = self._extract_context(content.text, match.start(), match.end())
                key_info['timelines'].append(context)
        
        # Use AI for more complex extraction
        if key_info['requirements'] or key_info['fees'] or key_info['timelines']:
            enhanced_info = await self._ai_enhance_key_info(content, key_info)
            key_info.update(enhanced_info)
        
        return key_info
    
    def _extract_context(self, text: str, start: int, end: int, window: int = 100) -> str:
        """Extract context around a match"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        
        # Find sentence boundaries
        while context_start > 0 and text[context_start] not in '.!?\n':
            context_start -= 1
        
        while context_end < len(text) and text[context_end] not in '.!?\n':
            context_end += 1
        
        return text[context_start:context_end].strip()
    
    async def _ai_enhance_key_info(self, content: PageContent, key_info: Dict) -> Dict:
        """Use AI to enhance extracted key information"""
        
        prompt = f"""
        Review this extracted information and enhance it:
        
        Page: {content.title}
        URL: {content.url}
        
        Extracted Requirements: {key_info['requirements'][:3]}
        Extracted Fees: {key_info['fees'][:3]}
        Extracted Timelines: {key_info['timelines'][:3]}
        
        Please:
        1. Verify and correct the extracted information
        2. Add any missing important details
        3. Structure the information clearly
        4. Identify the specific process or program these relate to
        """
        
        response = await self.llm.extract_structured(prompt)
        
        return {
            'program': response.get('program', 'unknown'),
            'verified_requirements': response.get('requirements', []),
            'verified_fees': response.get('fees', []),
            'verified_timelines': response.get('timelines', []),
            'additional_info': response.get('additional_info', {})
        }