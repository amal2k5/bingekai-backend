from django.utils.timezone import now, localtime
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.cache import cache
from typing import Dict, Optional
import logging
from .base_service import get_total_users

User = get_user_model()
logger = logging.getLogger(__name__)

CACHE_KEY = 'growth_metrics'
CACHE_TIMEOUT = 600
DEFAULT_DAYS = 7




class GrowthMetricsService:

    @classmethod
    def get_metrics(
        cls,
        days: Optional[int] = None,
        start_date=None,
        end_date=None,
        use_cache: bool = True
    ) -> Dict[str, float]:

        cache_key = cls._build_cache_key(days, start_date, end_date)

        if use_cache:
            cached = cache.get(cache_key)
            if cached:
                return cached

        try:
            metrics = cls._calculate_metrics(days, start_date, end_date)

            if use_cache:
                cache.set(cache_key, metrics, CACHE_TIMEOUT)

            return metrics

        except Exception as e:
            logger.error(f"Failed to calculate growth metrics: {str(e)}")
            raise

    @classmethod
    def _build_cache_key(cls, days, start_date, end_date) -> str:
        if start_date and end_date:
            return f"{CACHE_KEY}:{start_date}:{end_date}"
        days = days or DEFAULT_DAYS
        return f"{CACHE_KEY}:{days}"

    @staticmethod
    def _calculate_metrics(days, start_date, end_date) -> Dict[str, float]:
        total_users = get_total_users()

        if total_users == 0:
            return {
                "total_users": 0,
                "new_users": 0,
                "growth_percentage": 0.0,
                "daily_growth_rate": 0.0,
                "active_users": 0,           
                "suspended_users": 0,        
            }

        start, end, period_days = GrowthMetricsService._get_date_range(days, start_date, end_date)

        new_users = User.objects.filter(
            created_at__range=[start, end]
        ).count()
        active_users = User.objects.filter(is_active=True).count()
        suspended_users = User.objects.filter(is_active=False).count()

        return {
            "total_users": total_users,
            "new_users": new_users,
            "growth_percentage": round((new_users / total_users) * 100, 2),
            "daily_growth_rate": round(new_users / period_days, 2),
            "active_users": active_users,          
            "suspended_users": suspended_users,
        }

    @staticmethod
    def _get_date_range(days, start_date, end_date):
        if start_date and end_date:
            start = start_date
            end = end_date
            period_days = (end - start).days + 1
        else:
            days = days or DEFAULT_DAYS
            now_date = localtime(now()).date()
            start = now_date - timedelta(days=days - 1)
            end = now_date
            period_days = days
        
        return start, end, period_days

    @classmethod
    def invalidate_cache(cls, days: int = None, start_date=None, end_date=None):
        if days:
            cache.delete(f"{CACHE_KEY}:{days}")
        elif start_date and end_date:
            cache.delete(f"{CACHE_KEY}:{start_date}:{end_date}")
        else:
            for d in [1, 7, 30, 90, DEFAULT_DAYS]:
                cache.delete(f"{CACHE_KEY}:{d}")
        
        logger.info("Growth metrics cache invalidated")


def get_growth_metrics(days=None, start_date=None, end_date=None, use_cache=True):
    return GrowthMetricsService.get_metrics(
        days=days,
        start_date=start_date,
        end_date=end_date,
        use_cache=use_cache
    )