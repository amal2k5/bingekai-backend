from rest_framework import serializers
from .models import MovieList, MovieListItem


class MovieListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieListItem
        fields = ["id", "movie_id", "added_at"]


class MovieListSerializer(serializers.ModelSerializer):
    items = MovieListItemSerializer(many=True, read_only=True)
    movie_count = serializers.SerializerMethodField() 

    class Meta:
        model = MovieList
        fields = [
            "id",
            "name",
            "description",
            "is_public",
            "created_at",
            "items",
            "movie_count", 
        ]

    def get_movie_count(self, obj): 
        return obj.items.count()