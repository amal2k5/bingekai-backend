from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()




class FollowManager(models.Manager):
    
    def get_followers(self, user):
        return self.filter(following=user, is_accepted=True).select_related('follower')
    
    def get_following(self, user):
        return self.filter(follower=user, is_accepted=True).select_related('following')
    
    def get_pending_requests(self, user):
        return self.filter(following=user, is_accepted=False).select_related('follower')
    
    def get_sent_requests(self, user):
        return self.filter(follower=user, is_accepted=False).select_related('following')
    
    def are_connected(self, user1, user2):
        return self.filter(
            models.Q(follower=user1, following=user2, is_accepted=True) |
            models.Q(follower=user2, following=user1, is_accepted=True)
        ).exists()



class Follow(models.Model):
    
    follower = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="following_set"  
    )
    following = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followers_set" 
    )
    is_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 

    objects = FollowManager()

    class Meta:
        unique_together = ("follower", "following")
        indexes = [
            models.Index(fields=["follower", "is_accepted"]),  
            models.Index(fields=["following", "is_accepted"]),  
            models.Index(fields=["is_accepted", "created_at"]),  
            models.Index(fields=["created_at"]),
            models.Index(fields=["follower", "is_accepted", "created_at"]),
            models.Index(fields=["following", "is_accepted", "created_at"]),
        ]
        ordering = ['-created_at']  

    def clean(self):
        if self.follower == self.following:
            raise ValidationError("Users cannot follow themselves")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def accept(self):
        self.is_accepted = True
        self.save(update_fields=['is_accepted', 'updated_at'])

    def decline(self):
        self.delete()

    @property
    def status(self):
        return "Accepted" if self.is_accepted else "Pending"

    def __str__(self):
        return f"{self.follower.username} -> {self.following.username} ({self.status})"



class UserSocialMixin:
    
    @property
    def followers_count(self):
        return Follow.objects.filter(following=self, is_accepted=True).count()
    
    @property
    def following_count(self):
        return Follow.objects.filter(follower=self, is_accepted=True).count()
    
    @property
    def pending_requests_count(self):
        return Follow.objects.filter(following=self, is_accepted=False).count()
    
    def get_followers(self):
        return Follow.objects.get_followers(self)
    
    def get_following(self):
        return Follow.objects.get_following(self)
    
    def get_pending_requests(self):
        return Follow.objects.get_pending_requests(self)
    
    def is_following(self, user):
        return Follow.objects.filter(
            follower=self, 
            following=user, 
            is_accepted=True
        ).exists()
    
    def is_followed_by(self, user):
        return Follow.objects.filter(
            follower=user, 
            following=self, 
            is_accepted=True
        ).exists()