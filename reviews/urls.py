from django.urls import path
from .views import *


urlpatterns = [
    
    path("movie/<int:movie_id>/", MovieReviewListView.as_view()),
    path("create/", CreateReviewView.as_view()),
    path("update/<int:pk>/", UpdateReviewView.as_view()),
    path("delete/<int:pk>/", DeleteReviewView.as_view()),
    path("user/activity/", UserActivityView.as_view()),
    path('<int:review_id>/like/', toggle_like, name='toggle-like'),
    path('trending/', trending_reviews, name='trending-reviews'),
        
]