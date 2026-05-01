from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import MovieList, MovieListItem
from .serializers import MovieListSerializer, MovieListItemSerializer
from rest_framework.views import APIView



#- Create List

class CreateMovieListView(generics.CreateAPIView):
    serializer_class = MovieListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


#- Get User Lists

class UserMovieListsView(generics.ListAPIView):
    serializer_class = MovieListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MovieList.objects.filter(user=self.request.user).order_by("-created_at")
    
    
#- List Detail     
    
class MovieListDetailView(generics.RetrieveAPIView):
    serializer_class = MovieListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MovieList.objects.filter(user=self.request.user)  


#- Delete List

class DeleteMovieListView(generics.DestroyAPIView):
    queryset = MovieList.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MovieList.objects.filter(user=self.request.user)


#- Add Movie to List

class AddMovieToListView(generics.CreateAPIView):
    serializer_class = MovieListItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        list_id = request.data.get("list_id")
        movie_id = request.data.get("movie_id")

    
        if not list_id or not movie_id:
            return Response(
                {"error": "list_id and movie_id are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            movie_list = MovieList.objects.get(id=list_id, user=request.user)
        except MovieList.DoesNotExist:
            return Response({"error": "List not found"}, status=404)

        item, created = MovieListItem.objects.get_or_create(
            movie_list=movie_list,
            movie_id=movie_id
        )

        if not created:
            return Response({"message": "Movie already in list"}, status=200)

        return Response({"message": "Movie added"}, status=201)


#- Remove Movie from List

class RemoveMovieFromListView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, list_id=None, movie_id=None, *args, **kwargs):
        try:
            item = MovieListItem.objects.get(
                movie_list__id=list_id,
                movie_id=movie_id,
                movie_list__user=request.user
            )
            item.delete()
            return Response({"message": "Removed"}, status=200)
        except MovieListItem.DoesNotExist:
            return Response({"error": "Item not found"}, status=404)
        
        
        
class ListDetailView(APIView):
    def get(self, request, list_id):
        try:
            movie_list = MovieList.objects.get(id=list_id, is_public=True)
        except MovieList.DoesNotExist:
            return Response({"error": "List not found"}, status=404)

        
        items = MovieListItem.objects.filter(movie_list=movie_list).order_by('-added_at')

        return Response({
            "id": movie_list.id,
            "name": movie_list.name,
            "description": movie_list.description,
            "user": {
                "id": movie_list.user.id,
                "username": movie_list.user.username
            },
            "created_at": movie_list.created_at,
            "items": [
                {
                    "movie_id": item.movie_id,
                    "added_at": item.added_at
                }
                for item in items
            ]
        })