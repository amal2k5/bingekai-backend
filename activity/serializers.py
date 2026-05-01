from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()



class ActivitySerializer(serializers.Serializer):
    user = serializers.SerializerMethodField()
    movie_id = serializers.IntegerField()
    rating = serializers.IntegerField(allow_null=True)
    review = serializers.CharField(allow_null=True)
    review_id = serializers.IntegerField(allow_null=True)

    like_count = serializers.IntegerField(default=0)
    is_liked = serializers.BooleanField(default=False)

    is_spoiler = serializers.BooleanField(default=False)
    is_hidden = serializers.BooleanField(default=False)

    has_spoiler = serializers.BooleanField(default=False)
    spoiler_confidence = serializers.FloatField(default=0.0)
    spoiler_reasoning = serializers.CharField(allow_null=True)

    created_at = serializers.DateTimeField()
    activity_type = serializers.CharField()

    def get_user(self, obj):
        user = obj.get("user")
        if not user:
            return None
        
        avatar_url = None
        if user.avatar:
            request = self.context.get("request")
            if request:
                avatar_url = request.build_absolute_uri(user.avatar.url)
            else:
                avatar_url = user.avatar.url
        
        return {
            "id": user.id,
            "username": user.username,
            "avatar": avatar_url 
        }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']


class MovieSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()



