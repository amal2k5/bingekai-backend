from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from celery.result import AsyncResult
from ai.models import Recommendation
from ai.tasks import get_recommendations_task
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_user_activity(request):
    try:
        user = request.user
        from ratings.models import Rating
        from reviews.models import Review
        from watchlists.models import CollectionItem

        has_activity = any([
            Rating.objects.filter(user=user).exists(),
            Review.objects.filter(user=user).exists(),
            CollectionItem.objects.filter(collection__user=user).exists(),
        ])

        return Response({"has_activity": has_activity, "user_id": user.id})

    except Exception as e:
        logger.error(f"Failed to check activity: {e}")
        return Response({"has_activity": False, "error": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_recommendations(request):
    try:
        logger.info(f"Trigger request from user {request.user.id}")
        task = get_recommendations_task.delay(request.user.id)
        logger.info(f"Task ID: {task.id}")

        return Response({
            "status": "processing",
            "task_id": task.id,
            "message": "Generating recommendations in background"
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"Failed to trigger task: {e}", exc_info=True)
        return Response({"status": "error", "message": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_status(request, task_id):
    try:
        # ✅ Check DB first — if results saved, return SUCCESS immediately
        rec = Recommendation.objects.filter(user=request.user).first()
        if rec and rec.data and rec.data.get('movies'):
            data = rec.data
            return Response({
                "task_id": task_id,
                "status": "SUCCESS",
                "result": {
                    "movies": data.get("movies", []),
                    "method": data.get("method", "unknown"),
                    "ratings_count": data.get("ratings_count", 0),
                    "candidates_count": data.get("candidates_count", 0),
                    "confidence": data.get("confidence", 0.0),
                }
            })

        # Check Celery task state
        task_result = AsyncResult(task_id)

        if task_result.status == "PENDING":
            return Response({"task_id": task_id, "status": "PENDING"})

        elif task_result.status == "FAILURE":
            error_msg = str(task_result.result) if task_result.result else "Unknown error"
            logger.error(f"Task {task_id} failed: {error_msg}")
            return Response({
                "task_id": task_id,
                "status": "FAILURE",
                "error": error_msg,
            })

        elif task_result.status == "SUCCESS":
            result_value = task_result.result
            if isinstance(result_value, dict):
                return Response({
                    "task_id": task_id,
                    "status": "SUCCESS",
                    "result": {
                        "movies": result_value.get("movies", []),
                        "method": result_value.get("method", "unknown"),
                        "ratings_count": result_value.get("ratings_count", 0),
                        "candidates_count": result_value.get("candidates_count", 0),
                        "confidence": result_value.get("confidence", 0.0),
                    }
                })
            else:
                return Response({"task_id": task_id, "status": "SUCCESS",
                                 "result": {"movies": [], "method": "unknown"}})
        else:
            return Response({"task_id": task_id, "status": task_result.status})

    except Exception as e:
        logger.error(f"Status check error: {e}")
        return Response({"task_id": task_id, "status": "ERROR", "error": str(e)},
                        status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_saved_recommendations(request):
    try:
        user = request.user
        logger.info(f"Fetching saved recommendations for user {user.id}")

        rec = Recommendation.objects.filter(user=user).first()

        if not rec:
            logger.warning(f"No recommendations found for user {user.id}")
            return Response({
                "status": "ok",
                "type": "pending",
                "movies": [],
                "method": "pending_generation"
            })

        data = rec.data or {}
        method = data.get("method", "unknown")

        return Response({
            "status": "ok",
            "type": "personalized",
            "movies": data.get("movies", []),
            "method": method,
            "ratings_count": data.get("ratings_count", 0),
            "candidates_count": data.get("candidates_count", 0),
            "confidence": data.get("confidence", 0.0),
        })

    except Exception as e:
        logger.error(f"Failed to fetch recommendations: {e}", exc_info=True)
        return Response({"status": "error", "message": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invalidate_cache(request):
    try:
        Recommendation.objects.filter(user=request.user).delete()
        return Response({"status": "success",
                         "message": f"Cache cleared for user {request.user.id}"})
    except Exception as e:
        logger.error(f"Cache invalidation failed: {e}")
        return Response({"status": "error", "message": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)