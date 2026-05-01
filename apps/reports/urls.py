from django.urls import path
from .views import *

urlpatterns = [
    path("", CreateReportView.as_view()),
    path("admin/", AdminReportListView.as_view()),
    path("admin/<int:report_id>/action/", AdminReportActionView.as_view()),
    path("admin/reviews/<int:review_id>/action/", AdminReviewActionView.as_view()),
    path("admin/resolved/", AdminResolvedReportListView.as_view()),
]