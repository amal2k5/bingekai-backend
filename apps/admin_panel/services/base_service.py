from django.contrib.auth import get_user_model

User = get_user_model()


def get_total_users():
    return User.objects.count()