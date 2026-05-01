from celery import shared_task
from django.core.cache import cache

from .services.trending_service import get_trending_movies


@shared_task
def update_trending_movies_cache():
    data = get_trending_movies()
    cache.set("admin_trending_movies", data, timeout=60 * 10)
    return "Trending cache updated"