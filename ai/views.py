from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from celery.result import AsyncResult
from ai.models import Recommendation
from .tasks import get_recommendations_task
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_recommendations(request):
    try:
        logger.info(f"📥 Recommendation trigger request from user {request.user.id}")
        
        task = get_recommendations_task.delay(request.user.id)
        logger.info(f"   Task ID: {task.id}")

        return Response({
            "status": "processing",
            "task_id": task.id,
            "message": "Generating recommendations in background"
        }, status=status.HTTP_202_ACCEPTED)

    except Exception as e:
        logger.error(f"❌ Failed to trigger task: {e}", exc_info=True)
        return Response({
            "status": "error",
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_status(request, task_id):
    try:
        task_result = AsyncResult(task_id)
        logger.debug(f"Checking task status: {task_id} - {task_result.status}")
        
        # Handle different task states
        if task_result.status == "PENDING":
            return Response({
                "task_id": task_id,
                "status": "PENDING",
            })
        
        elif task_result.status == "FAILURE":
            error_msg = str(task_result.result) if task_result.result else "Unknown error"
            logger.error(f"   Task {task_id} failed: {error_msg}")
            
            # ✅ Return consistent format that frontend expects
            return Response({
                "task_id": task_id,
                "status": "FAILURE",
                "error": error_msg,
                "result": {  # Add result field to match frontend expectation
                    "movies": [],
                    "method": "error",
                    "error": error_msg
                }
            })
        
        elif task_result.status == "SUCCESS":
            result = task_result.result
            logger.info(f"   Task {task_id} completed successfully")
            
            # ✅ Format the result properly for frontend
            if isinstance(result, dict):
                # Ensure it has the expected structure
                formatted_result = {
                    "movies": result.get("movies", []),
                    "method": result.get("method", "unknown"),
                    "ratings_count": result.get("ratings_count", 0),
                    "candidates_count": result.get("candidates_count", 0),
                    "confidence": result.get("confidence", 0.0),
                }
            else:
                # If result is something else (like tuple), convert it
                logger.warning(f"Unexpected result type: {type(result)}")
                formatted_result = {
                    "movies": [],
                    "method": "unknown",
                    "error": f"Invalid result type: {type(result)}"
                }
            
            return Response({
                "task_id": task_id,
                "status": "SUCCESS",
                "result": formatted_result
            })
        
        else:
            # RUNNING, STARTED, RETRY, etc.
            return Response({
                "task_id": task_id,
                "status": task_result.status,
            })
    
    except Exception as e:
        logger.error(f"❌ Failed to get task status: {e}", exc_info=True)
        return Response({
            "task_id": task_id,
            "status": "ERROR",
            "error": str(e),
            "result": {
                "movies": [],
                "method": "error",
                "error": str(e)
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_recommendations(request):
    try:
        logger.info(f"Fetching recommendations for user {request.user.id}")
        
        rec = Recommendation.objects.filter(user=request.user).first()

        if not rec:
            logger.warning(f"   No recommendations found for user {request.user.id}")
            return Response({
                "status": "pending",
                "type": "pending",
                "movies": [],
                "message": "No recommendations generated yet"
            })

        data = rec.data or {}

        # ✅ Return consistent format that frontend expects
        response_data = {
            "status": "ok",
            "type": data.get("method", "unknown"),
            "movies": data.get("movies", []),
            "method": data.get("method", "unknown"),
            "ratings_count": data.get("ratings_count", 0),
            "candidates_count": data.get("candidates_count", 0),
            "confidence": data.get("confidence", 0.0),
        }
        
        # For trending fallback, frontend expects this format
        if data.get("method") == "trending_fallback":
            response_data["type"] = "trending"
            response_data["movies"] = data.get("movies", [])
        
        logger.info(f"   Found {len(response_data.get('movies', []))} recommendations")
        
        return Response(response_data)

    except Exception as e:
        logger.error(f"❌ Failed to fetch recommendations: {e}", exc_info=True)
        return Response({
            "status": "error",
            "type": "error",
            "movies": [],
            "message": str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)