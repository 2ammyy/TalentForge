from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
import json
from django.core.paginator import Paginator

from .models import Post, Comment, Reaction, JobPost, Share, Report, UserProfile, Message, Notification, Follow, Block
from .forms import PostForm, CommentForm, ShareForm, ReportForm, UserProfileForm, MessageForm, SearchForm

from utils.moderation import is_toxic_content


# ADD THIS NEW FUNCTION TO views.py (anywhere in the views file)
@csrf_exempt
@require_POST
def check_toxicity_api(request):
    """
    API endpoint for real-time content checking
    Called by JavaScript as user types
    """
    content = request.POST.get('content', '').strip()
    
    if not content:
        return JsonResponse({
            'error': 'No content provided',
            'is_toxic': False,
            'score': 0.0
        })
    
    # Use our utility function
    is_toxic, score = is_toxic_content(content)
    
    return JsonResponse({
        'is_toxic': is_toxic,
        'score': float(score),
        'content_length': len(content),
        'message': 'Content checked successfully'
    })


# ============ POSTS ============

# @login_required
# def post_create(request):
#     if request.method == 'POST':
#         form = PostForm(request.POST, request.FILES)
        
#         if form.is_valid():
#             post = form.save(commit=False)
#             post.author = request.user
#             post.save()
            
#             messages.success(request, 'Your post has been created successfully!')
#             return redirect('posts:post_detail', pk=post.pk)
#         else:
#             messages.error(request, 'Please correct the errors below.')
#     else:
#         post_type = request.GET.get('type', 'text')
#         form = PostForm(initial={'type': post_type})

#     return render(request, 'posts/post_create.html', {
#         'form': form,
#         'post_type': post_type if 'post_type' in locals() else 'text'
#     })

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        
        if form.is_valid():
            # --- ADD TOXICITY CHECK HERE ---
            content = form.cleaned_data.get('content', '')
            is_toxic, score = is_toxic_content(content)
            
            if is_toxic:
                messages.error(
                    request,
                    f"⚠️ Your post contains inappropriate language "
                    f"(detected with {score:.0%} confidence). "
                    "Please modify your text before posting."
                )
                # Return form with entered data
                return render(request, 'posts/post_create.html', {
                    'form': form,
                    'post_type': request.GET.get('type', 'text')
                })
            # --- END TOXICITY CHECK ---
            
            # If not toxic, proceed with saving
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            
            messages.success(request, 'Your post has been created successfully!')
            return redirect('posts:post_detail', pk=post.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        post_type = request.GET.get('type', 'text')
        form = PostForm(initial={'type': post_type})

    return render(request, 'posts/post_create.html', {
        'form': form,
        'post_type': post_type if 'post_type' in locals() else 'text'
    })

def post_list(request):
    # Get all posts with related data
    posts = Post.objects.all().select_related(
        'author', 
        'author__userprofile',
        'job_details'
    ).prefetch_related(
        'comments',
        'reactions',
        'post_shares'
    ).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(posts, 12)  # 12 posts per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'posts/post_list.html', {
        'posts': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    })


# def post_detail(request, pk):
#     """View for post details"""
#     post = get_object_or_404(Post, pk=pk)
#     comments = post.comments.all().order_by('created_at')
    
#     # Check if user has already reacted to this post
#     user_reaction = None
#     if request.user.is_authenticated:
#         user_reaction = Reaction.objects.filter(post=post, user=request.user).first()

#     if request.method == 'POST' and request.user.is_authenticated:
#         comment_form = CommentForm(request.POST)
#         if comment_form.is_valid():
#             comment = comment_form.save(commit=False)
#             comment.post = post
#             comment.author = request.user
#             comment.save()
            
#             # Create notification for post author
#             if post.author != request.user:
#                 Notification.objects.create(
#                     user=post.author,
#                     from_user=request.user,
#                     notification_type='comment',
#                     post=post
#                 )
            
#             messages.success(request, 'Comment added successfully!')
#             return redirect('posts:post_detail', pk=post.pk)
#     else:
#         comment_form = CommentForm()

#     return render(request, 'posts/post_detail.html', {
#         'post': post,
#         'comments': comments,
#         'form': comment_form,
#         'user_reaction': user_reaction
#     })

