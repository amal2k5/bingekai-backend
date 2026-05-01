from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import User
from django.db.models import Count

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    total_likes_received = serializers.SerializerMethodField()   
    most_liked_review = serializers.SerializerMethodField()     

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'username',
            'avatar',
            'is_verified',
            'created_at',
            'last_login',  
            'total_likes_received',  
            'most_liked_review',    
        ]

    def get_avatar(self, obj):
        request = self.context.get("request")
        
        if obj.avatar:
            if request:
                
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None

    def get_total_likes_received(self, obj):
        from reviews.models import Like
        return Like.objects.filter(review__user=obj).count()

    def get_most_liked_review(self, obj):
        review = (
            obj.reviews
            .annotate(like_count=Count('likes'))
            .order_by('-like_count')
            .first()
        )
        if not review:
            return None
        return {
            "id": review.id,
            "movie_id": review.movie_id,
            "content": review.content,
            "like_count": review.likes.count(),
        }


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["email", "username", "password"]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class VerifyEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)   


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()