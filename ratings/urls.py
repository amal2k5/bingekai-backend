from django.urls import path
from .views import RateMovieView, UserRatingView, MovieRatingStatsView, MyRatingsView



urlpatterns = [
    path('rate/', RateMovieView.as_view()),
    path('<int:movie_id>/', UserRatingView.as_view()),
    path('stats/<int:movie_id>/', MovieRatingStatsView.as_view()),
    path("my/", MyRatingsView.as_view()),


]