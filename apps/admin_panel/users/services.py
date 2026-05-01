from apps.admin_panel.models import AdminActionLog
from django.core.exceptions import ValidationError
from .selectors import get_all_users, get_user_by_id
from apps.admin_panel.services.growth_service import GrowthMetricsService


def list_users(*, search=None, is_active=None):
    return get_all_users(
        search=search,
        is_active=is_active
    )

def deactivate_user(*, target_user_id, performed_by):
    user = get_user_by_id(target_user_id)

    if user.id == performed_by.id:
        raise ValidationError("You cannot deactivate yourself.")

    if user.is_superuser:
        raise ValidationError("Cannot modify superuser.")

    if not user.is_active:
        return user

    user.is_active = False
    user.save(update_fields=["is_active"])


    GrowthMetricsService.invalidate_cache()

    log_admin_action(
        admin=performed_by,
        action="DEACTIVATE_USER",
        target_user=user,
        metadata={
            "previous_state": True,
            "new_state": False
        }
    )
    return user



def activate_user(*, target_user_id, performed_by):
    user = get_user_by_id(target_user_id)

    if user.is_active:
        return user

    user.is_active = True
    user.save(update_fields=["is_active"])

    GrowthMetricsService.invalidate_cache()

    log_admin_action(
        admin=performed_by,
        action="ACTIVATE_USER",
        target_user=user,
        metadata={
            "previous_state": False,
            "new_state": True
        }
    )

    return user


def log_admin_action(*, admin, action, target_user, metadata=None):
    AdminActionLog.objects.create(
        admin=admin,
        action=action,
        target_user=target_user,
        metadata=metadata or {}
    )