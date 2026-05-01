from django.db.models import Avg, Count
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Rating
from rest_framework import status
from django.conf import settings
import logging
from django.contrib.auth import get_user_model
User = get_user_model()




class RateMovieView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        movie_id = request.data.get("movie_id")
        rating_value = int(request.data.get("rating"))

        if not (1 <= rating_value <= 5):
            return Response({"error": "Rating must be 1-5"}, status=400)

        rating, created = Rating.objects.update_or_create(
            user=request.user,
            movie_id=movie_id,
            defaults={"rating": rating_value}
        )

        return Response({"message": "Rating saved", "rating": rating.rating})

    def delete(self, request):
        movie_id = request.data.get("movie_id")

        deleted, _ = Rating.objects.filter(
            user=request.user,
            movie_id=movie_id
        ).delete()

        if deleted:
            return Response({"message": "Rating removed"})
        else:
            return Response({"message": "No rating found"}, status=404)



class UserRatingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id):
        try:
            rating = Rating.objects.get(
                user=request.user,
                movie_id=movie_id
            )
            return Response({"rating": rating.rating})
        except Rating.DoesNotExist:
            return Response({"rating": None})
        
        
        

class MovieRatingStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, movie_id):
        stats = Rating.objects.filter(movie_id=movie_id).aggregate(
            average=Avg('rating'),
            total=Count('id')
        )

        return Response({
            "average_rating": round(stats["average"], 2) if stats["average"] else 0,
            "total_ratings": stats["total"]
        })        
        
        
        
        
class MyRatingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        ratings = Rating.objects.filter(user=request.user).order_by("-id")

        data = []
        for r in ratings:
            data.append({
                "id": r.id,
                "movie_id": r.movie_id,
                "rating": r.rating,
            })

        return Response(data)        
    
    


logger = logging.getLogger(__name__)

try:
    from ratings.models import Rating
except ImportError:
    Rating = None


class InternalUserRatingsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, user_id):
        try:
            key = request.headers.get('X-Internal-Service-Key')
            expected_key = settings.INTERNAL_SERVICE_KEY

            if key != expected_key:
                logger.warning("Invalid internal key provided")
                return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

            if Rating is None:
                logger.error("Rating model not found")
                return Response([], status=status.HTTP_200_OK)

            ratings = Rating.objects.filter(user_id=user_id)

            logger.info(f"Found {ratings.count()} ratings for user {user_id}")

            data = [
                {
                    "movie_id": int(r.movie_id),
                    "score": float(r.rating)
                }
                for r in ratings
            ]

            logger.info(f"Returning {len(data)} ratings for user {user_id}: {data}")
            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"InternalUserRatingsView error: {str(e)}", exc_info=True)
            return Response([], status=status.HTTP_200_OK)


class InternalAllRatingsView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        try:
            key = request.headers.get('X-Internal-Service-Key')
            expected_key = settings.INTERNAL_SERVICE_KEY

            if key != expected_key:
                logger.warning("Invalid internal key provided for all ratings")
                return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

            if Rating is None:
                logger.error("Rating model not found")
                return Response([], status=status.HTTP_200_OK)

            ratings = Rating.objects.all()

            logger.info(f"Found {ratings.count()} total ratings")

            data = [
                {
                    "user_id": int(r.user_id),
                    "movie_id": int(r.movie_id),
                    "score": float(r.rating)
                }
                for r in ratings
            ]

            logger.info(f"Returning {len(data)} total ratings")
            return Response(data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"InternalAllRatingsView error: {str(e)}", exc_info=True)
            return Response([], status=status.HTTP_200_OK)