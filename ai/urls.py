from django.urls import path
from . import views

app_name = 'ai'

urlpatterns = [

    path('recommendations/async/trigger/', views.trigger_recommendations, name='trigger-recommendations-async'),
    path('recommendations/async/status/<str:task_id>/', views.get_task_status, name='task-status-async'),
    path('recommendations/async/results/', views.get_recommendations, name='get-recommendations-async'),
    

    path('recommendations/trigger/', views.trigger_recommendations, name='trigger-recommendations'),
    path('recommendations/status/<str:task_id>/', views.get_task_status, name='task-status'),
    path('recommendations/', views.get_recommendations, name='get-recommendations'),
]