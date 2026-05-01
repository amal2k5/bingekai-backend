from django.urls import path
from apps.movies.views.tmdb_views import TrendingMoviesView,SearchMoviesView,MovieDetailView

urlpatterns = [
    
    path("trending/", TrendingMoviesView.as_view(), name="trending-movies"),
    path("search/", SearchMoviesView.as_view()),
    path("<int:movie_id>/", MovieDetailView.as_view()),
]