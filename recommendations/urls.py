from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('async/trigger/', views.trigger_recommendations, name='trigger-async'),
    path('async/status/<str:task_id>/', views.get_task_status, name='async-status'),
    path('async/results/', views.get_saved_recommendations, name='async-results'),
    path('activity/check/', views.check_user_activity, name='check-activity'),
    path('invalidate/', views.invalidate_cache, name='invalidate'),
]