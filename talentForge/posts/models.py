from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

class Post(models.Model):
    POST_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('job', 'Job Offer'),
    ]

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    type = models.CharField(max_length=10, choices=POST_TYPES)
    title = models.CharField(max_length=200, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='posts/images/', blank=True, null=True)
    video = models.FileField(upload_to='posts/videos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Champ pour le post original si c'est un partage (corrigé - un seul champ)
    shared_post = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='shares')

    def __str__(self):
        return f"{self.author.username} - {self.type}"

    def average_rating(self):
        return self.ratings.aggregate(models.Avg('score'))['score__avg'] or 0

    @property
    def share_count(self):
        """Retourne le nombre de fois que ce post a été partagé"""
        return self.shares.count()

    @property
    def like_count(self):
        """Retourne le nombre de likes"""
        return self.reactions.count()


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post}"


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
    reaction_type = models.CharField(max_length=10, choices=REACTIONS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')  # 1 reaction per user/post

    def __str__(self):
        return f"{self.user.username} - {self.reaction_type} on {self.post.id}"


class JobPost(models.Model):
    WORK_MODES = [
        ('onsite', 'On-site'),
        ('remote', 'Remote'),
        ('hybrid', 'Hybrid'),
        ('flexible', 'Flexible'),
    ]
    
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full-time'),
        ('part_time', 'Part-time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('freelance', 'Freelance'),
    ]
    
    SALARY_RANGES = [
        ('0-30k', '$0 - $30,000'),
        ('30k-50k', '$30,000 - $50,000'),
        ('50k-80k', '$50,000 - $80,000'),
        ('80k-120k', '$80,000 - $120,000'),
        ('120k+', '$120,000+'),
        ('negotiable', 'Negotiable'),
    ]
    
    post = models.OneToOneField(Post, on_delete=models.CASCADE, related_name='job_details')
    company = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    work_mode = models.CharField(max_length=20, choices=WORK_MODES, default='onsite')
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='full_time')
    salary_range = models.CharField(max_length=20, choices=SALARY_RANGES, blank=True, null=True)
    application_email = models.EmailField(blank=True, null=True)
    skills_required = models.TextField(blank=True, null=True)
    benefits = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Job at {self.company} - {self.post.title}"

    @property
    def skills_list(self):
        """Retourne la liste des compétences"""
        if self.skills_required:
            return [skill.strip() for skill in self.skills_required.split('\n') if skill.strip()]
        return []

    class Meta:
        ordering = ['-created_at']


class Share(models.Model):
    """Modèle spécifique pour gérer les partages avec caption"""
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='post_shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shares')
    caption = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')  # 1 partage par user/post

    def __str__(self):
        return f"{self.user.username} shared {self.post.id}"


class Report(models.Model):
    REPORT_CHOICES = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('violence', 'Violence'),
        ('hate_speech', 'Hate Speech'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reason = models.CharField(max_length=20, choices=REPORT_CHOICES)
    description = models.TextField(blank=True, null=True, help_text="Additional details about the report")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        is_new = self.pk is None
        print(f"🔍 DEBUG: Saving Report - is_new: {is_new}, Reporter: {self.reporter.username}")
        super().save(*args, **kwargs)
        
        # Send email only for new reports
        if is_new:
            self.send_confirmation_email()
        else:
            print("ℹ️ DEBUG: Report updated, no email sent")

    def send_confirmation_email(self):
        subject = "Report Confirmation - TalentForge"
        message = f"""
        Dear {self.reporter.username},
        
        Thank you for reporting content on TalentForge. We have received your report and will review it shortly.
        
        Report Details:
        - Post ID: {self.post.id}
        - Reason: {self.get_reason_display()}
        - Date: {self.created_at.strftime('%Y-%m-%d %H:%M')}
        - Status: {self.get_status_display()}
        
        We take all reports seriously and will investigate this matter. You will be notified once we've taken action.
        
        Thank you for helping us keep TalentForge a safe and professional community.
        
        Best regards,
        TalentForge Team
        """
        
        try:
            send_mail(
                subject,
                message,
                'talentforge.app@gmail.com',  # From email
                [self.reporter.email],        # To email
                fail_silently=False,
            )
        except Exception as e:
            # Log the error but don't break the report creation
            print(f"Failed to send email: {e}")
    
    def __str__(self):
        return f"Report #{self.id} - {self.post} by {self.reporter}"
    
    class Meta:
        ordering = ['-created_at']


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='posts_profile')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)
    website = models.URLField(blank=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    followers = models.ManyToManyField(User, related_name='following', blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def followers_count(self):
        return self.followers.count()
    
    def following_count(self):
        return self.user.following.count()


class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"From {self.sender} to {self.receiver}"


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('follow', 'Follow'),
        ('view', 'Profile View'),
        ('report', 'Report'),
    )
    
    user = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    from_user = models.ForeignKey(User, related_name='sent_notifications', on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.from_user.username} {self.get_notification_type_display()}"


# Signals pour les notifications automatiques
@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    if created and instance.author != instance.post.author:
        Notification.objects.create(
            user=instance.post.author,
            from_user=instance.author,
            notification_type='comment',
            post=instance.post
        )


@receiver(post_save, sender=Reaction)
def create_reaction_notification(sender, instance, created, **kwargs):
    if created and instance.user != instance.post.author:
        Notification.objects.create(
            user=instance.post.author,
            from_user=instance.user,
            notification_type='like',
            post=instance.post
        )


@receiver(post_save, sender=Share)
def create_share_notification(sender, instance, created, **kwargs):
    if created and instance.user != instance.post.author:
        Notification.objects.create(
            user=instance.post.author,
            from_user=instance.user,
            notification_type='share',
            post=instance.post
        )


@receiver(post_save, sender=Report)
def create_report_notification(sender, instance, created, **kwargs):
    if created:
        # Notification pour l'admin (vous pouvez ajuster selon vos besoins)
        admin_users = User.objects.filter(is_staff=True)
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                from_user=instance.reporter,
                notification_type='report',
                post=instance.post
            )


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()