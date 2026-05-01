from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *


router = DefaultRouter()
router.register(r'follow', FollowViewSet, basename='follow')

urlpatterns = [
    path('', include(router.urls)),
    path('search/', UserSearchView.as_view(), name='user-search'),
    path('suggestions/', SuggestedUsersView.as_view(), name='user-suggestions'),
    path('<str:username>/', PublicUserProfileView.as_view(), name='public-user-profile'), 
]