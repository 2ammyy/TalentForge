# talentForge/posts/models_ai.py
from django.db import models
from django.contrib.auth.models import User

class CreativeCategory(models.Model):
    """Dynamic creative categories for AI validation"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    keywords = models.TextField(help_text="Comma-separated keywords for this category")
    is_active = models.BooleanField(default=True)
    weight = models.FloatField(default=1.0, help_text="Importance weight for validation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Creative Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def keyword_list(self):
        """Convert comma-separated keywords to list"""
        if self.keywords:
            return [k.strip().lower() for k in self.keywords.split(',') if k.strip()]
        return []


class ContentValidationLog(models.Model):
    """Log of content validations"""
    POST_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('job', 'Job Offer'),
    ]
    
    post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True, related_name='validation_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content_type = models.CharField(max_length=20, choices=POST_TYPES)
    score = models.FloatField()
    is_approved = models.BooleanField(default=False)
    detected_categories = models.JSONField(default=list)
    suggestions = models.JSONField(default=list)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Content Validation Log"
        verbose_name_plural = "Content Validation Logs"
    
    def __str__(self):
        return f"Validation {self.id} - Score: {self.score:.2f}"