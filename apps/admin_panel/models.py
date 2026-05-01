from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AdminActionLog(models.Model):
    ACTION_CHOICES = [
        ("ACTIVATE_USER", "Activate User"),
        ("DEACTIVATE_USER", "Deactivate User"),
    ]

    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="admin_actions"
    )

    action = models.CharField(max_length=50, choices=ACTION_CHOICES)

    target_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="targeted_actions"
    )

    metadata = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin} -> {self.action} -> {self.target_user}"