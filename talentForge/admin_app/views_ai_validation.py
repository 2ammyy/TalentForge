# talentForge/admin_app/views_ai_validation.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q, Avg, F
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import json

# Get the active User model
User = get_user_model()

from .permissions import admin_required
from posts.models import Post, ContentValidationLog, CreativeCategory
from utils.content_validator import get_validator, validate_content

@login_required
@admin_required
def validation_dashboard(request):
    """Dashboard for AI content validation analytics"""
    
    # Get date ranges
    today = timezone.now().date()
    
    # Overall validation stats
    total_validations = ContentValidationLog.objects.count()
    approved_count = ContentValidationLog.objects.filter(is_approved=True).count()
    rejection_count = ContentValidationLog.objects.filter(is_approved=False).count()
    
    approval_rate = (approved_count / total_validations * 100) if total_validations > 0 else 0
    rejection_rate = (rejection_count / total_validations * 100) if total_validations > 0 else 0
    
    # Recent validations
    recent_validations = ContentValidationLog.objects.select_related('post', 'user').order_by('-created_at')[:10]
    
    # Score distribution
    score_stats = {
        'excellent': ContentValidationLog.objects.filter(score__gte=0.8).count(),
        'good': ContentValidationLog.objects.filter(score__gte=0.6, score__lt=0.8).count(),
        'average': ContentValidationLog.objects.filter(score__gte=0.4, score__lt=0.6).count(),
        'poor': ContentValidationLog.objects.filter(score__lt=0.4).count(),
    }
    
    # Category statistics
    category_stats = []
    categories = CreativeCategory.objects.filter(is_active=True)
    for category in categories:
        count = ContentValidationLog.objects.filter(
            detected_categories__contains=[category.name]
        ).count()
        if count > 0:
            category_stats.append({
                'name': category.name,
                'count': count,
                'percentage': (count / total_validations * 100) if total_validations > 0 else 0
            })
    
    # Sort by count
    category_stats.sort(key=lambda x: x['count'], reverse=True)
    
    # User statistics - Get users with highest average validation scores
    # Using direct ContentValidationLog relationship
    top_creators = User.objects.filter(
        contentvalidationlog__isnull=False
    ).annotate(
        validation_count=Count('contentvalidationlog'),
        avg_score=Avg('contentvalidationlog__score')
    ).filter(
        validation_count__gt=0,
        avg_score__isnull=False
    ).order_by('-avg_score')[:5]
    
    # Weekly trends
    daily_stats = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_validations = ContentValidationLog.objects.filter(created_at__date=day)
        day_count = day_validations.count()
        day_avg = day_validations.aggregate(avg=Avg('score'))['avg'] or 0
        
        daily_stats.append({
            'day': day.strftime('%a'),
            'date': day.strftime('%m/%d'),
            'count': day_count,
            'avg_score': round(day_avg, 2)
        })
    
    # Top performing categories by average score
    category_performance = []
    for category in CreativeCategory.objects.filter(is_active=True)[:5]:
        logs = ContentValidationLog.objects.filter(
            detected_categories__contains=[category.name]
        )
        if logs.exists():
            avg_score = logs.aggregate(avg=Avg('score'))['avg'] or 0
            category_performance.append({
                'name': category.name,
                'avg_score': round(avg_score, 2),
                'count': logs.count()
            })
    
    context = {
        'active_page': 'validation_dashboard',
        'total_validations': total_validations,
        'approved_count': approved_count,
        'rejection_count': rejection_count,
        'approval_rate': round(approval_rate, 1),
        'rejection_rate': round(rejection_rate, 1),
        'recent_validations': recent_validations,
        'score_stats': score_stats,
        'category_stats': category_stats[:10],  # Top 10 categories
        'top_creators': top_creators,
        'daily_stats': daily_stats,
        'category_performance': category_performance,
    }
    
    return render(request, 'admin_app/validation_dashboard.html', context)