# In the same views.py - MODIFY THE post_detail FUNCTION
def post_detail(request, pk):
    """View for post details"""
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all().order_by('created_at')
    
    # Check if user has already reacted to this post
    user_reaction = None
    if request.user.is_authenticated:
        user_reaction = Reaction.objects.filter(post=post, user=request.user).first()

    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            # --- ADD TOXICITY CHECK FOR COMMENTS ---
            comment_content = comment_form.cleaned_data.get('content', '')
            is_toxic, score = is_toxic_content(comment_content)
            
            if is_toxic:
                messages.error(
                    request,
                    f"⚠️ Your comment contains inappropriate language "
                    f"(detected with {score:.0%} confidence). "
                    "Please modify your text."
                )
                return render(request, 'posts/post_detail.html', {
                    'post': post,
                    'comments': comments,
                    'form': comment_form,
                    'user_reaction': user_reaction
                })
            # --- END TOXICITY CHECK ---
            
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            
            # Create notification for post author
            if post.author != request.user:
                Notification.objects.create(
                    user=post.author,
                    from_user=request.user,
                    notification_type='comment',
                    post=post
                )
            
            messages.success(request, 'Comment added successfully!')
            return redirect('posts:post_detail', pk=post.pk)
    else:
        comment_form = CommentForm()

    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': comment_form,
        'user_reaction': user_reaction
    })

@login_required
def feed(request):
    # Show posts from followed users and popular posts
    following_ids = Follow.objects.filter(follower=request.user).values_list('following_id', flat=True)
    posts = Post.objects.filter(
        Q(author_id__in=following_ids) | 
        Q(reactions__gt=5)  # Popular posts
    ).distinct().select_related('author', 'author__userprofile').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'posts/feed.html', {
        'posts': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    })


@require_POST
@login_required
def add_reaction(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type', 'like')
        
        # Check if user has already reacted
        existing_reaction = Reaction.objects.filter(post=post, user=request.user).first()
        
        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                # Remove reaction if it's the same
                existing_reaction.delete()
                action = 'removed'
            else:
                # Update reaction
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                action = 'updated'
        else:
            # Create new reaction
            Reaction.objects.create(
                post=post,
                user=request.user,
                reaction_type=reaction_type
            )
            action = 'added'
            
            # Create notification for post author
            if post.author != request.user:
                Notification.objects.create(
                    user=post.author,
                    from_user=request.user,
                    notification_type='like',
                    post=post
                )
        
        return JsonResponse({
            'success': True,
            'action': action,
            'total_reactions': post.reactions.count(),
            'user_reaction': reaction_type if action != 'removed' else None
        })
    except Post.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Post not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def share_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user has already shared this post
    existing_share = Share.objects.filter(post=post, user=request.user).first()
    
    if request.method == 'POST':
        form = ShareForm(request.POST)
        if form.is_valid():
            if existing_share:
                # Update existing share
                existing_share.caption = form.cleaned_data['caption']
                existing_share.save()
                action = 'updated'
            else:
                # Create new share
                share = form.save(commit=False)
                share.post = post
                share.user = request.user
                share.save()
                action = 'created'
                
                # Create notification for post author
                if post.author != request.user:
                    Notification.objects.create(
                        user=post.author,
                        from_user=request.user,
                        notification_type='share',
                        post=post
                    )
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True, 
                    'action': action,
                    'share_count': post.post_shares.count()
                })
            messages.success(request, 'Post shared successfully!')
            return redirect('posts:post_list')
    
    else:
        initial = {'caption': existing_share.caption if existing_share else ''}
        form = ShareForm(initial=initial)
    
    return render(request, 'posts/share_post.html', {
        'form': form,
        'post': post,
        'existing_share': existing_share
    })


@login_required
def unshare_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    Share.objects.filter(post=post, user=request.user).delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True, 
            'share_count': post.post_shares.count()
        })
    messages.info(request, 'Post unshared successfully!')
    return redirect('posts:post_list')


