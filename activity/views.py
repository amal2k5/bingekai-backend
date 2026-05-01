from rest_framework import generics, permissions
from rest_framework.response import Response
from .serializers import ActivitySerializer
from .services import get_activity_feed



class ActivityFeedView(generics.ListAPIView):
    serializer_class = ActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request, *args, **kwargs):
        limit = min(int(request.query_params.get('limit', 20)), 50)
        activities = get_activity_feed(request.user, limit=limit)
        serializer = self.get_serializer(activities, many=True)
        return Response(serializer.data)