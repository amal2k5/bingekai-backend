from django.db.models import Q
from social.models import Follow
from ratings.models import Rating
from social.models import Follow
from reviews.models import Review


def get_activity_feed(user, limit=20):

    following_ids = list(
        Follow.objects.filter(follower=user)
        .values_list("following_id", flat=True)
    )

    if not following_ids:
        return []

    ratings = (
        Rating.objects.filter(user_id__in=following_ids)
        .select_related("user")
    )


    reviews = (
        Review.objects.filter(
            user_id__in=following_ids,
            is_hidden=False
        )
        .select_related("user")
        .prefetch_related("likes")
    )

    activity_map = {}

    for rating in ratings:
        key = (rating.user_id, rating.movie_id)

        activity_map[key] = {
            "user": rating.user,
            "movie_id": rating.movie_id,
            "rating": rating.rating,
            "review": None,
            "review_id": None,
            "like_count": 0,
            "is_liked": False,

            "has_spoiler": False,
            "is_spoiler": False,
            "is_spoiler_overridden": False,
            "is_hidden": False,
            "spoiler_confidence": 0.0,
            "spoiler_reasoning": None,

            "created_at": rating.created_at,
            "activity_type": "rating",
        }


    for review in reviews:
        key = (review.user_id, review.movie_id)

        like_count = review.likes.count()
        is_liked = review.likes.filter(user=user).exists()

        review_data = {
            "user": review.user,
            "movie_id": review.movie_id,
            "review": review.content,
            "review_id": review.id,
            "like_count": like_count,
            "is_liked": is_liked,
            "has_spoiler": review.has_spoiler,
            "is_spoiler": review.is_spoiler,
            "is_spoiler_overridden": review.is_spoiler_overridden,
            "is_hidden": review.is_hidden,
            "spoiler_confidence": review.spoiler_confidence,
            "spoiler_reasoning": review.spoiler_reasoning,

            "created_at": review.created_at,
        }

        if key in activity_map:

            activity_map[key].update(review_data)

            activity_map[key]["rating"] = activity_map[key]["rating"]
            activity_map[key]["created_at"] = max(
                activity_map[key]["created_at"],
                review.created_at
            )
            activity_map[key]["activity_type"] = "rating_and_review"

        else:

            review_data["rating"] = None
            review_data["activity_type"] = "review"
            activity_map[key] = review_data

    activity_list = [
        item for item in activity_map.values()
        if not (item["review"] is None and item["review_id"] is None)]
    activity_list.sort(key=lambda x: x["created_at"], reverse=True)

    return activity_list[:limit]