@login_required
def report_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user has already reported this post
    existing_report = Report.objects.filter(post=post, reporter=request.user).first()
    
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            # If user already reported, update the existing report
            if existing_report:
                existing_report.reason = form.cleaned_data['reason']
                existing_report.description = form.cleaned_data['description']
                existing_report.status = 'pending'
                existing_report.save()
                messages.success(request, 'Your report has been updated successfully.')
            else:
                report = form.save(commit=False)
                report.post = post
                report.reporter = request.user
                report.save()
                messages.success(request, 'Thank you for reporting this post.')
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Report submitted successfully'})
            return redirect('posts:post_detail', pk=post.id)
    else:
        initial_data = {}
        if existing_report:
            initial_data = {
                'reason': existing_report.reason,
                'description': existing_report.description
            }
        form = ReportForm(initial=initial_data)
    
    context = {
        'form': form,
        'post': post,
        'existing_report': existing_report,
    }
    return render(request, 'posts/report_post.html', context)


@login_required
def my_reports(request):
    reports = Report.objects.filter(reporter=request.user).select_related('post').order_by('-created_at')
    context = {
        'reports': reports
    }
    return render(request, 'posts/my_reports.html', context)


@login_required
def test_email_view(request):
    try:
        send_mail(
            'Test Email from TalentForge',
            f'This is a test email sent to {request.user.email}',
            'talentforge.app@gmail.com',
            [request.user.email],
            fail_silently=False,
        )
        return HttpResponse(f"✅ Test email sent to {request.user.email}! Check your inbox.")
    except Exception as e:
        return HttpResponse(f"❌ Failed to send test email: {str(e)}")


# @login_required
# def post_edit(request, pk):
#     """View for editing an existing post"""
#     post = get_object_or_404(Post, pk=pk)
    
#     # Check if user is authorized to edit
#     if post.author != request.user and not request.user.is_staff:
#         messages.error(request, "You don't have permission to edit this post.")
#         return redirect('posts:post_detail', pk=post.pk)
    
#     if request.method == 'POST':
#         form = PostForm(request.POST, request.FILES, instance=post)
#         if form.is_valid():
#             updated_post = form.save()
#             messages.success(request, 'Post updated successfully!')
#             return redirect('posts:post_detail', pk=updated_post.pk)
#         else:
#             messages.error(request, 'Please correct the errors below.')
#     else:
#         form = PostForm(instance=post)
    
#     return render(request, 'posts/post_edit.html', {
#         'form': form,
#         'post': post
#     })