@login_required
@admin_required
def creative_categories(request):
    """Manage creative categories for AI validation"""
    categories = CreativeCategory.objects.all().order_by('name')
    
    if request.method == 'POST':
        if 'add_category' in request.POST:
            name = request.POST.get('name')
            keywords = request.POST.get('keywords')
            description = request.POST.get('description', '')
            weight = float(request.POST.get('weight', 1.0))
            
            if name and keywords:
                category = CreativeCategory.objects.create(
                    name=name,
                    keywords=keywords,
                    description=description,
                    weight=weight
                )
                messages.success(request, f'Category "{name}" added successfully!')
                return redirect('admin_app:creative_categories')
        
        elif 'update_category' in request.POST:
            category_id = request.POST.get('category_id')
            category = get_object_or_404(CreativeCategory, id=category_id)
            
            category.name = request.POST.get(f'name_{category_id}')
            category.keywords = request.POST.get(f'keywords_{category_id}')
            category.description = request.POST.get(f'description_{category_id}', '')
            category.weight = float(request.POST.get(f'weight_{category_id}', 1.0))
            category.is_active = request.POST.get(f'active_{category_id}') == 'on'
            category.save()
            
            messages.success(request, f'Category "{category.name}" updated!')
            return redirect('admin_app:creative_categories')
        
        elif 'delete_category' in request.POST:
            category_id = request.POST.get('category_id')
            category = get_object_or_404(CreativeCategory, id=category_id)
            name = category.name
            category.delete()
            messages.success(request, f'Category "{name}" deleted!')
            return redirect('admin_app:creative_categories')
    
    context = {
        'active_page': 'creative_categories',
        'categories': categories,
    }
    
    return render(request, 'admin_app/creative_categories.html', context)

