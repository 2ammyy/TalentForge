from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Post, Comment, Reaction, Notification
from .forms import PostForm, CommentForm

def post_list(request):
    posts = Post.objects.all().order_by('-created_at')
    return render(request, 'posts/post_list.html', {'posts': posts})


@login_required
def post_create(request):
    # if request.method == 'POST':
    #     form = PostForm(request.POST, request.FILES)
    #     if form.is_valid():
    #         post = form.save(commit=False)
    #         post.author = request.user
    #         post.save()
    #         return redirect('post_list')
    # else:
    #     form = PostForm()
    return render(request, 'posts/post_create.html')


def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    comments = post.comments.all().order_by('-created_at')

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid() and request.user.is_authenticated:
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    post=post,
                    notif_type='comment',
                    message=f"{request.user.username} commented on your post."
                )
            return redirect('post_detail', pk=pk)
    else:
        form = CommentForm()

    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comments,
        'form': form
    })


@login_required
def react_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    reaction, created = Reaction.objects.get_or_create(post=post, user=request.user, defaults={'type': 'like'})
    if not created:
        reaction.delete()  # toggle like
    else:
        if post.author != request.user:
            Notification.objects.create(
                recipient=post.author,
                sender=request.user,
                post=post,
                notif_type='reaction',
                message=f"{request.user.username} liked your post."
            )
    return redirect('post_list')


@login_required
def notifications_list(request):
    notifications = request.user.notifications.order_by('-created_at')
    return render(request, 'posts/notifications.html', {'notifications': notifications})
