# creator/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class CreatorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='creatorprofile')
    is_verified = models.BooleanField(default=False)
    followers_count = models.IntegerField(default=0)
    total_posts = models.IntegerField(default=0)
    total_likes = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)
    engagement_rate = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    username = models.CharField(max_length=150, blank=True)
    email = models.EmailField(blank=True)
        
    def sync_with_user_profile(self):
        """Sync follower count with Follow model"""
        try:
            from posts.models import Follow
            
            # Debug: Print what we're querying
            print(f"DEBUG: Syncing for user: {self.user.username}")
            print(f"DEBUG: Query: Follow.objects.filter(following={self.user.id})")
            
            # Get the count
            count = Follow.objects.filter(following=self.user).count()
            print(f"DEBUG: Found {count} followers")
            
            # Update and save
            self.followers_count = count
            self.save()
            
            return self.followers_count
            
        except ImportError as e:
            print(f"ERROR: Could not import Follow model: {e}")
            self.followers_count = 0
            self.save()
            return 0
        except Exception as e:
            print(f"ERROR in sync_with_user_profile: {e}")
            import traceback
            traceback.print_exc()
            self.followers_count = 0
            self.save()
            return 0
    
    def upgrade_to_creator(self):
        """Upgrade user to verified creator"""
        if self.followers_count >= 1:
            self.is_verified = True
            self.save()
            return True
        return False
    
    def __str__(self):
        return f"CreatorProfile for {self.user.username}"


# @receiver(post_save, sender=User)
# def create_or_update_creator_profile(sender, instance, created, **kwargs):
#     if created:
#         CreatorProfile.objects.create(user=instance)
#     else:
#         instance.creatorprofile.save()  

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import CreatorProfile

@receiver(post_save, sender=User)
def create_or_update_creator_profile(sender, instance, created, **kwargs):
    """
    Crée ou met à jour un profil créateur seulement si l'utilisateur est marqué comme créateur.
    """
    if created:
        # Si l'utilisateur est créé avec le flag is_creator=True, créez un profil
        if instance.is_creator:
            CreatorProfile.objects.create(
                user=instance,
                username=instance.username,
                email=instance.email
            )
    else:
        # Pour les mises à jour, gérez seulement si le profil existe
        try:
            if hasattr(instance, 'creatorprofile'):
                creator_profile = instance.creatorprofile
                # Met à jour les informations si elles ont changé
                if creator_profile.username != instance.username:
                    creator_profile.username = instance.username
                if creator_profile.email != instance.email:
                    creator_profile.email = instance.email
                creator_profile.save()
        except CreatorProfile.DoesNotExist:
            # Si l'utilisateur devient un créateur plus tard
            if instance.is_creator:
                CreatorProfile.objects.create(
                    user=instance,
                    username=instance.username,
                    email=instance.email
                )

class CreatorStat(models.Model):
    creator = models.ForeignKey(CreatorProfile, on_delete=models.CASCADE, related_name='stats')
    date = models.DateField(default=timezone.now)
    followers = models.IntegerField(default=0)
    posts = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    reach = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.creator.user.username} - {self.date}"

# Nous ajouterons Collaboration et AdCampaign plus tard
# class Collaboration(models.Model):
#     COLLAB_STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('accepted', 'Accepted'),
#         ('rejected', 'Rejected'),
#         ('completed', 'Completed'),
#     ]
#     
#     creator = models.ForeignKey(CreatorProfile, on_delete=models.CASCADE, related_name='collaborations_sent')
#     collaborator = models.ForeignKey(CreatorProfile, on_delete=models.CASCADE, related_name='collaborations_received')
#     title = models.CharField(max_length=200)
#     description = models.TextField()
#     status = models.CharField(max_length=20, choices=COLLAB_STATUS_CHOICES, default='pending')
#     budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     
#     def __str__(self):
#         return f"{self.title} - {self.creator.user.username}"

# class AdCampaign(models.Model):
#     creator = models.ForeignKey(CreatorProfile, on_delete=models.CASCADE, related_name='ad_campaigns')
#     title = models.CharField(max_length=200)
#     description = models.TextField()
#     budget = models.DecimalField(max_digits=10, decimal_places=2)
#     target_audience = models.JSONField(default=dict)
#     start_date = models.DateTimeField()
#     end_date = models.DateTimeField()
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     
#     def __str__(self):
#         return f"{self.title} - {self.creator.user.username}"

# Signals pour créer automatiquement le profil creator
@receiver(post_save, sender=User)
def create_creator_profile(sender, instance, created, **kwargs):
    if created:
        CreatorProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_creator_profile(sender, instance, **kwargs):
    if hasattr(instance, 'creator_profile'):
        instance.creator_profile.save()