# MODIFY THE post_edit FUNCTION
@login_required
def post_edit(request, pk):
    """View for editing an existing post"""
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user is authorized to edit
    if post.author != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to edit this post.")
        return redirect('posts:post_detail', pk=post.pk)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            # --- ADD TOXICITY CHECK FOR EDITS ---
            content = form.cleaned_data.get('content', '')
            is_toxic, score = is_toxic_content(content)
            
            if is_toxic:
                messages.error(
                    request,
                    f"⚠️ Your post contains inappropriate language "
                    f"(detected with {score:.0%} confidence). "
                    "Please modify your text."
                )
                return render(request, 'posts/post_edit.html', {
                    'form': form,
                    'post': post
                })
            # --- END TOXICITY CHECK ---
            
            updated_post = form.save()
            messages.success(request, 'Post updated successfully!')
            return redirect('posts:post_detail', pk=updated_post.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PostForm(instance=post)
    
    return render(request, 'posts/post_edit.html', {
        'form': form,
        'post': post
    })

@login_required
def post_delete(request, pk):
    """View for deleting a post"""
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user is authorized to delete
    if post.author != request.user and not request.user.is_staff:
        messages.error(request, "You don't have permission to delete this post.")
        return redirect('posts:post_detail', pk=post.pk)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('posts:post_list')
    
    return render(request, 'posts/post_confirm_delete.html', {
        'post': post
    })


@login_required
def post_update(request, pk):
    """Alternative name for post edit - same functionality"""
    return post_edit(request, pk)


# ============ PROFILES & SOCIAL FEATURES ============

# In talentForge/posts/views.py

@login_required
def my_profile(request):
    """Profile of the logged-in user"""
    user_posts = Post.objects.filter(author=request.user).order_by('-created_at')
    
    # Get shared posts
    shared_posts = Share.objects.filter(user=request.user).select_related(
        'post', 'post__author', 'post__author__userprofile'
    ).order_by('-created_at')
    
    context = {
        'profile_user': request.user,
        'user_posts': user_posts,
        'shared_posts': shared_posts,
        'is_own_profile': True
    }
    
    return render(request, 'posts/profile.html', context)


def user_profile(request, username):
    """Profile of another user"""
    profile_user = get_object_or_404(User, username=username)
    user_posts = Post.objects.filter(author=profile_user).order_by('-created_at')
    
    # Get shared posts
    shared_posts = Share.objects.filter(user=profile_user).select_related(
        'post', 'post__author', 'post__author__userprofile'
    ).order_by('-created_at')
    
    context = {
        'profile_user': profile_user,
        'user_posts': user_posts,
        'shared_posts': shared_posts,
        'is_own_profile': False
    }
    
    # Check social relations only if user is logged in
    if request.user.is_authenticated and request.user != profile_user:
        # Check if user follows this profile
        try:
            context['is_following'] = Follow.objects.filter(
                follower=request.user, 
                following=profile_user
            ).exists()
        except:
            context['is_following'] = False
        
        # Check if user has blocked this profile
        try:
            context['is_blocked'] = Block.objects.filter(
                blocker=request.user, 
                blocked=profile_user
            ).exists()
        except:
            context['is_blocked'] = False
    
    return render(request, 'posts/profile.html', context)


@login_required
def edit_profile(request):
    """Redirect to base app profile edit"""
    return redirect('base:edit_profile')


# ============ SOCIAL ACTIONS ============

@login_required
def follow_user(request, username):
    """Follow a user"""
    if request.method == 'POST':
        user_to_follow = get_object_or_404(User, username=username)
        
        if request.user == user_to_follow:
            messages.error(request, "You cannot follow yourself.")
            return redirect('posts:user_profile', username=username)
        
        # Check if already following
        if Follow.objects.filter(follower=request.user, following=user_to_follow).exists():
            messages.info(request, f"You are already following {username}.")
            return redirect('posts:user_profile', username=username)
        
        # Create follow relationship
        Follow.objects.create(follower=request.user, following=user_to_follow)
        
        # Create notification
        try:
            Notification.objects.create(
                user=user_to_follow,
                from_user=request.user,
                notification_type='follow',
                post=None
            )
        except:
            pass
        
        messages.success(request, f"You are now following {username}.")
        return redirect('posts:user_profile', username=username)
    
    return redirect('posts:user_profile', username=username)


@login_required
def unfollow_user(request, username):
    """Unfollow a user"""
    if request.method == 'POST':
        user_to_unfollow = get_object_or_404(User, username=username)
        
        follow_relationship = Follow.objects.filter(
            follower=request.user, 
            following=user_to_unfollow
        )
        
        if follow_relationship.exists():
            follow_relationship.delete()
            messages.success(request, f"You have unfollowed {username}.")
        else:
            messages.info(request, f"You were not following {username}.")
        
        return redirect('posts:user_profile', username=username)
    
    return redirect('posts:user_profile', username=username)


@login_required
def block_user(request, username):
    """Block a user"""
    if request.method == 'POST':
        user_to_block = get_object_or_404(User, username=username)
        
        if request.user == user_to_block:
            messages.error(request, "You cannot block yourself.")
            return redirect('posts:user_profile', username=username)
        
        # Check if already blocked
        if Block.objects.filter(blocker=request.user, blocked=user_to_block).exists():
            messages.info(request, f"You have already blocked {username}.")
            return redirect('posts:user_profile', username=username)
        
        # Create block relationship
        Block.objects.create(blocker=request.user, blocked=user_to_block)
        
        # Remove follow relationships if they exist
        Follow.objects.filter(follower=request.user, following=user_to_block).delete()
        Follow.objects.filter(follower=user_to_block, following=request.user).delete()
        
        messages.success(request, f"You have blocked {username}.")
        return redirect('posts:user_profile', username=username)
    
    return redirect('posts:user_profile', username=username)


@login_required
def unblock_user(request, username):
    """Unblock a user"""
    if request.method == 'POST':
        user_to_unblock = get_object_or_404(User, username=username)
        
        block_relationship = Block.objects.filter(
            blocker=request.user, 
            blocked=user_to_unblock
        )
        
        if block_relationship.exists():
            block_relationship.delete()
            messages.success(request, f"You have unblocked {username}.")
        else:
            messages.info(request, f"You had not blocked {username}.")
        
        return redirect('posts:user_profile', username=username)
    
    return redirect('posts:user_profile', username=username)


@login_required
def report_user(request, username):
    """Report a user"""
    if request.method == 'POST':
        user_to_report = get_object_or_404(User, username=username)
        
        if request.user == user_to_report:
            messages.error(request, "You cannot report yourself.")
            return redirect('posts:user_profile', username=username)
        
        reason = request.POST.get('reason')
        details = request.POST.get('details', '')
        
        # Create report
        Report.objects.create(
            reporter=request.user,
            reported_user=user_to_report,
            reason=reason,
            description=details,
            post=None
        )
        
        messages.success(request, f"Thank you for reporting {username}. We will review your report.")
        return redirect('posts:user_profile', username=username)
    
    return redirect('posts:user_profile', username=username)


# ============ SEARCH ============

@login_required
def search_view(request):
    query = request.GET.get('q', '')
    search_type = request.GET.get('search_type', 'all')
    
    post_results = []
    user_results = []
    job_results = []
    
    if query:
        if search_type in ['all', 'posts']:
            post_results = Post.objects.filter(
                Q(title__icontains=query) | 
                Q(content__icontains=query)
            ).select_related('author').order_by('-created_at')
        
        if search_type in ['all', 'users']:
            user_results = User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            ).distinct()
        
        if search_type in ['all', 'jobs']:
            job_results = JobPost.objects.filter(
                Q(company__icontains=query) |
                Q(location__icontains=query) |
                Q(post__title__icontains=query) |
                Q(skills_required__icontains=query)
            ).select_related('post').order_by('-created_at')
    
    return render(request, 'posts/search_results.html', {
        'query': query,
        'search_type': search_type,
        'post_results': post_results,
        'user_results': user_results,
        'job_results': job_results,
    })


