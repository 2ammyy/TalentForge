# creator/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class CreatorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='creator_profile')
    is_verified = models.BooleanField(default=False)
    verified_date = models.DateTimeField(null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    website = models.URLField(blank=True)
    join_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Creator: {self.user.username}"
    
    @property
    def followers_count(self):
        """Nombre réel de followers"""
        try:
            from django.apps import apps
            if apps.is_installed('users'):
                # Essayez d'importer le modèle Follow si il existe
                Follow = apps.get_model('users', 'Follow')
                return Follow.objects.filter(followed=self.user).count()
        except LookupError:
            pass
        
        # Fallback - pour l'instant, retourner 1 pour tester
        return 1
    
    @property
    def total_posts(self):
        """Nombre réel de posts"""
        try:
            from django.apps import apps
            if apps.is_installed('posts'):
                Post = apps.get_model('posts', 'Post')
                return Post.objects.filter(author=self.user).count()
        except LookupError:
            pass
        return 0
    
    @property
    def total_likes(self):
        """Nombre total de likes sur les posts"""
        try:
            from django.apps import apps
            if apps.is_installed('posts'):
                Post = apps.get_model('posts', 'Post')
                posts = Post.objects.filter(author=self.user)
                return sum(post.likes_count for post in posts if hasattr(post, 'likes_count'))
        except LookupError:
            pass
        return 0
    
    @property
    def total_comments(self):
        """Nombre total de commentaires sur les posts"""
        try:
            from django.apps import apps
            if apps.is_installed('posts'):
                Post = apps.get_model('posts', 'Post')
                posts = Post.objects.filter(author=self.user)
                return sum(post.comments_count for post in posts if hasattr(post, 'comments_count'))
        except LookupError:
            pass
        return 0
    
    @property
    def engagement_rate(self):
        """Taux d'engagement réel"""
        if self.followers_count > 0:
            total_engagements = self.total_likes + self.total_comments
            return (total_engagements / self.followers_count) * 100
        return 0
    
    def upgrade_to_creator(self):
        """Mettre à niveau en créateur"""
        if self.followers_count >= 1:  # 1 seul follower suffit
            self.is_verified = True
            self.verified_date = timezone.now()
            self.save()
            return True
        return False

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