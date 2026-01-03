# Create: talentForge/posts/views_mentions.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.db.models import Q
from django.contrib.auth.models import User
from .models import Block
from django.conf import settings

@login_required
@require_GET
def search_usernames(request):
    """API endpoint for username search (for @mentions)"""
    query = request.GET.get('q', '').strip()
    
    if not query or len(query) < 1:
        return JsonResponse({'results': []})
    
    # Exclude blocked users
    blocked_users = Block.objects.filter(blocker=request.user).values_list('blocked_id', flat=True)
    
    # Search users (excluding blocked and current user)
    users = User.objects.filter(
        Q(username__icontains=query) |
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query)
    ).exclude(
        Q(id__in=blocked_users) |
        Q(id=request.user.id)
    ).select_related('posts_profile')[:10]
    
    results = []
    for user in users:
        avatar_url = None
        if hasattr(user, 'posts_profile') and user.posts_profile.profile_picture:
            avatar_url = user.posts_profile.profile_picture.url
        
        results.append({
            'id': user.id,
            'username': user.username,
            'full_name': f"{user.first_name} {user.last_name}".strip() or user.username,
            'avatar_url': avatar_url,
            'initials': user.username[0].upper() if user.username else '?'
        })
    
    return JsonResponse({'results': results})