# ============ MESSAGING SYSTEM ============

@login_required
def messages_view(request):
    # Get unique conversations
    sent_messages = Message.objects.filter(sender=request.user).values('receiver').distinct()
    received_messages = Message.objects.filter(receiver=request.user).values('sender').distinct()
    
    user_ids = set()
    for msg in sent_messages:
        user_ids.add(msg['receiver'])
    for msg in received_messages:
        user_ids.add(msg['sender'])
    
    conversations = []
    for user_id in user_ids:
        user = User.objects.get(id=user_id)
        last_message = Message.objects.filter(
            Q(sender=request.user, receiver=user) | 
            Q(sender=user, receiver=request.user)
        ).order_by('-timestamp').first()
        
        unread_count = Message.objects.filter(
            sender=user, receiver=request.user, is_read=False
        ).count()
        
        conversations.append({
            'user': user,
            'last_message': last_message,
            'unread_count': unread_count
        })
    
    # Sort by last message timestamp
    conversations.sort(key=lambda x: x['last_message'].timestamp if x['last_message'] else x['user'].date_joined, reverse=True)
    
    # Mark messages as read when user opens messages page
    Message.objects.filter(receiver=request.user, is_read=False).update(is_read=True)
    
    return render(request, 'posts/messages.html', {
        'conversations': conversations
    })


@login_required
def conversation_view(request, username):
    other_user = get_object_or_404(User, username=username)
    message_list = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    ).order_by('timestamp')
    
    # Mark messages as read
    Message.objects.filter(sender=other_user, receiver=request.user, is_read=False).update(is_read=True)
    
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = other_user
            message.save()
            return redirect('posts:conversation', username=username)
    else:
        form = MessageForm()
    
    return render(request, 'posts/conversation.html', {
        'other_user': other_user,
        'message_list': message_list,
        'form': form
    })


# ============ NOTIFICATIONS ============

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-timestamp')
    unread_count = notifications.filter(is_read=False).count()
    
    # Mark as read when user views notifications
    if request.method == 'GET':
        notifications.update(is_read=True)
    
    return render(request, 'posts/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })


@login_required
def get_unread_counts(request):
    unread_messages = Message.objects.filter(receiver=request.user, is_read=False).count()
    unread_notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    
    return JsonResponse({
        'unread_messages': unread_messages,
        'unread_notifications': unread_notifications
    })


@login_required
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('posts:notifications')


@login_required
def clear_all_notifications(request):
    """Mark all notifications as read"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'All notifications marked as read!')
    return redirect('posts:notifications')