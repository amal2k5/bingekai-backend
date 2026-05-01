from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Follow

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'avatar']
    
    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class FollowSerializer(serializers.ModelSerializer):
    follower = UserBasicSerializer(read_only=True)
    following = UserBasicSerializer(read_only=True)
    follower_id = serializers.IntegerField(write_only=True, required=False)
    following_id = serializers.IntegerField(write_only=True, required=False)
    status = serializers.CharField(read_only=True)
    
    class Meta:
        model = Follow
        fields = [
            'id',
            'follower',
            'following', 
            'follower_id',
            'following_id',
            'is_accepted',
            'status',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        follower_id = attrs.get('follower_id')
        following_id = attrs.get('following_id')
        
        if follower_id and following_id and follower_id == following_id:
            raise serializers.ValidationError("Users cannot follow themselves")
        
        return attrs

    def create(self, validated_data):
        follower_id = validated_data.pop('follower_id', None)
        following_id = validated_data.pop('following_id', None)
        
        if follower_id:
            try:
                validated_data['follower'] = User.objects.get(id=follower_id)
            except User.DoesNotExist:
                raise serializers.ValidationError("Follower user does not exist")
        
        if following_id:
            try:
                validated_data['following'] = User.objects.get(id=following_id)
            except User.DoesNotExist:
                raise serializers.ValidationError("Following user does not exist")
        
        return super().create(validated_data)


class FollowRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    
    def validate_user_id(self, value):
        try:
            User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")
        return value


class FollowListSerializer(serializers.ModelSerializer):
    follower_username = serializers.CharField(source='follower.username', read_only=True)
    following_username = serializers.CharField(source='following.username', read_only=True)
    follower_avatar = serializers.SerializerMethodField()
    following_avatar = serializers.SerializerMethodField()
    follower_name = serializers.SerializerMethodField()
    following_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Follow
        fields = [
            'id',
            'follower_id',
            'following_id',
            'follower_username',
            'following_username',
            'follower_avatar',
            'following_avatar',
            'follower_name',
            'following_name',
            'is_accepted',
            'status',
            'created_at'
        ]
    
    def get_follower_avatar(self, obj):
        if obj.follower.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.follower.avatar.url)
            return obj.follower.avatar.url
        return None
    
    def get_following_avatar(self, obj):
        if obj.following.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.following.avatar.url)
            return obj.following.avatar.url
        return None
    
    def get_follower_name(self, obj):
        # ✅ Fix: Use username instead of get_full_name()
        return obj.follower.username
    
    def get_following_name(self, obj):
        # ✅ Fix: Use username instead of get_full_name()
        return obj.following.username

class UserFollowStatsSerializer(serializers.Serializer):
    followers_count = serializers.IntegerField()
    following_count = serializers.IntegerField()
    pending_requests_count = serializers.IntegerField()
    is_following = serializers.BooleanField(required=False)
    is_followed_by = serializers.BooleanField(required=False)


class FollowActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['accept', 'decline'])
    follow_id = serializers.IntegerField()
    
    def validate_follow_id(self, value):
        try:
            Follow.objects.get(id=value)
        except Follow.DoesNotExist:
            raise serializers.ValidationError("Follow request does not exist")
        return value


class BulkFollowSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        max_length=100
    )
    
    def validate_user_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate user IDs not allowed")
        
        existing_users = User.objects.filter(id__in=value).values_list('id', flat=True)
        missing_users = set(value) - set(existing_users)
        
        if missing_users:
            raise serializers.ValidationError(f"Users with IDs {missing_users} do not exist")
        
        return value


class UserSearchSerializer(serializers.ModelSerializer):
    follower_count = serializers.IntegerField(read_only=True)
    mutual_count = serializers.IntegerField(read_only=True, required=False)
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 
            'username', 
            'first_name',    
            'last_name',      
            'avatar',
            'follower_count',
            'mutual_count'     
        ]
    
    def get_avatar(self, obj):
        if obj.avatar:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None