from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from ratings.views import InternalUserRatingsView, InternalAllRatingsView

urlpatterns = [
    
    path('admin/', admin.site.urls),
    
    path("api/auth/", include("apps.accounts.urls")),  
    
    path("api/movies/", include("apps.movies.urls")),
    
    path('api/ratings/', include('ratings.urls')),
    
    path("api/reviews/", include("reviews.urls")),
    
    path("api/watchlists/", include("watchlists.urls")),
    
    path("api/lists/", include("lists.urls")),
    
    path("api/social/", include("social.urls")),
    
    path("api/activity/", include("activity.urls")),
    
    path("api/recommendations/", include("recommendations.urls")),
    
    path("api/reports/", include("apps.reports.urls")),
    path('api/admin/', include('apps.admin_panel.urls')),
    

    path('api/internal/ratings/<int:user_id>/', InternalUserRatingsView.as_view(), name='internal-user-ratings'),
    path('api/internal/ratings/all/', InternalAllRatingsView.as_view(), name='internal-all-ratings'),
    


    #- Google auth  
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),
    path("accounts/", include("allauth.urls")),  
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)