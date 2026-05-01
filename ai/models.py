from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Recommendation(models.Model):
    # ✅ Remove unique=True - allow multiple recommendations per user
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_recommendations'
    )
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_recommendation'
        ordering = ['-created_at']  # Show newest first

    def __str__(self):
        return f"Recommendations for {self.user} at {self.created_at}"