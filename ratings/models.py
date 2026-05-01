from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name="ratings")
    movie_id = models.IntegerField(db_index=True)  
    rating = models.PositiveSmallIntegerField() 
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'movie_id')
        indexes = [
            models.Index(fields=['movie_id']),
        ]

    def __str__(self):
        return f"{self.user} - {self.movie_id} - {self.rating}"