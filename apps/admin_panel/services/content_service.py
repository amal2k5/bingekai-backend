from reviews.models import Review
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import Length
from django.db.models import Avg, Count, Q
from django.core.cache import cache
from typing import Dict
import logging

from reviews.models import Review

logger = logging.getLogger(__name__)

CACHE_KEY = 'content_quality_metrics'
CACHE_TIMEOUT = 600
MIN_REVIEW_LENGTH = 10


class ContentQualityService:
    
    @classmethod
    def get_metrics(cls, use_cache: bool = True) -> Dict[str, float]:
        if use_cache:
            cached = cache.get(CACHE_KEY)
            if cached:
                return cached
        
        try:
            metrics = cls._calculate_metrics()
            if use_cache:
                cache.set(CACHE_KEY, metrics, CACHE_TIMEOUT)
            return metrics
        except Exception as e:
            logger.error(f"Failed to calculate content quality: {str(e)}")
            raise
    
    @staticmethod
    def _calculate_metrics() -> Dict[str, float]:
        stats = Review.objects.aggregate(
            total=Count('id'),
            with_text=Count('id', filter=~Q(content="")),
            avg_length=Avg(Length('content'), filter=~Q(content="")),
            quality_reviews=Count('id', filter=Q(content__regex=f'.{{{MIN_REVIEW_LENGTH},}}'))
        )
        
        total = stats['total'] or 0
        
        if total == 0:
            return {
                "reviews_with_text_percentage": 0.0,
                "avg_review_length": 0.0,
                "total_reviews": 0,
                "reviews_with_text": 0,
                "quality_reviews_percentage": 0.0,
            }
        
        with_text = stats['with_text'] or 0
        avg_length = stats['avg_length'] or 0
        quality = stats['quality_reviews'] or 0
        
        return {
            "reviews_with_text_percentage": round(with_text / total * 100, 2),
            "avg_review_length": round(avg_length, 2),
            "total_reviews": total,
            "reviews_with_text": with_text,
            "quality_reviews_percentage": round(quality / total * 100, 2),
        }
    
    @classmethod
    def invalidate_cache(cls) -> None:
        cache.delete(CACHE_KEY)


def get_content_quality(use_cache: bool = True) -> Dict[str, float]:
    return ContentQualityService.get_metrics(use_cache)



def get_content_quality_metrics(days=None, start_date=None, end_date=None):
    queryset = Review.objects.all()

    if start_date and end_date:
        queryset = queryset.filter(created_at__range=[start_date, end_date])
    elif days:
        since = timezone.now() - timedelta(days=days)
        queryset = queryset.filter(created_at__gte=since)

    return {
        "total_reviews": queryset.count()
    }