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

from .models import Post, Comment, Reaction, JobPost, Share, Report, UserProfile, Message, Notification
from .forms import PostForm, CommentForm, ShareForm, ReportForm, UserProfileForm, MessageForm, SearchForm


@login_required
def post_create(request):
    if request.method == 'POST':
        post_type = request.POST.get('type', 'text')
        print(f"🎯 Type de post reçu: {post_type}")
        print(f"🎯 Données reçues: {request.POST}")

        form = PostForm(request.POST, request.FILES)

        if form.is_valid():
            print("✅ Formulaire valide")
            post = form.save(commit=False)
            post.author = request.user

            # DEBUG: Print job details before saving
            if post_type == 'job':
                print("🔍 Détails job avant sauvegarde:")
                print(f"   Company: {form.cleaned_data.get('company')}")
                print(f"   Location: {form.cleaned_data.get('location')}")
                print(f"   Work Mode: {form.cleaned_data.get('work_mode')}")
                print(f"   Employment Type: {form.cleaned_data.get('employment_type')}")

            post.save()

            if post.type == 'job':
                try:
                    # Vérifiez si JobPost existe
                    if hasattr(post, 'job_details'):
                        job_details = post.job_details
                        print(f"✅ JobPost créé avec succès!")
                        print(f"   Company: {job_details.company}")
                        print(f"   Location: {job_details.location}")
                    else:
                        print("❌ CRITIQUE: JobPost non créé!")
                        # Création d'urgence du JobPost
                        company = form.cleaned_data.get('company', 'Unknown Company')
                        location = form.cleaned_data.get('location', 'Unknown Location')
                        JobPost.objects.create(
                            post=post,
                            company=company,
                            location=location,
                            work_mode=form.cleaned_data.get('work_mode', 'onsite'),
                            employment_type=form.cleaned_data.get('employment_type', 'full_time'),
                            salary_range=form.cleaned_data.get('salary_range'),
                            application_email=form.cleaned_data.get('application_email'),
                            skills_required=form.cleaned_data.get('skills_required'),
                            benefits=form.cleaned_data.get('benefits')
                        )
                        print(f"🚨 JobPost créé d'urgence: {company} - {location}")
                except Exception as e:
                    print(f"💥 Erreur lors de la vérification JobPost: {e}")

            messages.success(request, 'Your post has been created successfully!')
            return redirect('posts:post_detail', pk=post.pk)
        else:
            print("❌ Erreurs de formulaire:", form.errors)
            messages.error(request, 'Please correct the errors below.')
    else:
        post_type = request.GET.get('type', 'text')
        form = PostForm(initial={'type': post_type})

    return render(request, 'posts/post_create.html', {
        'form': form,
        'post_type': post_type
    })


def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'posts/post_list.html', {'posts': posts})


def post_detail(request, pk):
    """Vue pour les détails d'un post"""
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all().order_by('created_at')
    
    # Vérifier si l'utilisateur a déjà réagi à ce post
    user_reaction = None
    if request.user.is_authenticated:
        user_reaction = Reaction.objects.filter(post=post, user=request.user).first()

    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            
            # Créer une notification pour l'auteur du post
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
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'posts/feed.html', {'posts': posts})


@require_POST
@login_required
def add_reaction(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type', 'like')
        
        # Vérifier si l'utilisateur a déjà réagi
        existing_reaction = Reaction.objects.filter(post=post, user=request.user).first()
        
        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                # Supprimer la réaction si c'est la même
                existing_reaction.delete()
                action = 'removed'
            else:
                # Mettre à jour la réaction
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                action = 'updated'
        else:
            # Créer une nouvelle réaction
            Reaction.objects.create(
                post=post,
                user=request.user,
                reaction_type=reaction_type
            )
            action = 'added'
            
            # Créer une notification pour l'auteur du post
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
    
    # Vérifier si l'utilisateur a déjà partagé ce post
    existing_share = Share.objects.filter(post=post, user=request.user).first()
    
    if request.method == 'POST':
        form = ShareForm(request.POST)
        if form.is_valid():
            if existing_share:
                # Mettre à jour le partage existant
                existing_share.caption = form.cleaned_data['caption']
                existing_share.save()
                action = 'updated'
            else:
                # Créer un nouveau partage
                share = form.save(commit=False)
                share.post = post
                share.user = request.user
                share.save()
                action = 'created'
                
                # Créer une notification pour l'auteur du post
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
    
    # Vérifier que l'utilisateur a un email
    print(f"🔍 DEBUG: User email: {request.user.email}")
    if not request.user.email:
        messages.warning(request, 'Please add an email address to your account to receive confirmation emails.')
    
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
                messages.success(request, 'Thank you for reporting this post. We have sent you a confirmation email.')
            
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
@login_required
def profile_view(request, username=None):
    try:
        if username:
            user = User.objects.get(username=username)
        else:
            user = request.user
        
        # Créer le profil s'il n'existe pas
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        is_following = request.user in profile.followers.all() if request.user.is_authenticated else False
        
        # Get user's posts
        user_posts = Post.objects.filter(author=user).order_by('-created_at')
        
        # Create notification for profile view (if viewing someone else's profile)
        if request.user != user:
            Notification.objects.create(
                user=user,
                from_user=request.user,
                notification_type='view'
            )
        
        context = {
            'profile_user': user,
            'profile': profile,
            'is_following': is_following,
            'followers_count': profile.followers_count(),
            'following_count': profile.following_count(),
            'user_posts': user_posts,
        }
        return render(request, 'posts/profile.html', context)
        
    except User.DoesNotExist:
        messages.error(request, f"User '{username}' not found.")
        return redirect('posts:post_list')
    except Exception as e:
        messages.error(request, "An error occurred while loading the profile.")
        return redirect('posts:post_list')


@login_required
def edit_profile(request):
    profile = request.user.userprofile
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('posts:profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'posts/edit_profile.html', {'form': form})


@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    
    if request.user != user_to_follow:
        profile = user_to_follow.userprofile
        if request.user in profile.followers.all():
            profile.followers.remove(request.user)
            messages.info(request, f'You unfollowed {user_to_follow.username}')
            action = 'unfollowed'
        else:
            profile.followers.add(request.user)
            messages.success(request, f'You are now following {user_to_follow.username}')
            action = 'followed'
            
            # Create follow notification
            Notification.objects.create(
                user=user_to_follow,
                from_user=request.user,
                notification_type='follow'
            )
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'action': action,
                'followers_count': profile.followers_count()
            })
    
    return redirect('posts:profile', username=username)


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