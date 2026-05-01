from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class MovieList(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="movie_lists")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_public = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.user})"


class MovieListItem(models.Model):
    movie_list = models.ForeignKey(MovieList, on_delete=models.CASCADE, related_name="items")
    movie_id = models.IntegerField()  

    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("movie_list", "movie_id")

    def __str__(self):
        return f"{self.movie_id} in {self.movie_list.name}"