from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse 
from .models import Post, Comment, Reaction  , JobPost , Share  ,Report
from .forms import PostForm, CommentForm , ShareForm , ReportForm
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
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
            else:
                # Créer un nouveau partage
                share = form.save(commit=False)
                share.post = post
                share.user = request.user
                share.save()
                
                # # Créer une notification pour l'auteur du post
                # if post.author != request.user:
                #     Notifications.objects.create(
                #         recipient=post.author,
                #         sender=request.user,
                #         post=post,
                #         notif_type='share',
                #         message=f"{request.user.username} a partagé votre post"
                #     )
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'share_count': post.post_shares.count()})
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
        return JsonResponse({'success': True, 'share_count': post.post_shares.count()})
    return redirect('posts:posts_list')

# @login_required
# def notifications(request):
#     """Affiche les notifications - version simplifiée"""
#     user_notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')
#     return render(request, 'posts/notifications.html', {'notifications': user_notifications})

# @login_required
# def mark_notification_read(request, notification_id):
#     """Marque une notification comme lue"""
#     notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
#     notification.is_read = True
#     notification.save()
#     return JsonResponse({'status': 'success'})
#     return redirect('posts:notifications')

@login_required
def notifications(request):
    """Vue simple pour les notifications"""
    return render(request, 'posts/notifications.html', {
        'notifications': []
    })


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
    reports = Report.objects.filter(reporter=request.user).select_related('post')
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