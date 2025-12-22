from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from .models import ContentValidationLog, CreativeCategory
from django.db.models import Count, Avg, Q
from datetime import datetime, timedelta

@login_required
@user_passes_test(lambda u: u.is_staff)
def validation_analytics(request):
    """Admin dashboard for content validation analytics"""
    
    # Time ranges
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Overall statistics
    total_validations = ContentValidationLog.objects.count()
    approval_rate = ContentValidationLog.objects.filter(is_approved=True).count() / max(total_validations, 1)
    
    # Time-based statistics
    recent_validations = ContentValidationLog.objects.filter(
        created_at__gte=week_ago
    )
    
    # Category performance
    category_stats = []
    for post in Post.objects.all():
        if hasattr(post, 'validation_result') and post.validation_result:
            categories = post.validation_result.get('detected_categories', [])
            for cat in categories:
                category_stats.append(cat)
    
    from collections import Counter
    category_counts = Counter(category_stats)
    
    # User statistics
    user_stats = User.objects.annotate(
        post_count=Count('posts'),
        avg_score=Avg('posts__contentvalidationlog__score')
    ).filter(post_count__gt=0).order_by('-avg_score')[:10]
    
    context = {
        'total_validations': total_validations,
        'approval_rate': approval_rate * 100,
        'recent_validations': recent_validations,
        'category_counts': dict(category_counts.most_common(10)),
        'user_stats': user_stats,
        'today': today,
    }
    
    return render(request, 'admin/validation_analytics.html', context)