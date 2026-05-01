from django.core.cache import cache
from django.db.models import Count
from django.utils.timezone import now
from datetime import timedelta
from collections import defaultdict
from typing import Optional

from ratings.models import Rating
from reviews.models import Review

CACHE_TIMEOUT = 600
DEFAULT_DAYS = 7


def get_trending_movies(days=None, start_date=None, end_date=None):
    if start_date and end_date:
        cache_key = f"admin_trending_movies:{start_date}:{end_date}"
    else:
        days = days or DEFAULT_DAYS
        cache_key = f"admin_trending_movies:{days}"

    cached = cache.get(cache_key)
    if cached:
        return cached

    if start_date and end_date:
        start = start_date
        end = end_date
    else:
        days = days or DEFAULT_DAYS
        start = now() - timedelta(days=days)
        end = now()

    ratings = (
        Rating.objects
        .filter(created_at__range=[start, end])
        .values("movie_id")
        .annotate(score=Count("id"))
    )

    reviews = (
        Review.objects
        .filter(created_at__range=[start, end])
        .values("movie_id")
        .annotate(score=Count("id"))
    )

    movie_scores = defaultdict(int)

    for r in ratings:
        movie_scores[r["movie_id"]] += r["score"]

    for r in reviews:
        movie_scores[r["movie_id"]] += r["score"]

    result = [
        {"movie_id": movie_id, "score": score}
        for movie_id, score in sorted(
            movie_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
    ]

    cache.set(cache_key, result, CACHE_TIMEOUT)

    return result