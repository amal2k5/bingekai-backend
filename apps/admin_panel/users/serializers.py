from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'is_active', 'is_staff', 'created_at']
        read_only_fields = ['id', 'email', 'created_at']


class AdminUserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'is_active']
        read_only_fields = ['id', 'email']
        
        
class AdminUserDetailSerializer(serializers.ModelSerializer):
    activity = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "is_active",
            "is_verified",
            "created_at",
            "last_login",
            "activity",
        ]

    def get_activity(self, obj):
        return self.context.get("activity", {})