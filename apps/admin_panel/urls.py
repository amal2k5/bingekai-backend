from django.urls import path, include
from .views import AdminAnalyticsView

urlpatterns = [
    path('users/', include('apps.admin_panel.users.urls')),
    path('analytics/', AdminAnalyticsView.as_view()), 
]