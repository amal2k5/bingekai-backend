from .models import Collection, CollectionItem
from django.utils import timezone




def add_movie_to_collection(user, collection_id, movie_id):
    collection = Collection.objects.get(id=collection_id, user=user)

    obj, created = CollectionItem.objects.get_or_create(
        collection=collection,
        movie_id=movie_id
    )

    return created


def remove_movie(user, collection_id, movie_id):
    return CollectionItem.objects.filter(
        collection_id=collection_id,
        collection__user=user,
        movie_id=movie_id
    ).delete()


def toggle_watched(user, item_id):
    item = CollectionItem.objects.get(
        id=item_id,
        collection__user=user
    )

    item.is_watched = not item.is_watched
    item.watched_at = timezone.now() if item.is_watched else None
    item.save()

    return item.is_watched