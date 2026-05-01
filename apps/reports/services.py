from .models import ReviewReport
from reviews.services import *
from .models import ReviewReport




def create_report(*, user, review, reason):
    return ReviewReport.objects.create(
        reporter=user,
        review=review,
        reason=reason
    )


def resolve_report(report):
    report.is_resolved = True
    report.save(update_fields=["is_resolved"])
    return report




from django.core.cache import cache   

def handle_report_action(*, report, action):
    review = report.review

    if action == "hide":
        hide_review(review)

    elif action == "unhide":
        unhide_review(review)

    elif action == "spoiler":
        mark_spoiler(review)

    elif action == "unspoiler":
        unmark_spoiler(review)

    elif action == "delete":
        delete_review(review)

    else:
        raise ValueError("Invalid action")

    cache.delete(f"profile:{review.user_id}")

    report.is_resolved = True
    report.save(update_fields=["is_resolved"])

    return report