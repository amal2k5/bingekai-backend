from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    path("profile/", UserProfileView.as_view()),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("google/", GoogleLogin.as_view(), name="google_login"),
    path("verify-email/", VerifyEmailView.as_view(), name="verify-email"),
    path("resend-otp/", ResendOTPView.as_view(), name="resend-otp"),
    
    #- mfa
    path("mfa/setup/", MFASetupView.as_view()),
    path("mfa/verify-setup/", MFAVerifySetupView.as_view()),
    path("mfa/verify-login/", MFAVerifyLoginView.as_view()),
    path("mfa/disable/", MFADisableView.as_view()),
    
    #- public profile
    path("users/<int:user_id>/", PublicProfileView.as_view()),
    
    path('profile/', get_profile, name='get-profile'),
    path('upload-avatar/',upload_avatar, name='upload_avatar'),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)