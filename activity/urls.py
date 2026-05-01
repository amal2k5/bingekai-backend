from django.urls import path
from . import views



urlpatterns = [
    path('feed/', views.ActivityFeedView.as_view(), name='activity-feed'),
]