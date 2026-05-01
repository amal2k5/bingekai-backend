from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Count, Q
from django.core.cache import cache
from django.contrib.auth import get_user_model

from ratings.models import Rating
from reviews.models import Review
from .base_service import get_total_users
from typing import Optional

User = get_user_model()

CACHE_TIMEOUT = 300  
DEFAULT_DAYS = 7


def get_engagement_metrics(
    days: Optional[int] = None,
    start_date=None,
    end_date=None,
    use_cache: bool = True
):
    """
    Engagement metrics with support for:
    - preset days
    - custom date range
    """

    # 🔥 Determine mode
    if start_date and end_date:
        cache_key = f"engagement_metrics:{start_date}:{end_date}"
    else:
        days = days or DEFAULT_DAYS
        cache_key = f"engagement_metrics:{days}"

    # 🔁 Cache check
    if use_cache:
        cached = cache.get(cache_key)
        if cached:
            return cached

    # 📊 Basic totals (lifetime)
    total_users = get_total_users()
    total_ratings = Rating.objects.count()
    total_reviews = Review.objects.count()

    avg_ratings = total_ratings / total_users if total_users else 0
    avg_reviews = total_reviews / total_users if total_users else 0

    # 🔥 Date logic (FIXED)
    if start_date and end_date:
        start = start_date
        end = end_date
    else:
        days = days or DEFAULT_DAYS
        start = now() - timedelta(days=days)
        end = now()

    # 📊 Active users in period
    active_users = User.objects.filter(
        Q(ratings__created_at__range=[start, end]) |
        Q(reviews__created_at__range=[start, end])
    ).distinct().count()

    # 📊 Engagement %
    engagement_rate = (active_users / total_users * 100) if total_users else 0

    result = {
        "avg_ratings_per_user": round(avg_ratings, 2),
        "avg_reviews_per_user": round(avg_reviews, 2),
        "active_users_last_period": active_users,
        "engagement_rate_percentage": round(engagement_rate, 2),
    }

    # 💾 Cache result
    if use_cache:
        cache.set(cache_key, result, CACHE_TIMEOUT)

    return result