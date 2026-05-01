from .models import ReviewReport
from django.db.models import Count
from collections import defaultdict




def get_pending_reports_grouped():
    reports = (
        ReviewReport.objects
        .filter(is_resolved=False)
        .select_related("review", "review__user", "reporter")
    )

    grouped = defaultdict(list)

    for r in reports:
        grouped[r.review.id].append(r)

    result = []

    for review_id, group in grouped.items():
        review = group[0].review

        result.append({
            "review_id": review.id,
            "review_content": review.content,
            "review_user": review.user.username,

            # 🔥 FIXES
            "reporter_email": group[0].reporter.email,
            "created_at": group[0].created_at,
            "reason": group[0].reason,

            "reasons": list(set(r.reason for r in group)),
            "total_reports": len(group),
        })

    return sorted(result, key=lambda x: x["total_reports"], reverse=True)




def get_resolved_reports():
    reports = (
        ReviewReport.objects
        .filter(is_resolved=True)
        .select_related("review", "review__user", "reporter")
    )

    grouped = defaultdict(list)

    for r in reports:
        grouped[r.review.id].append(r)

    result = []

    for review_id, group in grouped.items():
        review = group[0].review

        result.append({
            "review_id": review.id,
            "review_content": review.content,
            "review_user": review.user.username,
            "reporter_email": group[0].reporter.email,
            "reason": group[0].reason,
            "created_at": group[0].created_at,
            "is_hidden": review.is_hidden,
            "is_spoiler": review.is_spoiler,
        })

    return result