from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from apps.admin_panel.services.admin_analytics_service import get_admin_dashboard
from datetime import datetime, date
from typing import Optional, Tuple




class AdminAnalyticsView(APIView):
    permission_classes = [IsAdminUser]
    
    MAX_DAYS_RANGE = 365
    DEFAULT_DAYS = 7
    VALID_DAYS_OPTIONS = {1, 7, 30, 90}
    DATE_FORMAT = "%Y-%m-%d"


    def get(self, request):
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if start_date and end_date:
            return self._handle_date_range(start_date, end_date)
        
        return self._handle_days_param(request.query_params.get("days"))
    
    

    def _handle_date_range(self, start_date_str: str, end_date_str: str) -> Response:
        try:
            start_date, end_date = self._parse_and_validate_dates(start_date_str, end_date_str)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)
        
        data = get_admin_dashboard(start_date=start_date, end_date=end_date)
        return Response(data)



    def _parse_and_validate_dates(self, start_date_str: str, end_date_str: str) -> Tuple[date, date]:
        try:
            start_date = datetime.strptime(start_date_str, self.DATE_FORMAT).date()
            end_date = datetime.strptime(end_date_str, self.DATE_FORMAT).date()
        except ValueError:
            raise ValueError("Invalid date format. Use YYYY-MM-DD")

        if start_date > end_date:
            raise ValueError("Start date must be before or equal to end date")

        if (end_date - start_date).days > self.MAX_DAYS_RANGE:
            raise ValueError(f"Date range cannot exceed {self.MAX_DAYS_RANGE} days")

        return start_date, end_date



    def _handle_days_param(self, days_param: Optional[str]) -> Response:
        days = self._get_validated_days(days_param)
        data = get_admin_dashboard(days=days)
        return Response(data)



    def _get_validated_days(self, days_param: Optional[str]) -> int:
        if days_param:
            try:
                days = int(days_param)
                if days in self.VALID_DAYS_OPTIONS:
                    return days
            except ValueError:
                pass
        return self.DEFAULT_DAYS