from django.db import models
from django.contrib.auth import get_user_model
from reviews.models import Review

User = get_user_model()


class ReviewReport(models.Model):
    REPORT_REASON_CHOICES = [
    ("spoiler", "Spoiler"),
    ("abusive", "Abusive / Hate Speech"),
    ("harassment", "Harassment"),
    ("spam", "Spam / Promotion"),
    ("irrelevant", "Irrelevant / Off-topic"),
    ("misleading", "Misleading / False Info"),
    ("sensitive", "Sensitive Content"),
]

    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submitted_reports"
    )

    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="reports"
    )

    reason = models.CharField(max_length=20, choices=REPORT_REASON_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        unique_together = ("reporter", "review", 'reason')

    def __str__(self):
        return f"{self.reporter} → {self.review} ({self.reason})"