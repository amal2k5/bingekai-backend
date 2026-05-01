from .growth_service import get_growth_metrics
from .engagement_service import get_engagement_metrics
from .activity_service import get_activity_trend
from .trending_service import get_trending_movies
from .insights_service import *
from .content_service import get_content_quality_metrics



def get_admin_dashboard(days=None, start_date=None, end_date=None):
    return {
        "time_range": "custom" if start_date else f"{days}_days",

        "growth": get_growth_metrics(
            days=days,
            start_date=start_date,
            end_date=end_date
        ),

        "engagement": get_engagement_metrics(
            days=days,
            start_date=start_date,
            end_date=end_date
        ),

        "activity": get_activity_trend(
            days=days,
            start_date=start_date,
            end_date=end_date
        ),

        "trending_movies": get_trending_movies(
            days=days,
            start_date=start_date,
            end_date=end_date
        ),

        "content_quality": get_content_quality_metrics(  
            start_date=start_date,
            end_date=end_date
        ),

        "insights": {                                     
            "most_followed_users": get_most_followed_users(),
            "most_liked_users": get_most_liked_users(),
        },
    }