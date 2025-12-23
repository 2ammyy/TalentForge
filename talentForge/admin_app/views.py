from django.shortcuts import render, get_object_or_404, redirect, Http404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Q, Avg, OuterRef, Subquery
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import csv
import json
from django.utils import timezone
from datetime import datetime, timedelta

from .permissions import admin_required


@login_required
@admin_required
def admin_dashboard(request):
    """Main admin dashboard"""
    from datetime import datetime, timedelta
    
    # Get duration parameter
    duration = request.GET.get('duration', 'week')
    if duration == 'month':
        days = 30
        date_format = '%m/%d'
    elif duration == 'quarter':
        days = 90
        date_format = '%m/%d'
    else:  # week
        days = 7
        date_format = '%a'
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Basic statistics
    stats = {
        'total_users': User.objects.count(),
        'new_users_today': User.objects.filter(date_joined__date=today).count(),
        'new_users_week': User.objects.filter(date_joined__gte=week_ago).count(),
        'new_users_month': User.objects.filter(date_joined__gte=month_ago).count(),
        'active_users': User.objects.filter(last_login__gte=week_ago).count(),
    }
    
    # Try to get creator stats if creator app exists
    try:
        from creator.models import CreatorProfile
        stats['total_creators'] = CreatorProfile.objects.filter(is_verified=True).count()
        stats['pending_creators'] = CreatorProfile.objects.filter(is_verified=False).count()
    except:
        stats['total_creators'] = 0
        stats['pending_creators'] = 0
    
    # Try to get post stats if posts app exists
    try:
        from posts.models import Post
        stats['total_posts'] = Post.objects.count()
        stats['posts_today'] = Post.objects.filter(created_at__date=today).count()
        stats['posts_week'] = Post.objects.filter(created_at__gte=week_ago).count()
    except:
        stats['total_posts'] = 0
        stats['posts_today'] = 0
        stats['posts_week'] = 0
    
    # Recent users
    recent_users = User.objects.order_by('-date_joined')[:10]
    
    # Daily signups for chart
    daily_signups = []
    for i in range(days-1, -1, -1):
        day = today - timedelta(days=i)
        count = User.objects.filter(date_joined__date=day).count()
        daily_signups.append({
            'day': day.strftime(date_format),
            'date': day.strftime('%m/%d'),
            'count': count
        })
    
    # Get weekly activity for quick stats
    weekly_activity = {
        'new_posts': stats['posts_week'],
        'new_creators': stats['pending_creators'],
        'active_creators': CreatorProfile.objects.filter(
            updated_at__gte=week_ago
        ).count() if 'creator' in locals() else 0,
    }
    
    # Get pending items
    pending_items = {
        'reports': 0,
        'posts': 0,
    }
    try:
        from posts.models import Report
        pending_items['reports'] = Report.objects.filter(status='pending').count()
        pending_items['posts'] = Post.objects.filter(validation_logs__isnull=True).count()
    except:
        pass
    
    context = {
        'stats': stats,
        'recent_users': recent_users,
        'daily_signups': daily_signups,
        'weekly_activity': weekly_activity,
        'pending_items': pending_items,
        'duration': duration,
        'date_format': date_format,
        'days': days,
        'active_page': 'dashboard',
    }
    
    return render(request, 'admin_app/dashboard.html', context)

@login_required
@admin_required
def user_management(request):
    """User management page"""
    users = User.objects.all()
    
    # Filters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    if status_filter == 'active':
        users = users.filter(is_active=True)
    elif status_filter == 'inactive':
        users = users.filter(is_active=False)
    elif status_filter == 'staff':
        users = users.filter(is_staff=True)
    elif status_filter == 'superuser':
        users = users.filter(is_superuser=True)
    
    # Sort and paginate
    users = users.order_by('-date_joined')
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'users': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'active_page': 'users',
    }
    
    return render(request, 'admin_app/users.html', context)

@login_required
@admin_required
def user_detail(request, user_id):
    """User detail view"""
    user = get_object_or_404(User, id=user_id)
    
    # Try to get user posts
    user_posts = []
    try:
        from posts.models import Post
        user_posts = Post.objects.filter(author=user).order_by('-created_at')[:10]
    except:
        pass
    
    # Check if user has creator profile
    creator_profile = None
    try:
        creator_profile = user.creatorprofile
    except:
        pass
    
    context = {
        'user': user,
        'user_posts': user_posts,
        'creator_profile': creator_profile,
        'active_page': 'users',
    }
    
    return render(request, 'admin_app/user_detail.html', context)

@login_required
@admin_required
def toggle_user_active(request, user_id):
    """Toggle user active status"""
    user = get_object_or_404(User, id=user_id)
    user.is_active = not user.is_active
    user.save()
    
    messages.success(request, f'✅ User {user.username} has been {"activated" if user.is_active else "deactivated"}.')
    return redirect('admin_app:user_detail', user_id=user_id)

