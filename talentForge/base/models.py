from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os
import shutil

<<<<<<< HEAD

=======
>>>>>>> main
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    profile_picture_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def get_profile_picture(self):
        # If user has an uploaded profile picture
        if self.profile_picture:
            return self.profile_picture.url
        
        # If user has a profile picture URL
        if self.profile_picture_url:
            return self.profile_picture_url
        
        # If no photo is set, use generated avatar
        return f'https://ui-avatars.com/api/?name={self.user.username}&background=007bff&color=fff&size=150&bold=true'

    def has_custom_photo(self):
        """Check if user has either uploaded photo or URL photo"""
        return bool(self.profile_picture or self.profile_picture_url)


# Signal to delete profile files when UserProfile is deleted
@receiver(post_delete, sender=UserProfile)
def delete_profile_files(sender, instance, **kwargs):
    """Delete profile picture files when UserProfile is deleted"""
    if instance.profile_picture:
        if os.path.isfile(instance.profile_picture.path):
            os.remove(instance.profile_picture.path)

# Signal to handle user deletion
@receiver(post_delete, sender=User)
def delete_user_files(sender, instance, **kwargs):
    """Delete user-related files when User is deleted"""
    # Delete user's profile pictures folder
    user_media_path = f"media/profile_pictures/{instance.username}"
    if os.path.exists(user_media_path):
        shutil.rmtree(user_media_path)