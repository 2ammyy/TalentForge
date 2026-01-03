# /app/posts/templatetags/post_tags.py
from django import template
from posts.models import SavedPost
from django.contrib.auth.models import User

register = template.Library()

@register.filter
def is_saved(post, user):
    """Check if a post is saved by a user"""
    if not user.is_authenticated:
        return False
    return SavedPost.objects.filter(user=user, post=post).exists()

@register.filter
def get_user_saved_posts(user):
    """Get all saved posts for a user"""
    if not user.is_authenticated:
        return []
    return SavedPost.objects.filter(user=user).select_related('post')

@register.filter
def get_following_count(user):
    """Get following count for a user"""
    return user.user_following.count()

@register.filter
def get_followers_count(user):
    """Get followers count for a user"""
    return user.user_followers.count()

@register.simple_tag
def get_saved_posts_count(user):
    """Get saved posts count for a user"""
    if not user.is_authenticated:
        return 0
    return SavedPost.objects.filter(user=user).count()

@register.filter
def is_following(user, target_user):
    """Check if user is following target_user"""
    if not user.is_authenticated:
        return False
    return user.user_following.filter(following=target_user).exists()

@register.filter
def is_blocked(user, target_user):
    """Check if user has blocked target_user"""
    if not user.is_authenticated:
        return False
    return user.user_blocking.filter(blocked=target_user).exists()