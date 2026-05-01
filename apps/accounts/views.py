from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.utils import timezone
from django.db.models import Count, Q
from django.core.cache import cache
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken
import jwt
from dj_rest_auth.registration.views import SocialLoginView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from .models import User
from reviews.models import Review
from ratings.models import Rating
from lists.models import *
from .serializers import VerifyEmailSerializer, RegisterSerializer, ResendOTPSerializer
from .utils import generate_otp, send_verification_email
from datetime import datetime, timedelta
import pyotp
import qrcode
import base64
from io import BytesIO
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from .models import User
from .serializers import UserSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .serializers import *
from django.utils import timezone
User = get_user_model()
User.objects.all()






class RegisterView(APIView):

    def post(self, request):

        email = request.data.get("email")

        existing_user = User.objects.filter(email=email).first()

        if existing_user:

            if existing_user.is_verified:
                return Response(
                    {"error": "Email already registered. Please login."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            otp = generate_otp()

            existing_user.verification_code = otp
            existing_user.code_created_at = timezone.now()
            existing_user.save()

            send_verification_email(existing_user.email, otp)

            return Response(
                {"message": "Account already exists but not verified. OTP resent."},
                status=status.HTTP_200_OK
            )

        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():

            user = serializer.save()

            otp = generate_otp()

            user.verification_code = otp
            user.code_created_at = timezone.now()
            user.is_verified = False
            user.save()

            send_verification_email(user.email, otp)

            return Response(
                {"message": "Verification code sent to your email"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise AuthenticationFailed("Invalid email or password")

        if user.auth_provider == "google":
            return Response(
                {"error": "This account uses Google login. Please continue with Google."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(password):
            raise AuthenticationFailed("Invalid email or password")

        if not user.is_active:
            return Response(
                {"error": "Account is deactivated."},
                status=status.HTTP_403_FORBIDDEN
            )

        if not user.is_verified and not user.is_staff:
            return Response(
                {"error": "Email not verified"},
                status=status.HTTP_403_FORBIDDEN
            )

 
        if user.mfa_enabled:
            payload = {
                "user_id": user.id,
                "exp": datetime.utcnow() + timedelta(minutes=5),
                "type": "mfa"
            }
            temp_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
            return Response({
                "mfa_required": True,
                "temp_token": temp_token
            })

        
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }
        })


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Logout successful"},
                status=status.HTTP_205_RESET_CONTENT
            )
        except Exception:
            return Response(
                {"error": "Invalid token"},
                status=status.HTTP_400_BAD_REQUEST
            )        
        


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter

    def get_response(self):
        response = super().get_response()

        user = self.user

        if not hasattr(user, "auth_provider") or user.auth_provider != "google":
            user.auth_provider = "google"

        if user.has_usable_password():
            user.set_unusable_password()

        user.is_verified = True

        user.save()
 
        refresh = RefreshToken.for_user(user)

        response.data["access"] = str(refresh.access_token)
        response.data["refresh"] = str(refresh)

        return response
    

    
#- email verification view

class VerifyEmailView(APIView):

    def post(self, request):

        serializer = VerifyEmailSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data["email"]
        code = serializer.validated_data["code"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if user.verification_code != code:
            return Response({"error": "Invalid verification code"}, status=400)

        if timezone.now() > user.code_created_at + timedelta(minutes=10):
            return Response({"error": "Verification code expired"}, status=400)

        user.is_verified = True
        user.verification_code = None
        user.code_created_at = None
        user.save()

        return Response({"message": "Email verified successfully"})    
    
    

    
#- resend otp view
    
class ResendOTPView(APIView):

    def post(self, request):

        serializer = ResendOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        if user.is_verified:
            return Response({"message": "Email already verified"}, status=400)


        otp = generate_otp()

        user.verification_code = otp
        user.code_created_at = timezone.now()
        user.save()

        send_verification_email(user.email, otp)

        return Response({"message": "New verification code sent"})
    
   
    

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
  
        serializer = UserSerializer(user, context={'request': request})
        data = serializer.data
        

        if user.avatar:
            data['avatar_url'] = request.build_absolute_uri(user.avatar.url)
        else:
            data['avatar_url'] = None
        
     
        data['mfa_enabled'] = user.mfa_enabled
        
        return Response(data)

    def patch(self, request):
        user = request.user
        
       
        if 'avatar' in request.FILES:
            file = request.FILES['avatar']
            
           
            allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
            if file.content_type not in allowed_types:
                return Response(
                    {"detail": "Invalid file type. Use JPG, PNG, or WEBP"},
                    status=status.HTTP_400_BAD_REQUEST
                )
      
            if file.size > 5 * 1024 * 1024:
                return Response(
                    {"detail": "File size must be less than 5MB"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user.avatar = file
        
      
        if 'username' in request.data:
            user.username = request.data['username']
        
        user.save()
        
   
        avatar_url = None
        if user.avatar:
            avatar_url = request.build_absolute_uri(user.avatar.url)
        
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar": user.avatar.url if user.avatar else None,
            "avatar_url": avatar_url,
            "mfa_enabled": user.mfa_enabled,
        })
       

#- Multi factor authentication view

class MFASetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user


        if user.mfa_enabled:
            return Response(
                {"error": "MFA already enabled"},
                status=400
            )


        if not user.mfa_secret:
            user.mfa_secret = pyotp.random_base32()
            user.save()

        secret = user.mfa_secret

   
        totp = pyotp.TOTP(secret)
        otp_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name="BingeKai"
        )


        qr = qrcode.make(otp_uri)

        buffer = BytesIO()
        qr.save(buffer, format="PNG")

        qr_base64 = base64.b64encode(buffer.getvalue()).decode()

        return Response({
            "qr_code": qr_base64
        })




#- mfa verify view

class MFAVerifySetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        otp = str(request.data.get("otp", "")).strip()

        if not otp:
            return Response({"error": "OTP required"}, status=400)

        if not user.mfa_secret:
            return Response({"error": "MFA setup not started"}, status=400)

        totp = pyotp.TOTP(user.mfa_secret)


        if not totp.verify(otp, valid_window=1):
            return Response({"error": "Invalid OTP"}, status=400)

        user.mfa_enabled = True
        user.save()

        return Response({"message": "MFA enabled successfully"})
    

    
#- mfa login verification
class MFAVerifyLoginView(APIView):

    def post(self, request):
        temp_token = request.data.get("temp_token")
        otp = str(request.data.get("otp", "")).strip()

        if not temp_token:
            return Response({"error": "Temp token required"}, status=400)

        if not otp:
            return Response({"error": "OTP required"}, status=400)

        try:
            payload = jwt.decode(
                temp_token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
            user_id = payload.get("user_id")

        except jwt.ExpiredSignatureError:
            return Response({"error": "Session expired"}, status=401)

        except jwt.InvalidTokenError:
            return Response({"error": "Invalid token"}, status=401)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

  
        if not user.is_active:
            return Response({"error": "Account is deactivated"}, status=403)

        if not user.mfa_enabled:
            return Response({"error": "MFA not enabled"}, status=400)

        totp = pyotp.TOTP(user.mfa_secret)

        if not totp.verify(otp, valid_window=2):
            return Response({"error": "Invalid OTP"}, status=400)


        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "email": user.email,
            "username": user.username
        })
        
        
class MFADisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.mfa_enabled:
            return Response(
                {"error": "MFA is not enabled"},
                status=400
            )

        user.mfa_enabled = False
        user.mfa_secret = None
        user.save()

        return Response({
            "message": "MFA disabled successfully"
        })       
        
        
        
#- public profile view

class PublicProfileView(APIView):

    def get(self, request, user_id):

        cache_key = f"profile:{user_id}"

    
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        user_data = (
            User.objects
            .filter(id=user_id)
            .annotate(
                ratings_count=Count("ratings", distinct=True),
                reviews_count=Count(
                    "reviews",
                    filter=Q(reviews__is_hidden=False),
                    distinct=True
                ),
                lists_count=Count(
                    "movie_lists",
                    filter=Q(movie_lists__is_public=True),
                    distinct=True
                ),
                followers_count=Count("followers_set", distinct=True),
                following_count=Count("following_set", distinct=True),   
            )
            .values("id", "username", "avatar", "ratings_count", "reviews_count", "lists_count", "followers_count", "following_count")
            .first()
        )

        if not user_data:
            return Response({"error": "User not found"}, status=404)

        ratings_data = list(
            Rating.objects
            .filter(user_id=user_id)
            .exclude(
                movie_id__in=Review.objects.filter(
                    user_id=user_id,
                    is_hidden=True
                ).values_list("movie_id", flat=True)
            )
            .order_by("-created_at")[:50]
            .values("movie_id", "rating")
        )

        reviews_queryset = (
            Review.objects
            .filter(user_id=user_id, is_hidden=False)
            .prefetch_related("likes")
            .order_by("-created_at")[:50]
        )

        reviews_data = []
        for rev in reviews_queryset:
            reviews_data.append({
                "id": rev.id,
                "movie_id": rev.movie_id,
                "review": rev.content,
                "like_count": rev.likes.count(),
                "is_liked": (
                    rev.likes.filter(user=request.user).exists()
                    if request.user.is_authenticated else False
                ),
                "has_spoiler": rev.has_spoiler,
                "is_spoiler": rev.is_spoiler,
                "is_spoiler_overridden": rev.is_spoiler_overridden,
                "spoiler_confidence": rev.spoiler_confidence,
                "spoiler_reasoning": rev.spoiler_reasoning,
                "created_at": rev.created_at,
            })

        public_lists = (
            MovieList.objects
            .filter(user_id=user_id, is_public=True)
            .order_by("-created_at")[:50]
        )

        lists_data = []
        for movie_list in public_lists:
            items = MovieListItem.objects.filter(
                movie_list=movie_list
            ).order_by("-added_at")

            lists_data.append({
                "id": movie_list.id,
                "name": movie_list.name,
                "description": movie_list.description,
                "created_at": movie_list.created_at,
                "items_count": items.count(),
                "items": [
                    {
                        "movie_id": item.movie_id,
                        "added_at": item.added_at
                    }
                    for item in items
                ]
            })

        avatar_url = None
        if user_data.get("avatar"):
            avatar_field = user_data["avatar"]
            if hasattr(avatar_field, 'url'):
                avatar_url = avatar_field.url
         
                if avatar_url.startswith('/'):
                    avatar_url = request.build_absolute_uri(avatar_url)
            elif isinstance(avatar_field, str):
                avatar_url = request.build_absolute_uri(f"/media/{avatar_field}") if avatar_field else None

        response_data = {
            "user": {
                "id": user_data["id"],
                "username": user_data["username"],
                "avatar": avatar_url,  # ✅ Fixed avatar URL
            },
            "stats": {
                "total_ratings": user_data["ratings_count"],
                "total_reviews": user_data["reviews_count"],
                "total_lists": user_data["lists_count"],
                "followers_count": user_data["followers_count"],   
                "following_count": user_data["following_count"],   
            },
            "ratings": ratings_data,
            "reviews": reviews_data,
            "lists": lists_data,
        }

        cache.set(cache_key, response_data, 300)

        return Response(response_data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    user = request.user
    from reviews.models import Like
    count = Like.objects.filter(review__user=user).count()
    print(f"Total likes for {user.username}: {count}") 
    
    serializer = UserSerializer(request.user, context={'request': request})
    return Response(serializer.data)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_avatar(request):
    if 'avatar' not in request.FILES:
        return Response(
            {'error': 'No file provided'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    

    if user.avatar:
        try:
            import cloudinary.uploader
            cloudinary.uploader.destroy(user.avatar.public_id)
        except:
            pass
    
    user.avatar = request.FILES['avatar']
    user.save()
    
  
    serializer = UserSerializer(user, context={'request': request})
    return Response(serializer.data, status=status.HTTP_200_OK)