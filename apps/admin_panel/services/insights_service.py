from django.db.models import Count
from reviews.models import Like
from django.contrib.auth import get_user_model

User = get_user_model()


def get_most_followed_users(limit=5):
    return list(
        User.objects.annotate(followers_count=Count("followers_set"))
        .order_by("-followers_count")[:limit]
        .values("username", "followers_count")
    )


def get_most_liked_users(limit=5):
    return [
        {
            "user_id": u["review__user__id"],
            "username": u["review__user__username"],
            "likes_count": u["likes_count"],
        }
        for u in Like.objects
        .values("review__user__id", "review__user__username")
        .annotate(likes_count=Count("id"))
        .order_by("-likes_count")[:limit]
    ]