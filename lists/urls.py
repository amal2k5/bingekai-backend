from django.urls import path
from .views import *




urlpatterns = [
    
    path("create/", CreateMovieListView.as_view()),
    path("my/", UserMovieListsView.as_view()),
    path("delete/<int:pk>/", DeleteMovieListView.as_view()),
    path("add-movie/", AddMovieToListView.as_view()),
    path("<int:pk>/", MovieListDetailView.as_view()),
    path("collections/<int:list_id>/remove/<int:movie_id>/", RemoveMovieFromListView.as_view()),
    path("public/<int:list_id>/", ListDetailView.as_view()),
    
    
]