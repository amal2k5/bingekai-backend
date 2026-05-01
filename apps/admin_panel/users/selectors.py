from django.contrib.auth import get_user_model
from django.db.models import Count, Q

User = get_user_model()




def get_all_users(*, search=None, is_active=None):
    qs = User.objects.filter(is_staff=False, is_superuser=False)

    if search:
        qs = qs.filter(
            Q(email__icontains=search) |
            Q(username__icontains=search)
        )

    if is_active is not None:
        if isinstance(is_active, str):
            if is_active.lower() == "true":
                qs = qs.filter(is_active=True)
            elif is_active.lower() == "false":
                qs = qs.filter(is_active=False)

    return qs.order_by("-created_at")




def get_user_by_id(user_id):
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        return None
    
    


def get_user_with_activity(user_id):
    user = User.objects.filter(id=user_id).annotate(
        ratings_count=Count('ratings', distinct=True),
        reviews_count=Count('reviews', filter=Q(reviews__is_hidden=False), distinct=True),
        lists_count=Count('movie_lists', distinct=True),
        followers_count=Count('followers_set', distinct=True),
        following_count=Count('following_set', distinct=True),
        likes_received_count=Count(
        'reviews__likes',
        filter=Q(reviews__is_hidden=False),
        distinct=True)).first()

    if not user:
        return None

    return {
        "user": user,
        "stats": {
            "ratings_count": user.ratings_count,
            "reviews_count": user.reviews_count,
            "lists_count": user.lists_count,
            "followers_count": user.followers_count,
            "following_count": user.following_count,
            "likes_received_count": user.likes_received_count,
        }
    }