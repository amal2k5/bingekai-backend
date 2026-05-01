from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews")
    movie_id = models.IntegerField()  
    content = models.TextField()
    rating = models.PositiveSmallIntegerField()  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    has_spoiler = models.BooleanField(default=False)
    spoiler_confidence = models.FloatField(default=0.0)
    spoiler_reasoning = models.TextField(blank=True, null=True)
    is_spoiler = models.BooleanField(default=False)
    is_spoiler_overridden = models.BooleanField(default=False)  
    is_hidden = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "movie_id")
        
    def __str__(self):
        return f"{self.user} - {self.movie_id} ({self.rating})"
   
   
   
    
#- Like system    
class Like(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'review')  
        indexes = [
            models.Index(fields=['review']), 
            models.Index(fields=['user']),     
        ]

    def __str__(self):
        return f"{self.user.username} likes review {self.review.id}"    