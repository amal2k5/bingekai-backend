import requests
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional
from django.conf import settings
from django.core.cache import cache
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

FASTAPI_URL = getattr(settings, "FASTAPI_URL", "http://localhost:8001")
CACHE_TTL_RECOMMENDATIONS = 1800
CACHE_TTL_MOVIE_DETAILS = 86400




def _create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=2,
        backoff_factor=0.5,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    adapter = HTTPAdapter(
        pool_connections=10,
        pool_maxsize=20,
        max_retries=retry,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


_session = _create_session()


def _cache_key(prefix: str, identifier: str) -> str:
    return f"reco_{prefix}_{identifier}"


def clear_user_recommendation_cache(user) -> None:
    keys = [
        _cache_key("fastapi", str(user.id)),
        _cache_key("full", str(user.id)),
    ]
    cache.delete_many(keys)
    logger.info(f"🔄 Cleared recommendation cache for user {user.id}")


def _get_user_movie_data(user) -> dict:
    from ratings.models import Rating

    ratings = list(
        Rating.objects.filter(user=user)
        .values('movie_id', 'rating')
    )

    watchlist: list = []
    try:
        from watchlists.models import Collection, CollectionItem
        collection = Collection.objects.get(user=user, name="Watchlist")
        watchlist = list(
            CollectionItem.objects.filter(collection=collection)
            .values_list("movie_id", flat=True)
        )
    except Exception as e:
        logger.debug(f"Could not fetch watchlist: {e}")

    return {
        "user_id": user.id,
        "ratings": ratings,
        "watchlist_movies": watchlist,
    }


def fetch_movie_details(movie_id: int) -> Optional[dict]:
    cache_key = _cache_key("movie", str(movie_id))
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug(f"Cache HIT: movie {movie_id}")
        return cached

    try:
        url = f"{settings.TMDB_BASE_URL}/movie/{movie_id}"
        resp = _session.get(
            url,
            params={"api_key": settings.TMDB_API_KEY},
            timeout=5
        )
        resp.raise_for_status()
        data = resp.json()

        result = {
            "id": data.get("id"),
            "title": data.get("title"),
            "overview": data.get("overview"),
            "poster_path": data.get("poster_path"),
            "vote_average": data.get("vote_average"),
            "release_date": data.get("release_date"),
            "genres": [g["name"] for g in data.get("genres", [])],
        }

        cache.set(cache_key, result, timeout=CACHE_TTL_MOVIE_DETAILS)
        logger.debug(f"Cached movie {movie_id}")
        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ TMDB error for movie {movie_id}: {e}")
        return None


def fetch_multiple_movie_details(
    movie_ids: List[int],
    max_workers: int = 5
) -> Dict[int, dict]:
    results: Dict[int, dict] = {}
    unique_ids = list(set(movie_ids))

    logger.info(f"📽️ Fetching details for {len(unique_ids)} movies from TMDB")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_id = {
            executor.submit(fetch_movie_details, mid): mid
            for mid in unique_ids
        }
        for future in as_completed(future_to_id):
            mid = future_to_id[future]
            try:
                details = future.result()
                if details:
                    results[mid] = details
            except Exception as e:
                logger.error(f"❌ Failed to fetch movie {mid}: {e}")

    logger.info(f"✅ Fetched {len(results)}/{len(unique_ids)} movies from TMDB")
    return results


def _fetch_recommendation_ids_from_fastapi(user) -> List[int]:
    cache_key = _cache_key("fastapi", str(user.id))
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug(f"✅ Cache HIT: recommendation IDs for user {user.id}")
        return cached

    user_data = _get_user_movie_data(user)

    if not user_data["ratings"]:
        logger.warning(f"⚠️ User {user.id} has no ratings - cannot generate recommendations")
        return []

    try:
        from ratings.models import Rating
        rated_ids = set(Rating.objects.filter(user=user).values_list('movie_id', flat=True))
        
        resp = requests.get(
            "https://api.themoviedb.org/3/movie/popular",
            params={
                "api_key": settings.TMDB_API_KEY,
                "language": "en-US",
                "page": 1
            },
            timeout=10
        )
        resp.raise_for_status()
        popular = resp.json().get('results', [])
        candidate_ids = [m['id'] for m in popular if m['id'] not in rated_ids][:100]
        
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Failed to fetch TMDB popular: {e}")
        return []

    payload = {
        "user_id": user.id,
        "ratings": [
            {"movie_id": r['movie_id'], "score": float(r['rating'])}
            for r in user_data["ratings"]
        ],
        "candidate_movie_ids": candidate_ids,
        "limit": 50
    }

    try:
        logger.info(f"🤖 Calling FastAPI for user {user.id}...")
        resp = _session.post(
            f"{FASTAPI_URL}/recommend/",
            json=payload,
            timeout=30
        )
        resp.raise_for_status()
        data = resp.json()

        movie_ids = [r["movie_id"] for r in data.get("recommendations", [])]

        cache.set(cache_key, movie_ids, timeout=CACHE_TTL_RECOMMENDATIONS)
        logger.info(f"✅ FastAPI returned {len(movie_ids)} recommendations for user {user.id}")
        return movie_ids

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ FastAPI error for user {user.id}: {e}")
        return []


def get_recommendations(user, max_movies: int = 10) -> List[dict]:
    cache_key = _cache_key("full", str(user.id))
    cached = cache.get(cache_key)
    if cached is not None:
        logger.debug(f"✅ Cache HIT: full recommendations for user {user.id}")
        return cached[:max_movies]

    logger.info(f"📥 Generating recommendations for user {user.id}...")

    movie_ids = _fetch_recommendation_ids_from_fastapi(user)
    if not movie_ids:
        logger.warning(f"⚠️ No recommendations generated for user {user.id}")
        return []

    movie_ids = movie_ids[:max_movies]
    movies_dict = fetch_multiple_movie_details(movie_ids)

    movies = [movies_dict[mid] for mid in movie_ids if mid in movies_dict]

    cache.set(cache_key, movies, timeout=CACHE_TTL_RECOMMENDATIONS)
    logger.info(f"✅ Returning {len(movies)} recommendations for user {user.id}")
    return movies


def clear_user_recommendation_cache(user) -> None:
    keys = [
        _cache_key("fastapi", str(user.id)),
        _cache_key("full", str(user.id)),
    ]
    cache.delete_many(keys)
    logger.info(f"Cleared recommendation cache for user {user.id}")