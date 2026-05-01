from rest_framework import serializers
from .models import Collection, CollectionItem
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import serializers
from .models import Collection, CollectionItem


class CollectionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionItem
        fields = [
            "id",
            "movie_id",
            "is_watched",
            "added_at",
            "watched_at"
        ]
        read_only_fields = ["added_at", "watched_at"]
        
        
        

class CollectionSerializer(serializers.ModelSerializer):
    items = CollectionItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Collection
        fields = [
            "id",
            "name",
            "created_at",
            "item_count",
            "items"
        ]
        read_only_fields = ["created_at"]

    def get_item_count(self, obj):
        return obj.items.count()
        
        
class CollectionListSerializer(serializers.ModelSerializer):
    item_count = serializers.IntegerField(source="items.count", read_only=True)

    class Meta:
        model = Collection
        fields = [
            "id",
            "name",
            "item_count"
        ]      
        
        
class CollectionItemUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CollectionItem
        fields = ["is_watched"]        