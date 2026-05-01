from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.movies.services.tmdb_service import TMDBService




tmdb = TMDBService()


class TrendingMoviesView(APIView):

    def get(self, request):
        data = tmdb.get_trending_movies()

        if "error" in data:
            return Response(
                {"message": "Failed to fetch movies", "error": data["error"]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(data, status=status.HTTP_200_OK)
    
    
    

class SearchMoviesView(APIView):
    def get(self, request):
        query = request.query_params.get("q")

        if not query:
            return Response(
                {"error": "Query parameter 'q' is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = tmdb.search_movies(query)

        if "error" in data:
            return Response(
                {"error": data["error"]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(data, status=status.HTTP_200_OK)    
    
    
    
    
class MovieDetailView(APIView):
    def get(self, request, movie_id):
        movie = tmdb.get_movie_details(movie_id)
        credits = tmdb.get_movie_credits(movie_id)

        if "error" in movie:
            return Response(
                {"error": movie["error"]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            "movie": movie,
            "credits": credits
        })    
        
        
        
class MovieDetailView(APIView):
    def get(self, request, movie_id):
        movie = tmdb.get_movie_details(movie_id)
        credits = tmdb.get_movie_credits(movie_id)
        providers = tmdb.get_watch_providers(movie_id)

        return Response({
            "movie": movie,
            "credits": credits,
            "providers": providers
        })        