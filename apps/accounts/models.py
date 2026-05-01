from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .managers import UserManager
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from cloudinary.models import CloudinaryField 

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(unique=True, max_length=50)
    
    avatar = CloudinaryField(
        'avatar',
        folder='cinehub/avatars/',
        transformation=[
            {'width': 400, 'height': 400, 'crop': 'fill', 'gravity': 'face'},
            {'quality': 'auto', 'fetch_format': 'auto'}
        ],
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    mfa_enabled = models.BooleanField(default=False)
    mfa_secret = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)  # 👈 ADD THIS LINE
    verification_code = models.CharField(max_length=6, blank=True, null=True)
    code_created_at = models.DateTimeField(null=True, blank=True)
    
    auth_provider = models.CharField(max_length=20, default="email")

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email
    
from django.db.models.signals import pre_save
from django.dispatch import receiver
import cloudinary.uploader

@receiver(pre_save, sender=User)
def auto_delete_old_avatar(sender, instance, **kwargs):
    """Delete old avatar from Cloudinary when user uploads new one"""
    if not instance.pk:
        return False

    try:
        old_user = User.objects.get(pk=instance.pk)
        old_avatar = old_user.avatar
        new_avatar = instance.avatar

        if old_avatar and old_avatar != new_avatar:
            # Delete from Cloudinary
            cloudinary.uploader.destroy(old_avatar.public_id)
    except User.DoesNotExist:
        pass
    except Exception as e:
        print(f"Error deleting old avatar: {e}")    