import requests
import logging
from celery import shared_task
from django.conf import settings
from django.contrib.auth import get_user_model
from ai.models import Recommendation
from ratings.models import Rating

logger = logging.getLogger(__name__)
User = get_user_model()

FASTAPI_URL = getattr(settings, "FASTAPI_URL", "http://localhost:8001")
TMDB_API_KEY = settings.TMDB_API_KEY


@shared_task(bind=True)
def get_recommendations_task(self, user_id):
    try:
        logger.info(f"Task started for user {user_id}")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return {"movies": [], "method": "error", "error": "User not found",
                    "ratings_count": 0, "candidates_count": 0}

        ratings = list(Rating.objects.filter(user=user).values('movie_id', 'rating'))
        logger.info(f"Found {len(ratings)} ratings for user {user_id}")

        if not ratings:
            return {"movies": [], "method": "no_ratings",
                    "ratings_count": 0, "candidates_count": 0}

        # Fetch candidate movies from TMDB
        try:
            response = requests.get(
                "https://api.themoviedb.org/3/movie/popular",
                params={"api_key": TMDB_API_KEY, "language": "en-US", "page": 1},
                timeout=15
            )
            response.raise_for_status()
            popular = response.json().get('results', [])
        except Exception as e:
            logger.error(f"Failed to fetch popular movies: {e}")
            popular = []

        rated_ids = {r['movie_id'] for r in ratings}
        candidate_ids = [m['id'] for m in popular if m['id'] not in rated_ids][:100]

        if not candidate_ids:
            return {"movies": [], "method": "no_candidates",
                    "ratings_count": len(ratings), "candidates_count": 0}

        # Call FastAPI
        payload = {
            "user_id": user_id,
            "ratings": [
                {"movie_id": r['movie_id'], "score": float(r['rating']) * 2}
                for r in ratings
            ],
            "candidate_movie_ids": candidate_ids,
            "limit": 20
        }

        try:
            fastapi_response = requests.post(
                f"{FASTAPI_URL}/recommend/",
                json=payload,
                timeout=45,
                headers={"Content-Type": "application/json"}
            )
            fastapi_response.raise_for_status()
            fastapi_data = fastapi_response.json()

            movie_ids = [r['movie_id'] for r in fastapi_data.get('recommendations', [])]
            method = fastapi_data.get('method', 'ai_similarity')
            confidence = fastapi_data.get('confidence', 0.7)
        except Exception as e:
            logger.error(f"FastAPI call failed: {e}")
            movie_ids = candidate_ids[:20]
            method = "fallback_popular"
            confidence = 0.3

        result = {
            "movies": movie_ids,
            "method": method,
            "ratings_count": len(ratings),
            "candidates_count": len(candidate_ids),
            "confidence": confidence
        }

        try:
            Recommendation.objects.update_or_create(
                user=user,
                defaults={"data": result}
            )
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")

        logger.info(f"Task completed, returned {len(movie_ids)} movies")
        return result

    except Exception as e:
        logger.error(f"Task failed: {str(e)}", exc_info=True)
        return {"movies": [], "method": "error", "error": str(e),
                "ratings_count": 0, "candidates_count": 0}