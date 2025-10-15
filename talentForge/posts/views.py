from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Post, Comment, Reaction, Notification
from .forms import PostForm, CommentForm

@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            
            # Déterminer automatiquement le type si non spécifié
            if not post.type:
                if post.image:
                    post.type = 'image'
                elif post.video:
                    post.type = 'video'
                else:
                    post.type = 'text'
            
            post.save()
            messages.success(request, 'Your post has been created successfully!')
            return redirect('posts:post_detail', pk=post.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PostForm()
    
    return render(request, 'posts/post_create.html', {'form': form})

def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'posts/post_list.html', {'posts': posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all().order_by('created_at')
    
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            
            # Créer une notification pour le propriétaire du post
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    post=post,
                    notif_type='comment',
                    message=f"{request.user.username} commented on your post"
                )
                messages.info(request.user, f"{request.user.username} commented on your post")
            
            return redirect('posts:post_detail', pk=post.pk)
    else:
        comment_form = CommentForm()
    
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': comment_form
    })

@login_required
def react_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    reaction_type = request.POST.get('reaction_type', 'like')
    
    # Vérifier si l'utilisateur a déjà réagi à ce post
    existing_reaction = Reaction.objects.filter(post=post, user=request.user).first()
    
    if existing_reaction:
        if existing_reaction.type == reaction_type:
            # Supprimer la réaction si c'est la même
            existing_reaction.delete()
            action = 'removed'
        else:
            # Modifier la réaction
            existing_reaction.type = reaction_type
            existing_reaction.save()
            action = 'updated'
    else:
        # Créer une nouvelle réaction
        Reaction.objects.create(
            post=post,
            user=request.user,
            type=reaction_type
        )
        action = 'added'
        
        # Créer une notification pour le propriétaire du post
        if post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                post=post,
                notif_type='reaction',
                message=f"{request.user.username} reacted to your post"
            )
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'reactions_count': post.reactions.count(),
            'user_reacted': True,
            'action': action
        })
    
    return redirect('posts:post_detail', pk=post.pk)

@login_required
def share_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    # Implémentez la logique de partage ici
    messages.success(request, 'Post shared successfully!')
    return redirect('posts:post_detail', pk=post.pk)

@login_required
def report_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    # Implémentez la logique de signalement ici
    messages.success(request, 'Post reported to administrators.')
    return redirect('posts:post_detail', pk=post.pk)

@login_required
def notifications(request):
    user_notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')
    return render(request, 'posts/notifications.html', {'notifications': user_notifications})

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})