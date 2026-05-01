from django.core.cache import cache
from django.db import transaction




def hide_review(review):
    with transaction.atomic():
        review.is_hidden = True
        review.save(update_fields=["is_hidden"])
        

        cache.delete_many([
            f"profile:{review.user_id}",      
            f"user_reviews:{review.user_id}",
            f"review_detail:{review.id}",
        ])
   
        if hasattr(review, 'target_user_id') and review.target_user_id:
            cache.delete(f"profile:{review.target_user_id}")

def unhide_review(review):
    with transaction.atomic():
        review.is_hidden = False
        review.save(update_fields=["is_hidden"])
        
        cache.delete_many([
            f"profile:{review.user_id}",
            f"user_reviews:{review.user_id}",
            f"review_detail:{review.id}",
        ])
        
        if hasattr(review, 'target_user_id') and review.target_user_id:
            cache.delete(f"profile:{review.target_user_id}")


def mark_spoiler(review):
    with transaction.atomic():
        review.is_spoiler = True
        review.is_spoiler_overridden = True
        review.has_spoiler = True  
        review.save(update_fields=[
            "is_spoiler", 
            "is_spoiler_overridden", 
            "has_spoiler"
        ])

        cache.delete_many([
            f"profile:{review.user_id}",    
            f"user_reviews:{review.user_id}",
            f"review_detail:{review.id}",
        ])



def unmark_spoiler(review):
    with transaction.atomic():
        review.is_spoiler = False
        review.is_spoiler_overridden = True
        review.has_spoiler = False 
        review.spoiler_confidence = 0.0
        review.save(update_fields=[
            "is_spoiler", 
            "is_spoiler_overridden", 
            "has_spoiler",
            "spoiler_confidence"
        ])
        

        cache.delete_many([
            f"profile:{review.user_id}",    
            f"user_reviews:{review.user_id}",
            f"review_detail:{review.id}",
        ])



def delete_review(review):
    user_id = review.user_id
    target_user_id = getattr(review, 'target_user_id', None)
    review_id = review.id
    
    with transaction.atomic():
        review.delete()
        
        cache_keys = [
            f"profile:{user_id}",
            f"user_reviews:{user_id}",
            f"review_detail:{review_id}",
        ]
        
        if target_user_id:
            cache_keys.append(f"profile:{target_user_id}")
        
        cache.delete_many(cache_keys)
    
    return True