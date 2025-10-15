from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    profile_picture_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    #  field for delete profile picture
    remove_profile_picture = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def get_profile_picture(self):
        # If the user requested deletion OR has no photo
        if self.remove_profile_picture or not self.profile_picture:
            if self.profile_picture_url:
                return self.profile_picture_url
            else:
                # Automatically generated avatar
                return f'https://ui-avatars.com/api/?name={self.user.username}&background=007bff&color=fff&size=150&bold=true'
        return self.profile_picture.url

    def save(self, *args, **kwargs):
        # If remove_profile_picture is True, delete the photo
        if self.remove_profile_picture and self.profile_picture:
            self.profile_picture.delete(save=False)
            self.profile_picture = None
            self.remove_profile_picture = False  # Reset the flag
        super().save(*args, **kwargs)