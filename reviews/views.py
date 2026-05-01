import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from ratings.models import Rating
from rest_framework import generics, permissions, status
from .serializers import ReviewSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Like, Review
from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .ai_client import detect_spoiler_via_ai

TMDB_API_KEY = settings.TMDB_API_KEY  

import logging
logger = logging.getLogger(__name__)



#- GET all reviews for a movie

class MovieReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        movie_id = self.kwargs["movie_id"]
        sort = self.request.query_params.get("sort", "top")

        queryset = (
            Review.objects
            .filter(movie_id=movie_id, is_hidden=False)
            .prefetch_related('likes')
            .annotate(like_count_val=Count('likes'))
        )

        if sort == "latest":
            return queryset.order_by("-created_at")
        else:
            return queryset.order_by("-like_count_val", "-created_at")  

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    

#- POST review


class CreateReviewView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        content = serializer.validated_data.get('content', '')
        
        has_spoiler, confidence, method, reasoning = detect_spoiler_via_ai(content)
        
        serializer.save(
            user=self.request.user,
            has_spoiler=has_spoiler,
            spoiler_confidence=confidence,
            spoiler_reasoning=reasoning 
        )
        
#- UPDATE review

class UpdateReviewView(generics.UpdateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)


#- DELETE review

class DeleteReviewView(generics.DestroyAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(user=self.request.user)
    
    


class UserActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get_movie_details(self, movie_id):
        cache_key = f"movie_details_{movie_id}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return cached_data

        try:
            url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
            res = requests.get(url, timeout=3)

            if res.status_code == 200:
                data = res.json()
                result = {
                    "title": data.get("title", "Unknown Title"),
                    "poster_path": data.get("poster_path"),
                    "release_date": data.get("release_date", ""),
                }
                cache.set(cache_key, result, timeout=86400)
                return result

        except Exception as e:
            print(f"--- TMDB API ERROR for ID {movie_id}: {e} ---")

        return {
            "title": "Title Unavailable",
            "poster_path": None
        }

    def get(self, request):
        user = request.user

        ratings = Rating.objects.filter(user=user)
        reviews = Review.objects.filter(user=user).prefetch_related('likes')

        activity_map = {}

        for r in ratings:
            activity_map[r.movie_id] = {
                "movie_id": r.movie_id,
                "rating": r.rating,
                "review": None,
                "review_id": None,
                "like_count": 0,
                "is_liked": False,
                "has_spoiler": False,
                "spoiler_confidence": 0.0,
                "spoiler_reasoning": None,
                "created_at": r.created_at,
            }

        for rev in reviews:
            like_count = rev.likes.count()
            is_liked = rev.likes.filter(user=user).exists()

            if rev.movie_id in activity_map:
                activity_map[rev.movie_id]["review"] = rev.content
                activity_map[rev.movie_id]["review_id"] = rev.id
                activity_map[rev.movie_id]["like_count"] = like_count
                activity_map[rev.movie_id]["is_liked"] = is_liked
                activity_map[rev.movie_id]["has_spoiler"] = rev.has_spoiler
                activity_map[rev.movie_id]["spoiler_confidence"] = rev.spoiler_confidence
                activity_map[rev.movie_id]["spoiler_reasoning"] = rev.spoiler_reasoning
                activity_map[rev.movie_id]["created_at"] = max(
                    activity_map[rev.movie_id]["created_at"],
                    rev.created_at
                )
            else:
                activity_map[rev.movie_id] = {
                    "movie_id": rev.movie_id,
                    "rating": None,
                    "review": rev.content,
                    "review_id": rev.id,
                    "like_count": like_count,
                    "is_liked": is_liked,
                    "has_spoiler": rev.has_spoiler,
                    "spoiler_confidence": rev.spoiler_confidence,
                    "spoiler_reasoning": rev.spoiler_reasoning,
                    "created_at": rev.created_at,
                }

        final_activity = []
        for movie_id, data in activity_map.items():
            details = self.get_movie_details(movie_id)
            data.update(details)
            final_activity.append(data)

        return Response(final_activity)

#- Review Like Feature

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_like(request, review_id):
    
    review = get_object_or_404(Review, id=review_id)

    like, created = Like.objects.get_or_create(
        user=request.user,
        review=review
    )

    if not created:

        like.delete()
        liked = False
    else:
        liked = True

    like_count = review.likes.count()

    return Response({
        'liked': liked,
        'like_count': like_count,
    }, status=status.HTTP_200_OK)    
    
    
    
    
#- trending reviews

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trending_reviews(request):
    week_ago = timezone.now() - timedelta(days=7)

    reviews = (
        Review.objects.filter(is_hidden=False)
        .prefetch_related('likes')
        .select_related('user')
        .annotate(
            recent_likes=Count(
                'likes',
                filter=Q(likes__created_at__gte=week_ago)
            )
        )
        .filter(recent_likes__gt=0)
        .order_by('-recent_likes', '-created_at')[:20]
    )

    data = [
    {
        "id": r.id,
        "movie_id": r.movie_id,
        "content": r.content,
        "rating": r.rating,
        "like_count": r.likes.count(),
        "is_liked": r.likes.filter(user=request.user).exists(),
        "recent_likes": r.recent_likes,
        "created_at": r.created_at,
        "has_spoiler": r.has_spoiler,                  
        "spoiler_confidence": r.spoiler_confidence,    
        "spoiler_reasoning": r.spoiler_reasoning,
        "user": {
            "id": r.user.id,
            "username": r.user.username,
            "avatar": request.build_absolute_uri(r.user.avatar.url) if r.user.avatar else None
        }
    }
    for r in reviews
]

    return Response(data)