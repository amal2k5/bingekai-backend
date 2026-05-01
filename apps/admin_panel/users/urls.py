from django.urls import path
from .views import *


urlpatterns = [
    path('', AdminUserListView.as_view(), name='admin-user-list'),
    path('<int:user_id>/', AdminUserDetailView.as_view()),
    path('<int:user_id>/deactivate/', AdminDeactivateUserView.as_view()),
    path('<int:user_id>/activate/', AdminActivateUserView.as_view()),
]