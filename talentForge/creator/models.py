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

# SIGNAL UNIQUE ET CORRIGÉ - UTILISE get_or_create() POUR ÉVITER LES DOUBLONS
@receiver(post_save, sender=User)
def handle_user_save(sender, instance, created, **kwargs):
    """
    Gère la création/mise à jour du profil créateur pour TOUS les utilisateurs.
    Utilise get_or_create pour éviter les doublons.
    """
    # Utilise get_or_create au lieu de create() pour éviter les erreurs de doublon
    profile, profile_created = CreatorProfile.objects.get_or_create(
        user=instance,
        defaults={
            'username': instance.username,
            'email': instance.email
        }
    )
    
    # Met à jour les informations si le profil existait déjà
    if not profile_created:
        profile.username = instance.username
        profile.email = instance.email
        profile.save()