from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    POST_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('poll', 'Poll'),
        ('job', 'Job Offer'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    type = models.CharField(max_length=10, choices=POST_TYPES, default='text')
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='posts/images/', blank=True, null=True)
    video = models.FileField(upload_to='posts/videos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username} - {self.type}"

    def average_rating(self):
        return self.ratings.aggregate(models.Avg('score'))['score__avg'] or 0


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class Reaction(models.Model):
    REACTIONS = [
        ('like', '👍'),
        ('love', '❤️'),
        ('laugh', '😂'),
        ('sad', '😢'),
        ('angry', '😡'),
    ]
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=REACTIONS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')  # 1 reaction per user/post


class Notification(models.Model):
    NOTIF_TYPES = [
        ('comment', 'Comment'),
        ('reaction', 'Reaction'),
    ]
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    notif_type = models.CharField(max_length=10, choices=NOTIF_TYPES)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"To {self.recipient} - {self.message}"
