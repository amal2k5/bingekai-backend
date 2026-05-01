from django.db import models
from django.conf import settings




User = settings.AUTH_USER_MODEL

class Collection(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="collections"
    )
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "name")

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class CollectionItem(models.Model):
    collection = models.ForeignKey(
        Collection,
        on_delete=models.CASCADE,
        related_name="items"
    )
    movie_id = models.IntegerField()

    is_watched = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)
    watched_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("collection", "movie_id")

    def __str__(self):
        return f"{self.collection.name} - {self.movie_id}"
    
    
    
    
class WatchedMovie(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie_id = models.IntegerField()
    watched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie_id')    