@login_required
@admin_required
def validation_logs(request):
    """View validation logs with filtering"""
    logs = ContentValidationLog.objects.select_related('post', 'user').order_by('-created_at')
    
    # Filters
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    score_min = request.GET.get('score_min', '')
    score_max = request.GET.get('score_max', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)
    if score_min:
        try:
            logs = logs.filter(score__gte=float(score_min))
        except ValueError:
            pass
    if score_max:
        try:
            logs = logs.filter(score__lte=float(score_max))
        except ValueError:
            pass
    if status == 'approved':
        logs = logs.filter(is_approved=True)
    elif status == 'rejected':
        logs = logs.filter(is_approved=False)
    
    if search:
        logs = logs.filter(
            Q(post__title__icontains=search) |
            Q(post__content__icontains=search) |
            Q(user__username__icontains=search) |
            Q(notes__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'active_page': 'validation_logs',
        'logs': page_obj,
        'filters': {
            'date_from': date_from,
            'date_to': date_to,
            'score_min': score_min,
            'score_max': score_max,
            'status': status,
            'search': search,
        }
    }
    
    return render(request, 'admin_app/validation_logs.html', context)

@login_required
@admin_required
def validation_settings(request):
    """Configure validation settings"""
    
    # Default settings
    default_settings = {
        'threshold_approve': 0.5,
        'threshold_warning': 0.3,
        'enable_real_time': True,
        'enable_job_validation': True,
        'enable_image_validation': True,
        'enable_video_validation': True,
        'ai_model': 'facebook/bart-large-mnli',
    }
    
    if request.method == 'POST':
        # Save settings
        try:
            threshold_approve = float(request.POST.get('threshold_approve', 0.5))
            threshold_warning = float(request.POST.get('threshold_warning', 0.3))
        except ValueError:
            messages.error(request, 'Please enter valid numbers for thresholds')
            return redirect('admin_app:validation_settings')
        
        enable_real_time = request.POST.get('enable_real_time') == 'on'
        enable_job_validation = request.POST.get('enable_job_validation') == 'on'
        enable_image_validation = request.POST.get('enable_image_validation') == 'on'
        enable_video_validation = request.POST.get('enable_video_validation') == 'on'
        
        # Update settings (in a real app, you'd save these to a database)
        default_settings['threshold_approve'] = threshold_approve
        default_settings['threshold_warning'] = threshold_warning
        default_settings['enable_real_time'] = enable_real_time
        default_settings['enable_job_validation'] = enable_job_validation
        default_settings['enable_image_validation'] = enable_image_validation
        default_settings['enable_video_validation'] = enable_video_validation
        
        # Update validator instance if available
        try:
            validator = get_validator()
            if hasattr(validator, 'threshold_approve'):
                validator.threshold_approve = threshold_approve
            if hasattr(validator, 'threshold_warning'):
                validator.threshold_warning = threshold_warning
        except:
            pass  # Validator might not be available yet
        
        messages.success(request, 'Validation settings updated!')
        return redirect('admin_app:validation_settings')
    
    context = {
        'active_page': 'validation_settings',
        'settings': default_settings,
    }
    
    return render(request, 'admin_app/validation_settings.html', context)

@login_required
@admin_required
def manual_validation(request, post_id):
    """Manually validate a post"""
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')
        
        try:
            score = float(request.POST.get('score', 0))
            categories = json.loads(request.POST.get('categories', '[]'))
            suggestions = json.loads(request.POST.get('suggestions', '[]'))
        except (ValueError, json.JSONDecodeError):
            messages.error(request, 'Invalid data provided')
            return redirect('admin_app:validation_logs')
        
        # Create or update validation log
        log, created = ContentValidationLog.objects.update_or_create(
            post=post,
            defaults={
                'user': request.user,
                'content_type': post.type,
                'score': score,
                'is_approved': action == 'approve',
                'detected_categories': categories,
                'suggestions': suggestions,
                'notes': notes,
            }
        )
        
        if action == 'approve':
            messages.success(request, f'Post "{post.title}" approved!')
        else:
            messages.warning(request, f'Post "{post.title}" rejected!')
        
        return redirect('admin_app:validation_logs')
    
    # Get AI validation result if validator is available
    validation_result = None
    try:
        validator = get_validator()
        validation_data = {
            'type': post.type,
            'title': post.title or '',
            'content': post.content or '',
            'image': post.image if post.image else None,
            'video': post.video if post.video else None,
        }
        
        if hasattr(post, 'job_details') and post.job_details:
            validation_data['job_fields'] = {
                'company': post.job_details.company,
                'location': post.job_details.location,
                'skills_required': post.job_details.skills_required or '',
            }
        
        validation_result = validator.validate_post(validation_data)
    except:
        # Validator not available, use default values
        validation_result = {
            'score': 0.5,
            'is_approved': True,
            'detected_categories': [],
            'suggestions': []
        }
    
    context = {
        'post': post,
        'validation_result': validation_result,
    }
    
    return render(request, 'admin_app/manual_validation.html', context)

@login_required
@admin_required
def test_validation(request):
    """Test validation with custom text"""
    result = None
    
    if request.method == 'POST':
        test_text = request.POST.get('test_text', '')
        test_type = request.POST.get('test_type', 'text')
        
        if test_text:
            try:
                validator = get_validator()
                
                validation_data = {
                    'type': test_type,
                    'title': request.POST.get('test_title', ''),
                    'content': test_text,
                }
                
                if test_type == 'job':
                    validation_data['job_fields'] = {
                        'company': request.POST.get('test_company', ''),
                        'location': request.POST.get('test_location', ''),
                        'skills_required': request.POST.get('test_skills', ''),
                    }
                
                result = validator.validate_post(validation_data)
            except Exception as e:
                messages.error(request, f'Validation error: {str(e)}')
    
    context = {
        'active_page': 'validation_dashboard',
        'test_result': result,
    }
    
    return render(request, 'admin_app/test_validation.html', context)

@login_required
@admin_required
def api_validation_stats(request):
    """API for validation dashboard widgets"""
    today = timezone.now().date()
    
    # Real-time stats
    today_validations = ContentValidationLog.objects.filter(created_at__date=today)
    today_count = today_validations.count()
    today_approved = today_validations.filter(is_approved=True).count()
    
    stats = {
        'validations_today': today_count,
        'approved_today': today_approved,
        'approval_rate_today': (today_approved / today_count * 100) if today_count > 0 else 0,
        'avg_score_today': today_validations.aggregate(avg=Avg('score'))['avg'] or 0,
    }
    
    return JsonResponse(stats)

@login_required
@admin_required
def validation_overview(request):
    """Quick overview of validation statistics"""
    
    # Quick stats
    total_posts = Post.objects.count()
    validated_posts = ContentValidationLog.objects.values('post').distinct().count()
    pending_validation = total_posts - validated_posts
    
    # Recent validations (last 24 hours)
    yesterday = timezone.now() - timedelta(hours=24)
    recent_count = ContentValidationLog.objects.filter(created_at__gte=yesterday).count()
    
    # Top issues
    low_score_count = ContentValidationLog.objects.filter(score__lt=0.4).count()
    
    context = {
        'active_page': 'validation_dashboard',
        'total_posts': total_posts,
        'validated_posts': validated_posts,
        'pending_validation': pending_validation,
        'recent_count': recent_count,
        'low_score_count': low_score_count,
        'validation_rate': (validated_posts / total_posts * 100) if total_posts > 0 else 0,
    }
    
    return render(request, 'admin_app/validation_overview.html', context)