from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError
from .services import list_users, activate_user, deactivate_user
from .serializers import *
from .permissions import IsAdminUserCustom
from rest_framework.permissions import IsAdminUser
from .selectors import get_user_with_activity
from apps.admin_panel.utils.pagination import AdminPagination




class AdminUserListView(APIView):
    permission_classes = [IsAdminUserCustom]

    def get(self, request):
        search = request.query_params.get("search")
        is_active = request.query_params.get("is_active")

        users = list_users(
            search=search,
            is_active=is_active
        )

        paginator = AdminPagination()
        page = paginator.paginate_queryset(users, request)

        serializer = AdminUserSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)




class AdminDeactivateUserView(APIView):
    permission_classes = [IsAdminUserCustom]

    def patch(self, request, user_id):
        try:
            user = deactivate_user(
                target_user_id=user_id,
                performed_by=request.user
            )
        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = AdminUserStatusSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)



class AdminActivateUserView(APIView):
    permission_classes = [IsAdminUserCustom]

    def patch(self, request, user_id):
        user = activate_user(
            target_user_id=user_id,
            performed_by=request.user
        )

        serializer = AdminUserStatusSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)



class AdminUserDetailView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request, user_id):
        data = get_user_with_activity(user_id)

        if not data:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        user = data["user"]
        stats = data["stats"]

        serializer = AdminUserDetailSerializer(
            user,
            context={"activity": stats}
        )

        return Response(serializer.data, status=status.HTTP_200_OK)