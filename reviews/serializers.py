from rest_framework import serializers
from .models import Review, Like
from django.contrib.auth import get_user_model

User = get_user_model()





class ReviewUserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "avatar"]

    def get_avatar(self, obj):
        request = self.context.get("request")
        if obj.avatar:
            return request.build_absolute_uri(obj.avatar.url) if request else obj.avatar.url
        return None


class ReviewSerializer(serializers.ModelSerializer):
    user = ReviewUserSerializer(read_only=True)  
    is_owner = serializers.SerializerMethodField()
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            "id",
            "movie_id",
            "content",
            "rating",
            "user",         
            "is_owner",
            "created_at",
            "like_count",
            "is_liked",
            "has_spoiler",
            "is_spoiler",
            "spoiler_confidence",
            "spoiler_reasoning",
            "is_spoiler_overridden",
            "is_hidden",
            
        ]
        read_only_fields = ["user", "is_owner", "created_at"]

    def get_is_owner(self, obj):
        request = self.context.get("request")
        return request and request.user == obj.user

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value

    def validate_content(self, value):
        if not value.strip():
            raise serializers.ValidationError("Review cannot be empty")
        return value

    def validate(self, data):
        request = self.context.get("request")
        if request and request.user:
            movie_id = data.get("movie_id")
            if Review.objects.filter(user=request.user, movie_id=movie_id).exists():
                raise serializers.ValidationError("You already reviewed this movie")
        return data

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get("request")

        if not request or not request.user.is_authenticated:
            return False

        return obj.likes.filter(user=request.user).exists()



class UserActivitySerializer(serializers.Serializer):
    movie_id = serializers.IntegerField()
    rating = serializers.FloatField(allow_null=True)
    review = serializers.CharField(allow_null=True)



class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["id", "user", "review", "created_at"]
        read_only_fields = ["user", "created_at"]
