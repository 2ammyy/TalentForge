from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator
from datetime import datetime, timedelta
import csv

from .permissions import admin_required

@login_required
@admin_required
def admin_dashboard(request):
    """Main admin dashboard"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Basic statistics
    stats = {
        'total_users': User.objects.count(),
        'new_users_today': User.objects.filter(date_joined__date=today).count(),
        'new_users_week': User.objects.filter(date_joined__gte=week_ago).count(),
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
    except:
        stats['total_posts'] = 0
        stats['posts_today'] = 0
    
    # Recent users
    recent_users = User.objects.order_by('-date_joined')[:10]
    
    # Daily signups for chart (last 7 days including today)
    daily_signups = []
    
    # Start from 6 days ago to today
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = User.objects.filter(date_joined__date=day).count()
        daily_signups.append({
            'day': day.strftime('%a'),  # Short day name like "Mon"
            'count': count
        })
    
    print("Daily signups data:", daily_signups)  # Debug print
    
    context = {
        'stats': stats,
        'recent_users': recent_users,
        'daily_signups': daily_signups,
        'active_page': 'dashboard',
    }
    
    return render(request, 'admin_app/dashboard.html', context)
    """Main admin dashboard"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Basic statistics
    stats = {
        'total_users': User.objects.count(),
        'new_users_today': User.objects.filter(date_joined__date=today).count(),
        'new_users_week': User.objects.filter(date_joined__gte=week_ago).count(),
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
    except:
        stats['total_posts'] = 0
        stats['posts_today'] = 0
    
    # Recent users
    recent_users = User.objects.order_by('-date_joined')[:10]
    
    # Daily signups for chart (last 7 days including today)
    daily_signups = []
    labels = []
    data = []
    
    for i in range(6, -1, -1):  # Last 7 days including today
        day = today - timedelta(days=i)
        count = User.objects.filter(date_joined__date=day).count()
        daily_signups.append({
            'day': day.strftime('%a'),
            'date': day.strftime('%m/%d'),
            'count': count
        })
        labels.append(day.strftime('%a'))
        data.append(count)
    
    context = {
        'stats': stats,
        'recent_users': recent_users,
        'daily_signups': daily_signups,
        'chart_labels': labels,  # Add this
        'chart_data': data,      # Add this
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