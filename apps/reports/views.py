from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .serializers import CreateReportSerializer, ReportListSerializer
from .selectors import get_pending_reports_grouped, get_resolved_reports
from .services import create_report, handle_report_action
from reviews.models import Review
from .models import ReviewReport





class CreateReportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateReportSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            create_report(
                user=request.user,
                review=serializer.validated_data["review"],
                reason=serializer.validated_data["reason"]
            )

            return Response(
                {"message": "Report submitted"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class AdminReportListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        data = get_pending_reports_grouped()
        return Response(data)





class AdminReportActionView(APIView):
    permission_classes = [IsAdminUser]

    VALID_ACTIONS = ["hide", "unhide", "spoiler", "unspoiler", "delete"]

    def patch(self, request, report_id):
        action = request.data.get("action")

        if action not in self.VALID_ACTIONS:
            return Response(
                {"error": "Invalid action"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            report = ReviewReport.objects.select_related("review").get(id=report_id)
        except ReviewReport.DoesNotExist:
            return Response({"error": "Report not found"}, status=404)

        handle_report_action(report=report, action=action)

        if not report.is_resolved:
            report.is_resolved = True
            report.save(update_fields=["is_resolved"])

        return Response({
            "message": f"Action '{action}' applied"
        }, status=status.HTTP_200_OK)
        




class AdminReviewActionView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, review_id):
        action = request.data.get("action")

        VALID_ACTIONS = ["hide", "unhide", "spoiler", "unspoiler", "delete"]

        if action not in VALID_ACTIONS:
            return Response({"error": "Invalid action"}, status=400)

        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)

        if action == "hide":
            review.is_hidden = True
        elif action == "unhide":
            review.is_hidden = False
        elif action == "spoiler":
            review.is_spoiler = True
        elif action == "unspoiler":
            review.is_spoiler = False
        elif action == "delete":
            review.delete()

            ReviewReport.objects.filter(
                review_id=review_id,
                is_resolved=False
            ).update(is_resolved=True)

            return Response({"message": "Review deleted"}, status=200)

        review.save(update_fields=["is_hidden", "is_spoiler"])

        ReviewReport.objects.filter(
            review=review,
            is_resolved=False
        ).update(is_resolved=True)

        return Response({"message": f"{action} applied"}, status=200)
    
    
    
class AdminResolvedReportListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        reports = get_resolved_reports()
        return Response(reports)