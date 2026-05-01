from django.utils.timezone import now, localtime
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.core.cache import cache
from datetime import timedelta
from typing import List, Dict
import logging

from ratings.models import Rating
from reviews.models import Review

logger = logging.getLogger(__name__)

CACHE_KEY = 'activity_trend'
CACHE_TIMEOUT = 300
DEFAULT_DAYS = 7




class ActivityTrendService:

    @classmethod
    def get_trend(
        cls,
        days: int = None,
        start_date=None,
        end_date=None,
        use_cache: bool = True
    ) -> List[Dict]:

        if start_date and end_date:
            cache_key = f"{CACHE_KEY}:{start_date}:{end_date}"
        else:
            days = days or DEFAULT_DAYS
            cache_key = f"{CACHE_KEY}:{days}"

        if use_cache:
            cached = cache.get(cache_key)
            if cached:
                logger.debug(f"Activity trend retrieved from cache ({cache_key})")
                return cached

        try:
            trend = cls._calculate_trend(days, start_date, end_date)

            if use_cache:
                cache.set(cache_key, trend, CACHE_TIMEOUT)
                logger.info(f"Activity trend calculated and cached ({cache_key})")

            return trend

        except Exception as e:
            logger.error(f"Failed to calculate activity trend: {str(e)}")
            raise

    @classmethod
    def _calculate_trend(cls, days, start_date, end_date) -> List[Dict]:

        if start_date and end_date:
            start = start_date
            end = end_date
            days = (end - start).days + 1
        else:
            current_date = localtime(now()).date()
            days = days or DEFAULT_DAYS
            start = current_date - timedelta(days=days - 1)
            end = current_date

        ratings = (
            Rating.objects
            .filter(created_at__date__range=[start, end])
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'))
        )

        reviews = (
            Review.objects
            .filter(created_at__date__range=[start, end],
            is_hidden=False)
            .annotate(day=TruncDate('created_at'))
            .values('day')
            .annotate(count=Count('id'))
        )

        ratings_map = {r['day']: r['count'] for r in ratings}
        reviews_map = {r['day']: r['count'] for r in reviews}

        result = []

        for i in range(days):
            day = start + timedelta(days=i)
            r = ratings_map.get(day, 0)
            rv = reviews_map.get(day, 0)
            result.append({
                'date': day.isoformat(),
                'ratings': r,
                'reviews': rv,
                'total': r + rv
            })

        return result

    @classmethod
    def invalidate_cache(cls, days: int = None):
        if days:
            cache.delete(f"{CACHE_KEY}:{days}")
        else:
            for d in [1, 7, 30, 90]:
                cache.delete(f"{CACHE_KEY}:{d}")

        logger.info("Activity trend cache invalidated")


def get_activity_trend(days=None, start_date=None, end_date=None, use_cache=True):
    return ActivityTrendService.get_trend(
        days=days,
        start_date=start_date,
        end_date=end_date,
        use_cache=use_cache
    )