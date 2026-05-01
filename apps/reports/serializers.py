from rest_framework import serializers
from .models import ReviewReport


class CreateReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReviewReport
        fields = ["review", "reason"]

    def validate(self, data):
        user = self.context["request"].user
        review = data["review"]
        reason = data['reason']

        if ReviewReport.objects.filter(reporter=user, review=review, reason=reason).exists():
            raise serializers.ValidationError("You already reported this for the same reason.")

        return data


class ReportListSerializer(serializers.ModelSerializer):
    reporter_email = serializers.SerializerMethodField()
    review_user = serializers.SerializerMethodField()
    review_content = serializers.SerializerMethodField()
    review_id = serializers.IntegerField(source="review.id", read_only=True)
    is_hidden = serializers.SerializerMethodField()
    is_spoiler = serializers.SerializerMethodField()

    class Meta:
        model = ReviewReport
        fields = [
            "id",
            "review_id",
            "reporter_email",
            "review_user",
            "review_content",
            "reason",
            "created_at",
            'is_hidden',
            'is_spoiler'
            
        ]

    def get_reporter_email(self, obj):
        if obj.reporter:
            return obj.reporter.email
        return "unknown"

    def get_review_user(self, obj):
        if obj.review and obj.review.user:
            return obj.review.user.username
        return "unknown"

    def get_review_content(self, obj):
        if obj.review:
            return obj.review.content
        return "No content"
    
    def get_is_hidden(self, obj):
        return obj.review.is_hidden if obj.review else False

    def get_is_spoiler(self, obj):
        return obj.review.is_spoiler if obj.review else False