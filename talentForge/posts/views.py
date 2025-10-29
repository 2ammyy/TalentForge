from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Post, Comment, Reaction, Notification  , JobPost
from .forms import PostForm, CommentForm
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

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


def posts_list(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'posts/post_list.html', {'posts': posts})

def post_detail(request, pk):
    """Vue pour les détails d'un post (si elle n'existe pas)"""
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all().order_by('created_at')

    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('posts:post_detail', pk=post.pk)
    else:
        comment_form = CommentForm()

    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': comment_form
    })



@login_required
def share_post(request, pk):
    """Gère le partage de posts"""
    post = get_object_or_404(Post, pk=pk)
    # Logique de partage à implémenter
    messages.success(request, 'Post shared successfully!')
    return redirect('posts:post_detail', pk=post.pk)

@login_required
def report_post(request, pk):
    """Gère les signalements de posts"""
    post = get_object_or_404(Post, pk=pk)
    # Logique de signalement à implémenter
    messages.success(request, 'Post reported to administrators.')
    return redirect('posts:post_detail', pk=post.pk)

@login_required
def notifications(request):
    """Affiche les notifications"""
    user_notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')
    return render(request, 'posts/notifications.html', {'notifications': user_notifications})

@login_required
def mark_notification_read(request, notification_id):
    """Marque une notification comme lue"""
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return JsonResponse({'status': 'success'})


@login_required
def feed(request):
    posts = Post.objects.all().prefetch_related('poll_options')
    return render(request, 'feed.html', {'posts': posts})


@require_POST
def add_reaction(request, post_id):
    try:
        post = Post.objects.get(id=post_id)
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type', 'like')
        existing_reaction = Reaction.objects.filter(post=post, user=request.user).first()
        if existing_reaction:
            existing_reaction.delete()
        else:
            Reaction.objects.create(
                post=post,
                user=request.user,
                reaction_type=reaction_type
            )
        return JsonResponse({
            'success': True,
            'total_reactions': post.reactions.count()
        })
    except Post.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Post not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})