@login_required
@admin_required
def make_user_staff(request, user_id):
    """Make user a staff member"""
    user = get_object_or_404(User, id=user_id)
    user.is_staff = True
    user.save()
    
    messages.success(request, f'✅ User {user.username} is now a staff member.')
    return redirect('admin_app:user_detail', user_id=user_id)

@login_required
@admin_required
def placeholder_page(request, page_name):
    """Placeholder for features not yet implemented"""
    page_titles = {
        'creators': 'Creator Management',
        'moderation': 'Content Moderation',
        'analytics': 'Analytics Dashboard',
        'reports': 'Reports',
        'settings': 'Settings',
    }
    
    context = {
        'active_page': page_name,
        'page_title': page_titles.get(page_name, page_name.title()),
    }
    
    return render(request, 'admin_app/placeholder.html', context)

@login_required
@admin_required
def api_stats(request):
    """API for real-time stats"""
    today = timezone.now().date()
    
    stats = {
        'total_users': User.objects.count(),
        'new_users_today': User.objects.filter(date_joined__date=today).count(),
        'active_today': User.objects.filter(last_login__date=today).count(),
    }
    
    return JsonResponse(stats)

@login_required
@admin_required
def export_users_csv(request):
    """Export users to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="talentforge_users.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['ID', 'Username', 'Email', 'First Name', 'Last Name', 'Date Joined', 'Last Login', 'Active', 'Staff', 'Superuser'])
    
    users = User.objects.all()
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            user.first_name,
            user.last_name,
            user.date_joined.strftime('%Y-%m-%d %H:%M'),
            user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else '',
            user.is_active,
            user.is_staff,
            user.is_superuser
        ])
    
    return response


@login_required
@admin_required
def creator_management(request):
    """Creator management page"""
    try:
        from creator.models import CreatorProfile
        creators = CreatorProfile.objects.select_related('user').all()
        
        # Filters
        search_query = request.GET.get('search', '')
        status_filter = request.GET.get('status', 'all')
        
        if search_query:
            creators = creators.filter(
                Q(user__username__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(username__icontains=search_query)
            )
        
        if status_filter == 'verified':
            creators = creators.filter(is_verified=True)
        elif status_filter == 'pending':
            creators = creators.filter(is_verified=False)
        elif status_filter == 'featured':
            # Since there's no is_featured field, we can't filter by it
            creators = creators.none()  # Return empty if filtering by featured
        
        # Sort and paginate
        creators = creators.order_by('-created_at')
        paginator = Paginator(creators, 25)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)
        
        # Stats - REMOVE is_featured since it doesn't exist
        stats = {
            'total': CreatorProfile.objects.count(),
            'verified': CreatorProfile.objects.filter(is_verified=True).count(),
            'pending': CreatorProfile.objects.filter(is_verified=False).count(),
            'featured': 0,  # Set to 0 since there's no is_featured field
        }
        
    except ImportError:
        page_obj = []
        stats = {}
        messages.warning(request, "Creator app not installed")
    
    context = {
        'creators': page_obj,
        'stats': stats,
        'search_query': search_query,
        'status_filter': status_filter,
        'active_page': 'creators',
    }
    
    return render(request, 'admin_app/creators.html', context)

@login_required
@admin_required
def creator_detail(request, creator_id):
    """Creator detail view"""
    try:
        from creator.models import CreatorProfile
        creator = get_object_or_404(CreatorProfile.objects.select_related('user'), id=creator_id)
        
        # Get creator's posts
        from posts.models import Post
        creator_posts = Post.objects.filter(author=creator.user).order_by('-created_at')[:20]
        
        # Get stats - FIXED: Use reactions instead of ratings
        post_count = Post.objects.filter(author=creator.user).count()
        
        # Calculate average score from validation logs instead of ratings
        from posts.models import ContentValidationLog
        avg_score = ContentValidationLog.objects.filter(
            post__author=creator.user
        ).aggregate(Avg('score'))['score__avg'] or 0
        
        # Recent activity
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        recent_posts = Post.objects.filter(author=creator.user, created_at__gte=week_ago).count()
        
    except ImportError:
        raise Http404("Creator app not installed")
    
    context = {
        'creator': creator,
        'creator_posts': creator_posts,
        'post_count': post_count,
        'avg_rating': round(avg_score, 2),  # Renamed to avg_score for clarity
        'recent_posts': recent_posts,
        'active_page': 'creators',
    }
    
    return render(request, 'admin_app/creator_detail.html', context)
    """Creator detail view"""
    try:
        from creator.models import CreatorProfile
        creator = get_object_or_404(CreatorProfile.objects.select_related('user'), id=creator_id)
        
        # Get creator's posts
        from posts.models import Post
        creator_posts = Post.objects.filter(author=creator.user).order_by('-created_at')[:20]
        
        # Get stats
        post_count = Post.objects.filter(author=creator.user).count()
        avg_rating = creator_posts.aggregate(Avg('ratings__score'))['ratings__score__avg'] or 0
        
        # Recent activity
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        recent_posts = Post.objects.filter(author=creator.user, created_at__gte=week_ago).count()
        
    except ImportError:
        raise Http404("Creator app not installed")
    
    context = {
        'creator': creator,
        'creator_posts': creator_posts,
        'post_count': post_count,
        'avg_rating': round(avg_rating, 2),
        'recent_posts': recent_posts,
        'active_page': 'creators',
    }
    
    return render(request, 'admin_app/creator_detail.html', context)
@login_required
@admin_required
def verify_creator(request, creator_id):
    """Verify a creator"""
    try:
        from creator.models import CreatorProfile
        creator = get_object_or_404(CreatorProfile, id=creator_id)
        creator.is_verified = not creator.is_verified
        creator.save()
        
        status = "verified" if creator.is_verified else "unverified"
        messages.success(request, f'✅ Creator {creator.user.username} has been {status}.')
        
        # Send notification to creator
        from posts.models import Notification
        if creator.is_verified:
            Notification.objects.create(
                user=creator.user,
                from_user=request.user,
                notification_type='follow',  # Using follow as generic notification
                post=None
            )
        
    except ImportError:
        messages.error(request, "Creator app not installed")
    
    return redirect('admin_app:creator_detail', creator_id=creator_id)


@login_required
@admin_required
def creator_stats(request, creator_id):
    """Get creator statistics (API endpoint)"""
    try:
        from creator.models import CreatorProfile
        creator = get_object_or_404(CreatorProfile, id=creator_id)
        
        from posts.models import Post, Reaction, Comment
        from datetime import datetime, timedelta
        
        # Calculate stats
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        stats = {
            'total_posts': Post.objects.filter(author=creator.user).count(),
            'posts_week': Post.objects.filter(author=creator.user, created_at__date__gte=week_ago).count(),
            'posts_month': Post.objects.filter(author=creator.user, created_at__date__gte=month_ago).count(),
            'total_likes': Reaction.objects.filter(post__author=creator.user).count(),
            'total_comments': Comment.objects.filter(post__author=creator.user).count(),
            'engagement_rate': 0,  # Calculate based on followers and interactions
        }
        
        return JsonResponse(stats)
        
    except ImportError:
        return JsonResponse({'error': 'Creator app not installed'}, status=404)


@login_required
@admin_required
def content_moderation(request):
    """Content moderation dashboard"""
    try:
        from posts.models import Post, Report, ContentValidationLog
        
        # Get stats
        stats = {
            'total_posts': Post.objects.count(),
            'pending_moderation': Post.objects.filter(validation_logs__isnull=True).count(),
            'total_reports': Report.objects.filter(status='pending').count(),
            'low_quality': ContentValidationLog.objects.filter(score__lt=0.4).count(),
        }
        
        # Get recent reports
        recent_reports = Report.objects.select_related('post', 'reporter', 'reported_user').filter(
            status='pending'
        ).order_by('-created_at')[:10]
        
        # Get low quality posts
        low_quality_posts = ContentValidationLog.objects.select_related('post').filter(
            score__lt=0.4
        ).order_by('score')[:10]
        
    except Exception as e:
        stats = {}
        recent_reports = []
        low_quality_posts = []
        messages.warning(request, f"Error loading moderation data: {str(e)}")
    
    context = {
        'stats': stats,
        'recent_reports': recent_reports,
        'low_quality_posts': low_quality_posts,
        'active_page': 'moderation',
    }
    
    return render(request, 'admin_app/moderation.html', context)


@login_required
@admin_required
def post_moderation(request):
    """Post moderation list"""
    from posts.models import Post, ContentValidationLog
    from django.db.models import OuterRef, Subquery
    
    # Get posts with their latest validation score
    latest_validation = ContentValidationLog.objects.filter(
        post=OuterRef('pk')
    ).order_by('-created_at')
    
    posts = Post.objects.annotate(
        latest_score=Subquery(latest_validation.values('score')[:1]),
        is_approved=Subquery(latest_validation.values('is_approved')[:1]),
        validation_count=Count('validation_logs')
    ).select_related('author').order_by('-created_at')
    
    # Filters
    status_filter = request.GET.get('status', 'all')
    score_min = request.GET.get('score_min', '')
    score_max = request.GET.get('score_max', '')
    search = request.GET.get('search', '')
    
    if status_filter == 'approved':
        posts = posts.filter(is_approved=True)
    elif status_filter == 'rejected':
        posts = posts.filter(is_approved=False)
    elif status_filter == 'unvalidated':
        posts = posts.filter(validation_count=0)
    
    if score_min:
        try:
            posts = posts.filter(latest_score__gte=float(score_min))
        except ValueError:
            pass
    
    if score_max:
        try:
            posts = posts.filter(latest_score__lte=float(score_max))
        except ValueError:
            pass
    
    if search:
        posts = posts.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(author__username__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(posts, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'posts': page_obj,
        'active_page': 'moderation',
        'filters': {
            'status': status_filter,
            'score_min': score_min,
            'score_max': score_max,
            'search': search,
        }
    }
    
    return render(request, 'admin_app/post_moderation.html', context)


@login_required
@admin_required
def post_detail(request, post_id):
    """Post detail for moderation"""
    from posts.models import Post, Report, ContentValidationLog
    from django.db.models import Count
    
    post = get_object_or_404(
        Post.objects.select_related('author'), 
        id=post_id
    )
    
    # Get validation logs
    validation_logs = ContentValidationLog.objects.filter(
        post=post
    ).order_by('-created_at')
    
    # Get reports
    reports = Report.objects.filter(post=post).select_related('reporter')
    
    # Get latest validation
    latest_validation = validation_logs.first()
    
    # Get post statistics
    stats = {
        'likes': post.reactions.count(),
        'comments': post.comments.count(),
        'shares': post.shares.count(),
        'reports': reports.count(),
    }
    
    context = {
        'post': post,
        'validation_logs': validation_logs,
        'latest_validation': latest_validation,
        'reports': reports,
        'stats': stats,
        'active_page': 'moderation',
    }
    
    return render(request, 'admin_app/post_detail.html', context)


@login_required
@admin_required
def approve_post(request, post_id):
    """Approve a post"""
    from posts.models import Post, ContentValidationLog
    
    post = get_object_or_404(Post, id=post_id)
    
    # Create validation log
    ContentValidationLog.objects.create(
        post=post,
        user=request.user,
        content_type=post.type,
        score=0.8,  # Default score for manual approval
        is_approved=True,
        detected_categories=[],
        suggestions=[],
        notes=f"Manually approved by {request.user.username}"
    )
    
    messages.success(request, f'✅ Post "{post.title}" has been approved.')
    return redirect('admin_app:post_detail', post_id=post_id)


@login_required
@admin_required
def reject_post(request, post_id):
    """Reject a post"""
    from posts.models import Post, ContentValidationLog
    
    post = get_object_or_404(Post, id=post_id)
    
    # Create validation log
    ContentValidationLog.objects.create(
        post=post,
        user=request.user,
        content_type=post.type,
        score=0.3,  # Low score for rejection
        is_approved=False,
        detected_categories=[],
        suggestions=[],
        notes=f"Manually rejected by {request.user.username}"
    )
    
    messages.warning(request, f'⚠️ Post "{post.title}" has been rejected.')
    return redirect('admin_app:post_detail', post_id=post_id)


@login_required
@admin_required
def delete_post(request, post_id):
    """Delete a post"""
    from posts.models import Post
    
    post = get_object_or_404(Post, id=post_id)
    post_title = post.title or f"Post #{post.id}"
    post.delete()
    
    messages.success(request, f'🗑️ Post "{post_title}" has been deleted.')
    return redirect('admin_app:post_moderation')


@login_required
@admin_required
def reports_dashboard(request):
    """Reports dashboard"""
    from posts.models import Report
    from django.db.models import Count, Q
    from datetime import datetime, timedelta
    
    # Date ranges
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Overall stats
    total_reports = Report.objects.count()
    pending_reports = Report.objects.filter(status='pending').count()
    resolved_reports = Report.objects.filter(status='resolved').count()
    
    # Reports by type
    reports_by_type = Report.objects.values('reason').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Reports by status
    reports_by_status = Report.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Recent reports
    recent_reports = Report.objects.select_related(
        'post', 'reported_user', 'reporter'
    ).order_by('-created_at')[:10]
    
    # Weekly trend
    weekly_trend = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_reports = Report.objects.filter(created_at__date=day).count()
        weekly_trend.append({
            'day': day.strftime('%a'),
            'date': day.strftime('%m/%d'),
            'count': day_reports
        })
    
    context = {
        'active_page': 'reports',
        'total_reports': total_reports,
        'pending_reports': pending_reports,
        'resolved_reports': resolved_reports,
        'reports_by_type': reports_by_type,
        'reports_by_status': reports_by_status,
        'recent_reports': recent_reports,
        'weekly_trend': weekly_trend,
    }
    
    return render(request, 'admin_app/reports_dashboard.html', context)


@login_required
@admin_required
def user_reports(request):
    """User reports management"""
    from posts.models import Report
    from django.db.models import Count
    
    # Get user reports (reports against users)
    reports = Report.objects.filter(
        reported_user__isnull=False
    ).select_related(
        'reported_user', 'reporter'
    ).order_by('-created_at')
    
    # Filters
    status_filter = request.GET.get('status', 'all')
    reason_filter = request.GET.get('reason', '')
    search = request.GET.get('search', '')
    
    if status_filter != 'all':
        reports = reports.filter(status=status_filter)
    
    if reason_filter:
        reports = reports.filter(reason=reason_filter)
    
    if search:
        reports = reports.filter(
            Q(reported_user__username__icontains=search) |
            Q(reporter__username__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Get top reported users
    top_reported_users = Report.objects.filter(
        reported_user__isnull=False
    ).values(
        'reported_user__username',
        'reported_user__id'
    ).annotate(
        report_count=Count('id')
    ).order_by('-report_count')[:10]
    
    # Pagination
    paginator = Paginator(reports, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'reports': page_obj,
        'top_reported_users': top_reported_users,
        'active_page': 'reports',
        'filters': {
            'status': status_filter,
            'reason': reason_filter,
            'search': search,
        }
    }
    
    return render(request, 'admin_app/user_reports.html', context)


@login_required
@admin_required
def content_reports(request):
    """Content reports management"""
    from posts.models import Report
    from django.db.models import Count
    
    # Get content reports (reports against posts)
    reports = Report.objects.filter(
        post__isnull=False
    ).select_related(
        'post', 'post__author', 'reporter'
    ).order_by('-created_at')
    
    # Filters
    status_filter = request.GET.get('status', 'all')
    reason_filter = request.GET.get('reason', '')
    search = request.GET.get('search', '')
    
    if status_filter != 'all':
        reports = reports.filter(status=status_filter)
    
    if reason_filter:
        reports = reports.filter(reason=reason_filter)
    
    if search:
        reports = reports.filter(
            Q(post__title__icontains=search) |
            Q(post__content__icontains=search) |
            Q(post__author__username__icontains=search) |
            Q(reporter__username__icontains=search)
        )
    
    # Get top reported posts
    top_reported_posts = Report.objects.filter(
        post__isnull=False
    ).values(
        'post__title',
        'post__id'
    ).annotate(
        report_count=Count('id')
    ).order_by('-report_count')[:10]
    
    # Pagination
    paginator = Paginator(reports, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'reports': page_obj,
        'top_reported_posts': top_reported_posts,
        'active_page': 'reports',
        'filters': {
            'status': status_filter,
            'reason': reason_filter,
            'search': search,
        }
    }
    
    return render(request, 'admin_app/content_reports.html', context)


@login_required
@admin_required
def analytics_reports(request):
    """Analytics reports"""
    from posts.models import Post, User, Report
    from datetime import datetime, timedelta
    import json
    
    # Date ranges
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # User analytics
    user_stats = {
        'total': User.objects.count(),
        'new_today': User.objects.filter(date_joined__date=today).count(),
        'new_week': User.objects.filter(date_joined__gte=week_ago).count(),
        'new_month': User.objects.filter(date_joined__gte=month_ago).count(),
        'active_today': User.objects.filter(last_login__date=today).count(),
        'active_week': User.objects.filter(last_login__gte=week_ago).count(),
    }
    
    # Content analytics
    content_stats = {
        'total_posts': Post.objects.count(),
        'posts_today': Post.objects.filter(created_at__date=today).count(),
        'posts_week': Post.objects.filter(created_at__gte=week_ago).count(),
        'posts_month': Post.objects.filter(created_at__gte=month_ago).count(),
        'text_posts': Post.objects.filter(type='text').count(),
        'image_posts': Post.objects.filter(type='image').count(),
        'video_posts': Post.objects.filter(type='video').count(),
        'job_posts': Post.objects.filter(type='job').count(),
    }
    
    # Report analytics
    report_stats = {
        'total': Report.objects.count(),
        'pending': Report.objects.filter(status='pending').count(),
        'resolved': Report.objects.filter(status='resolved').count(),
        'dismissed': Report.objects.filter(status='dismissed').count(),
        'today': Report.objects.filter(created_at__date=today).count(),
        'week': Report.objects.filter(created_at__gte=week_ago).count(),
    }
    
    # Daily signups for chart
    daily_signups = []
    for i in range(29, -1, -1):  # Last 30 days
        day = today - timedelta(days=i)
        count = User.objects.filter(date_joined__date=day).count()
        daily_signups.append({
            'day': day.strftime('%m/%d'),
            'count': count
        })
    
    context = {
        'active_page': 'reports',
        'user_stats': user_stats,
        'content_stats': content_stats,
        'report_stats': report_stats,
        'daily_signups': daily_signups,
        'daily_signups_json': json.dumps([item['count'] for item in daily_signups]),
        'daily_labels_json': json.dumps([item['day'] for item in daily_signups]),
    }
    
    return render(request, 'admin_app/analytics_reports.html', context)

@login_required
@admin_required
def site_analytics(request):
    """Site analytics dashboard"""
    from posts.models import Post, User, Report, Reaction, Comment
    from datetime import datetime, timedelta
    import json
    
    # Get duration parameter
    duration = request.GET.get('duration', 'week')
    if duration == 'month':
        days = 30
        date_format = '%m/%d'
    elif duration == 'quarter':
        days = 90
        date_format = '%m/%d'
    else:  # week
        days = 7
        date_format = '%a'
    
    # Date ranges
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # User growth
    total_users = User.objects.count()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    new_users_week = User.objects.filter(date_joined__gte=week_ago).count()
    
    # Content metrics
    total_posts = Post.objects.count()
    posts_today = Post.objects.filter(created_at__date=today).count()
    posts_week = Post.objects.filter(created_at__gte=week_ago).count()
    
    # Engagement metrics - FIXED: Use actual model counts
    total_likes = Reaction.objects.count()
    total_comments = Comment.objects.count()
    total_shares = Post.objects.filter(shared_post__isnull=False).count()
    
    # Report metrics
    pending_reports = Report.objects.filter(status='pending').count() if 'Report' in locals() else 0
    
    # Daily metrics for charts
    daily_metrics = []
    for i in range(days-1, -1, -1):
        day = today - timedelta(days=i)
        
        day_users = User.objects.filter(date_joined__date=day).count()
        day_posts = Post.objects.filter(created_at__date=day).count()
        day_likes = Reaction.objects.filter(created_at__date=day).count()
        day_comments = Comment.objects.filter(created_at__date=day).count()
        
        daily_metrics.append({
            'day': day.strftime(date_format),
            'date': day.strftime('%m/%d'),
            'users': day_users,
            'posts': day_posts,
            'likes': day_likes,
            'comments': day_comments,
        })
    
    # Top performing content - FIXED: Use correct field names
    top_posts = Post.objects.annotate(
        like_count_val=Count('reactions'),
        comment_count_val=Count('comments')
    ).order_by('-like_count_val')[:5]
    
    # Prepare data for JSON
    labels = [item['day'] for item in daily_metrics]
    users_data = [item['users'] for item in daily_metrics]
    posts_data = [item['posts'] for item in daily_metrics]
    engagement_data = [item['likes'] + item['comments'] for item in daily_metrics]
    
    context = {
        'active_page': 'analytics',
        'total_users': total_users,
        'new_users_today': new_users_today,
        'new_users_week': new_users_week,
        'total_posts': total_posts,
        'posts_today': posts_today,
        'posts_week': posts_week,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'pending_reports': pending_reports,
        'daily_metrics': daily_metrics,
        'top_posts': top_posts,
        'duration': duration,
        'date_format': date_format,
        'days': days,
        'daily_labels_json': json.dumps(labels),
        'users_data_json': json.dumps(users_data),
        'posts_data_json': json.dumps(posts_data),
        'engagement_data_json': json.dumps(engagement_data),
    }
    
    return render(request, 'admin_app/site_analytics.html', context)

@login_required
@admin_required
def user_analytics(request):
    """User analytics"""
    from django.contrib.auth.models import User
    from datetime import datetime, timedelta
    from django.db.models import Count, Q
    
    # User demographics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    staff_users = User.objects.filter(is_staff=True).count()
    superusers = User.objects.filter(is_superuser=True).count()
    
    # User growth
    today = datetime.now().date()
    month_ago = today - timedelta(days=30)
    
    user_growth = User.objects.filter(
        date_joined__gte=month_ago
    ).extra({
        'signup_date': "date(date_joined)"
    }).values('signup_date').annotate(
        count=Count('id')
    ).order_by('signup_date')
    
    # User activity
    active_today = User.objects.filter(last_login__date=today).count()
    active_week = User.objects.filter(last_login__gte=today - timedelta(days=7)).count()
    active_month = User.objects.filter(last_login__gte=month_ago).count()
    
    # Top active users
    top_active_users = User.objects.annotate(
        post_count=Count('posts'),
        login_count=Count('last_login')  # Simplified
    ).order_by('-post_count')[:10]
    
    context = {
        'active_page': 'analytics',
        'total_users': total_users,
        'active_users': active_users,
        'staff_users': staff_users,
        'superusers': superusers,
        'active_today': active_today,
        'active_week': active_week,
        'active_month': active_month,
        'user_growth': user_growth,
        'top_active_users': top_active_users,
    }
    
    return render(request, 'admin_app/user_analytics.html', context)


@login_required
@admin_required
def content_analytics(request):
    """Content analytics"""
    from posts.models import Post
    from datetime import datetime, timedelta
    from django.db.models import Count, Q
    
    # Content statistics
    total_posts = Post.objects.count()
    
    # By type
    text_posts = Post.objects.filter(type='text').count()
    image_posts = Post.objects.filter(type='image').count()
    video_posts = Post.objects.filter(type='video').count()
    job_posts = Post.objects.filter(type='job').count()
    
    # Time-based
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    posts_today = Post.objects.filter(created_at__date=today).count()
    posts_week = Post.objects.filter(created_at__gte=week_ago).count()
    posts_month = Post.objects.filter(created_at__gte=month_ago).count()
    
    # Daily posting trend
    daily_posts = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Post.objects.filter(created_at__date=day).count()
        daily_posts.append({
            'day': day.strftime('%a'),
            'date': day.strftime('%m/%d'),
            'count': count
        })
    
    # Top content creators
    top_creators = Post.objects.values(
        'author__username',
        'author__id'
    ).annotate(
        post_count=Count('id')
    ).order_by('-post_count')[:10]
    
    # Content type distribution
    type_distribution = Post.objects.values('type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'active_page': 'analytics',
        'total_posts': total_posts,
        'text_posts': text_posts,
        'image_posts': image_posts,
        'video_posts': video_posts,
        'job_posts': job_posts,
        'posts_today': posts_today,
        'posts_week': posts_week,
        'posts_month': posts_month,
        'daily_posts': daily_posts,
        'top_creators': top_creators,
        'type_distribution': type_distribution,
    }
    
    return render(request, 'admin_app/content_analytics.html', context)


@login_required
@admin_required
def engagement_analytics(request):
    """Engagement analytics"""
    from posts.models import Post, Reaction, Comment, Share
    from datetime import datetime, timedelta
    from django.db.models import Count, Avg
    
    # Get duration parameter
    duration = request.GET.get('duration', 'week')
    if duration == 'month':
        days = 30
        date_format = '%m/%d'
    elif duration == 'quarter':
        days = 90
        date_format = '%m/%d'
    else:  # week
        days = 7
        date_format = '%a'
    
    # Date ranges
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    # Engagement metrics - FIXED: Use actual model counts
    total_likes = Reaction.objects.count()
    total_comments = Comment.objects.count()
    total_shares = Share.objects.count() if 'Share' in locals() else Post.objects.filter(shared_post__isnull=False).count()
    
    # Calculate averages correctly
    # Get posts with their related counts
    posts_with_counts = Post.objects.annotate(
        like_count_db=Count('reactions'),
        comment_count_db=Count('comments'),
        share_count_db=Count('shares') if 'Share' in locals() else Count('post_shares')
    )
    
    # Calculate averages
    if posts_with_counts.exists():
        avg_likes_per_post = posts_with_counts.aggregate(
            avg_likes=Avg('like_count_db')
        )['avg_likes'] or 0
        avg_comments_per_post = posts_with_counts.aggregate(
            avg_comments=Avg('comment_count_db')
        )['avg_comments'] or 0
    else:
        avg_likes_per_post = 0
        avg_comments_per_post = 0
    
    # Time-based engagement
    likes_week = Reaction.objects.filter(created_at__gte=week_ago).count()
    comments_week = Comment.objects.filter(created_at__gte=week_ago).count()
    shares_week = Share.objects.filter(created_at__gte=week_ago).count() if 'Share' in locals() else 0
    
    # Daily engagement trend
    daily_engagement = []
    for i in range(days-1, -1, -1):
        day = today - timedelta(days=i)
        
        day_likes = Reaction.objects.filter(created_at__date=day).count()
        day_comments = Comment.objects.filter(created_at__date=day).count()
        day_shares = Share.objects.filter(created_at__date=day).count() if 'Share' in locals() else 0
        
        daily_engagement.append({
            'day': day.strftime(date_format),
            'date': day.strftime('%m/%d'),
            'likes': day_likes,
            'comments': day_comments,
            'shares': day_shares,
            'total': day_likes + day_comments + day_shares
        })
    
    # Most engaging posts - FIXED: Use annotated fields
    engaging_posts = Post.objects.annotate(
        like_count_db=Count('reactions'),
        comment_count_db=Count('comments'),
        share_count_db=Count('shares') if 'Share' in locals() else Count('post_shares')
    ).annotate(
        total_engagement=Count('reactions') + Count('comments') + Count('shares') if 'Share' in locals() else Count('reactions') + Count('comments')
    ).order_by('-total_engagement')[:10]
    
    # Reaction type distribution
    reaction_types = []
    try:
        reaction_types = Reaction.objects.values('reaction_type').annotate(
            count=Count('id')
        ).order_by('-count')
    except:
        pass
    
    # Calculate percentages
    total_reactions = sum(rt['count'] for rt in reaction_types) if reaction_types else 1
    
    context = {
        'active_page': 'analytics',
        'total_likes': total_likes,
        'total_comments': total_comments,
        'total_shares': total_shares,
        'avg_likes_per_post': round(avg_likes_per_post, 2),
        'avg_comments_per_post': round(avg_comments_per_post, 2),
        'likes_week': likes_week,
        'comments_week': comments_week,
        'shares_week': shares_week,
        'daily_engagement': daily_engagement,
        'engaging_posts': engaging_posts,
        'reaction_types': reaction_types,
        'total_reactions': total_reactions,
        'duration': duration,
        'date_format': date_format,
        'days': days,
    }
    
    return render(request, 'admin_app/engagement_analytics.html', context)

@login_required
@admin_required
def admin_settings(request):
    """Admin settings main page"""
    context = {
        'active_page': 'settings',
    }
    return render(request, 'admin_app/settings.html', context)


@login_required
@admin_required
def general_settings(request):
    """General settings"""
    from django.conf import settings
    
    context = {
        'active_page': 'settings',
        'settings': settings,
    }
    
    return render(request, 'admin_app/general_settings.html', context)


@login_required
@admin_required
def email_settings(request):
    """Email settings"""
    from django.conf import settings
    
    email_config = {
        'email_backend': getattr(settings, 'EMAIL_BACKEND', 'Not configured'),
        'email_host': getattr(settings, 'EMAIL_HOST', 'Not configured'),
        'email_port': getattr(settings, 'EMAIL_PORT', 'Not configured'),
        'email_use_tls': getattr(settings, 'EMAIL_USE_TLS', False),
        'email_host_user': getattr(settings, 'EMAIL_HOST_USER', 'Not configured'),
        'default_from_email': getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured'),
    }
    
    context = {
        'active_page': 'settings',
        'email_config': email_config,
    }
    
    return render(request, 'admin_app/email_settings.html', context)


@login_required
@admin_required
def ai_settings(request):
    """AI settings"""
    from utils.content_validator import get_validator
    
    try:
        validator = get_validator()
        ai_config = {
            'threshold_approve': getattr(validator, 'threshold_approve', 0.5),
            'threshold_warning': getattr(validator, 'threshold_warning', 0.3),
            'model_name': getattr(validator, 'model_name', 'facebook/bart-large-mnli'),
        }
    except:
        ai_config = {
            'threshold_approve': 0.5,
            'threshold_warning': 0.3,
            'model_name': 'facebook/bart-large-mnli',
        }
    
    context = {
        'active_page': 'settings',
        'ai_config': ai_config,
    }
    
    return render(request, 'admin_app/ai_settings.html', context)


@login_required
@admin_required
def bulk_send_notification(request):
    """Bulk send notification to users"""
    if request.method == 'POST':
        user_ids = request.POST.getlist('users')
        notification_type = request.POST.get('notification_type', 'info')
        message = request.POST.get('message', '')
        
        if not message:
            messages.error(request, 'Please enter a message')
            return redirect('admin_app:users')
        
        from posts.models import Notification
        
        users_sent = 0
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                Notification.objects.create(
                    user=user,
                    from_user=request.user,
                    notification_type='follow',  # Using follow as generic
                    post=None
                )
                users_sent += 1
            except User.DoesNotExist:
                continue
        
        messages.success(request, f'✅ Notification sent to {users_sent} users.')
        return redirect('admin_app:users')
    
    return redirect('admin_app:users')


@login_required
@admin_required
def cleanup_inactive_users(request):
    """Cleanup inactive users"""
    from datetime import datetime, timedelta
    
    # Find users inactive for more than 30 days
    cutoff_date = datetime.now() - timedelta(days=30)
    inactive_users = User.objects.filter(
        last_login__lt=cutoff_date,
        is_active=True,
        is_staff=False,
        is_superuser=False
    )
    
    count = inactive_users.count()
    
    if request.method == 'POST':
        # Deactivate users
        inactive_users.update(is_active=False)
        messages.success(request, f'✅ {count} inactive users have been deactivated.')
        return redirect('admin_app:users')
    
    context = {
        'inactive_users': inactive_users,
        'count': count,
        'cutoff_date': cutoff_date,
    }
    
    return render(request, 'admin_app/cleanup_inactive.html', context)


@login_required
@admin_required
def api_recent_activity(request):
    """API for recent activity"""
    from posts.models import Post, User
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    # Recent activity
    recent_posts = Post.objects.filter(created_at__gte=week_ago).count()
    recent_users = User.objects.filter(date_joined__gte=week_ago).count()
    
    # Today's activity
    posts_today = Post.objects.filter(created_at__date=today).count()
    users_today = User.objects.filter(date_joined__date=today).count()
    
    activity = {
        'recent_posts': recent_posts,
        'recent_users': recent_users,
        'posts_today': posts_today,
        'users_today': users_today,
    }
    
    return JsonResponse(activity)


@login_required
@admin_required
def api_chart_data(request):
    """API for chart data"""
    from datetime import datetime, timedelta
    import json
    
    today = datetime.now().date()
    
    # Daily signups for last 7 days
    daily_signups = []
    labels = []
    data = []
    
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = User.objects.filter(date_joined__date=day).count()
        labels.append(day.strftime('%a'))
        data.append(count)
    
    chart_data = {
        'labels': labels,
        'datasets': [{
            'label': 'New Users',
            'data': data,
            'backgroundColor': 'rgba(102, 126, 234, 0.1)',
            'borderColor': 'rgba(102, 126, 234, 1)',
            'borderWidth': 2,
            'fill': True,
            'tension': 0.4,
        }]
    }
    
    return JsonResponse(chart_data)


@login_required
@admin_required
def test_email_connection(request):
    """Test email connection"""
    if request.method == 'POST':
        try:
            import json
            data = json.loads(request.body)
            email = data.get('email')
            
            from django.core.mail import send_mail
            from django.conf import settings
            
            send_mail(
                'TalentForge - Test Email',
                'This is a test email from TalentForge admin panel.',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return JsonResponse({'success': True, 'message': 'Test email sent successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def get_chart_settings(duration='week'):
    """Helper function to get chart settings based on duration"""
    if duration == 'month':
        days = 30
        date_format = '%m/%d'
    elif duration == 'quarter':
        days = 90
        date_format = '%m/%d'
    else:  # week
        days = 7
        date_format = '%a'
    
    return days, date_format