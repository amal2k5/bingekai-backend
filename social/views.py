from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from .models import Follow
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Count, Q, F, Max
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from reviews.serializers import ReviewSerializer
from ratings.models import Rating
from reviews.models import Review

User = get_user_model()




class FollowViewSet(viewsets.ModelViewSet):
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Follow.objects.select_related('follower', 'following').filter(
            follower=self.request.user
        )
    
    def get_serializer_class(self):
        if self.action in ['list', 'followers', 'following', 'pending_requests', 'sent_requests']:
            return FollowListSerializer
        elif self.action in ['send_request', 'unfollow']:
            return FollowRequestSerializer
        return FollowSerializer
    
    def get_serializer_context(self):
        # ✅ Pass request context to serializer for absolute URLs
        context = super().get_serializer_context()
        context.update({'request': self.request})
        return context
    
    @action(detail=False, methods=['post'])
    def send_request(self, request):
        serializer = FollowRequestSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            target_user = get_object_or_404(User, id=user_id)
            
            if target_user == request.user:
                return Response(
                    {'error': 'Cannot follow yourself'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            follow, created = Follow.objects.get_or_create(
                follower=request.user,
                following=target_user,
                defaults={'is_accepted': False}
            )
            
            if created:
                return Response(
                    FollowSerializer(follow, context={'request': request}).data,
                    status=status.HTTP_201_CREATED
                )
            else:
                return Response(
                    {'error': 'Follow request already exists'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        follow = get_object_or_404(Follow, id=pk, following=request.user)
        
        if follow.is_accepted:
            return Response(
                {'error': 'Follow request has already been accepted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        follow.accept()
        return Response(FollowSerializer(follow, context={'request': request}).data)
    
    @action(detail=True, methods=['post'])
    def decline(self, request, pk=None):
        follow = get_object_or_404(
            Follow, 
            id=pk, 
            following=request.user, 
            is_accepted=False
        )
        follow.decline()
        return Response({'message': 'Follow request declined'})
    
    @action(detail=False, methods=['post'])
    def unfollow(self, request):
        serializer = FollowRequestSerializer(data=request.data)
        if serializer.is_valid():
            user_id = serializer.validated_data['user_id']
            try:
                follow = Follow.objects.get(
                    follower=request.user,
                    following_id=user_id,
                    is_accepted=True
                )
                follow.delete()
                return Response({'message': 'Unfollowed successfully'})
            except Follow.DoesNotExist:
                return Response(
                    {'error': 'Not following this user'},
                    status=status.HTTP_404_NOT_FOUND
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def pending_requests(self, request):
        follows = Follow.objects.get_pending_requests(request.user)
        serializer = FollowListSerializer(follows, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def sent_requests(self, request):
        follows = Follow.objects.get_sent_requests(request.user)
        serializer = FollowListSerializer(follows, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def followers(self, request):
        user_id = request.query_params.get('user_id')
        user = get_object_or_404(User, id=user_id) if user_id else request.user
        
        follows = Follow.objects.get_followers(user)
        serializer = FollowListSerializer(follows, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def following(self, request):
        user_id = request.query_params.get('user_id')
        user = get_object_or_404(User, id=user_id) if user_id else request.user
        
        follows = Follow.objects.get_following(user)
        serializer = FollowListSerializer(follows, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def relation(self, request):
        user_id = request.query_params.get('user_id')
        target = get_object_or_404(User, id=user_id)

        follow = Follow.objects.filter(
            follower=request.user,
            following=target
        ).first()

        if not follow:
            return Response({"status": "none"})

        if follow.is_accepted:
            return Response({"status": "following"})
    
        return Response({"status": "requested"})
    
    @action(detail=False, methods=['post'])
    def cancel_request(self, request):
        user_id = request.data.get("user_id")

        follow = get_object_or_404(
            Follow,
            follower=request.user,
            following_id=user_id,
            is_accepted=False
        )

        follow.delete()
        return Response({"message": "Request cancelled"})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        user_id = request.query_params.get('user_id')
        user = get_object_or_404(User, id=user_id) if user_id else request.user
        
        stats = {
            'followers_count': Follow.objects.filter(following=user, is_accepted=True).count(),
            'following_count': Follow.objects.filter(follower=user, is_accepted=True).count(),
            'pending_requests_count': Follow.objects.filter(following=user, is_accepted=False).count(),
        }
        
        if user != request.user:
            stats.update({
                'is_following': Follow.objects.filter(
                    follower=request.user, following=user, is_accepted=True
                ).exists(),
                'is_followed_by': Follow.objects.filter(
                    follower=user, following=request.user, is_accepted=True
                ).exists(),
            })
        
        serializer = UserFollowStatsSerializer(stats)
        return Response(serializer.data)


class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.GET.get("q", "").strip()

        if len(query) < 2:
            return Response(
                {"detail": "Query must be at least 2 characters"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            users = (
                User.objects
                .filter(username__icontains=query)
                .exclude(id=request.user.id)
                .annotate(
                    follower_count=Count(
                        'followers_set',
                        filter=Q(followers_set__is_accepted=True),
                        distinct=True
                    )
                )
                .order_by('-follower_count')
                [:20]
            )

            user_objects = {u.id: u for u in users}

            result = [
                {
                    'id': user.id,
                    'username': user.username,
                    'avatar': request.build_absolute_uri(user.avatar.url) if user.avatar else None,
                    'follower_count': user.follower_count,
                }
                for user in user_objects.values()
            ]

            return Response(result)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response(
                {"detail": "Search failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SuggestedUsersView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            current_user = request.user
            cache_key = f'user_suggestions_{current_user.id}'

            cached_suggestions = cache.get(cache_key)
            if cached_suggestions:
                return Response(cached_suggestions)

            following_ids = list(
                Follow.objects
                .filter(follower=current_user, is_accepted=True)
                .values_list('following_id', flat=True)
            )

            recent_date = timezone.now() - timedelta(days=30)

            suggestions_qs = (
                User.objects
                .exclude(id=current_user.id)
                .exclude(id__in=following_ids)
                .annotate(
                    mutual_count=Count(
                        'followers_set',
                        filter=Q(
                            followers_set__follower_id__in=following_ids,
                            followers_set__is_accepted=True
                        ),
                        distinct=True
                    ),
                    follower_count=Count(
                        'followers_set',
                        filter=Q(followers_set__is_accepted=True),
                        distinct=True
                    ),
                    recent_reviews=Count(
                        'reviews',
                        filter=Q(reviews__created_at__gte=recent_date),
                        distinct=True
                    ),
                    total_reviews=Count('reviews', distinct=True)
                )
                .annotate(
                    relevance_score=(
                        F('mutual_count') * 10 +
                        F('recent_reviews') * 5 +
                        F('follower_count') * 2 +
                        F('total_reviews') * 1
                    )
                )
                .filter(relevance_score__gt=0)
                .order_by('-relevance_score', '-follower_count')
                [:15]
            )

            suggestions = [
                {
                    'id': user.id,
                    'username': user.username,
                    'avatar': request.build_absolute_uri(user.avatar.url) if user.avatar else None,
                    'follower_count': user.follower_count,
                    'mutual_count': user.mutual_count,
                }
                for user in suggestions_qs
            ]

            if len(suggestions) < 5:
                fallback_qs = (
                    User.objects
                    .exclude(id=current_user.id)
                    .exclude(id__in=following_ids)
                    .annotate(
                        follower_count=Count(
                            'followers_set',
                            filter=Q(followers_set__is_accepted=True)
                        )
                    )
                    .order_by('-follower_count')
                    [:15]
                )

                suggestions = [
                    {
                        'id': user.id,
                        'username': user.username,
                        'avatar': request.build_absolute_uri(user.avatar.url) if user.avatar else None,
                        'follower_count': user.follower_count,
                        'mutual_count': 0,
                    }
                    for user in fallback_qs
                ]

            result = list(suggestions)
            cache.set(cache_key, result, 300)

            return Response(result)

        except Exception as e:
            import traceback
            print(f"Suggestions error: {e}")
            traceback.print_exc()
            return Response(
                {"detail": "Failed to load suggestions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PublicUserProfileView(APIView):
    permission_classes = []
    
    def get(self, request, username):
        user = get_object_or_404(User, username=username)
        
        reviews = Review.objects.filter(user=user).prefetch_related('likes').order_by('-created_at')
        ratings = Rating.objects.filter(user=user)
        
        review_serializer = ReviewSerializer(
            reviews, 
            many=True,
            context={'request': request}
        )
        
        return Response({
            "id": user.id,
            "username": user.username,
            "avatar": user.avatar.url if user.avatar else None,
            "reviews": review_serializer.data,
            "total_reviews": reviews.count(),
            "total_ratings": ratings.count(),
        })