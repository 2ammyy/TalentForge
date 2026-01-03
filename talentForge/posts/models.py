from django.db import models
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

# ============ MODÈLES EXISTANTS ============

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
    
    # Champ pour les rapports de posts
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    
    # NOUVEAUX CHAMPS pour les rapports d'utilisateurs
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_against', null=True, blank=True)
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reason = models.CharField(max_length=20, choices=REPORT_CHOICES)
    
    # Renommez 'description' en 'details' ou gardez 'description'
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
        
        if self.post:
            report_type = "content"
            target = f"Post ID: {self.post.id}"
        else:
            report_type = "user"
            target = f"User: {self.reported_user.username}"
            
        message = f"""
        Dear {self.reporter.username},
        
        Thank you for reporting {report_type} on TalentForge. We have received your report and will review it shortly.
        
        Report Details:
        - {target}
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
                'talentforge.app@gmail.com',
                [self.reporter.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send email: {e}")
    
    def __str__(self):
        if self.post:
            return f"Report #{self.id} - {self.post} by {self.reporter}"
        else:
            return f"Report #{self.id} - {self.reported_user} by {self.reporter}"
    
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
    
    # SUPPRIMEZ cette ligne car nous utilisons maintenant le modèle Follow
    # followers = models.ManyToManyField(User, related_name='following', blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def followers_count(self):
        """Utilise le modèle Follow pour compter les followers"""
        return self.user.user_followers.count()  # user_followers au lieu de followers

    def following_count(self):
        """Utilise le modèle Follow pour compter les suivis"""
        return self.user.user_following.count()  # user_following au lieu de following


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

class Mention(models.Model):
    """Model to track user mentions in posts and comments"""
    post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True, related_name='mentions')
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True, related_name='mentions')
    mentioned_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentions')
    created_at = models.DateTimeField(auto_now_add=True)
    position = models.PositiveIntegerField(help_text="Position in the text where mention occurs", default=0)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Mention"
        verbose_name_plural = "Mentions"
    
    def __str__(self):
        if self.post:
            return f"{self.mentioned_user.username} mentioned in Post #{self.post.id}"
        else:
            return f"{self.mentioned_user.username} mentioned in Comment #{self.comment.id}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('share', 'Share'),
        ('follow', 'Follow'),
        ('view', 'Profile View'),
        ('report', 'Report'),
        ('mention', 'Mention'),
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


# ============ MODÈLES DE RELATIONS SOCIALES ============

class Follow(models.Model):
    """Modèle pour gérer les relations de suivi entre utilisateurs"""
    follower = models.ForeignKey(
        User, 
        related_name='user_following',  # CHANGÉ: related_name unique
        on_delete=models.CASCADE
    )
    following = models.ForeignKey(
        User, 
        related_name='user_followers',  # CHANGÉ: related_name unique
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'following')
        verbose_name = 'Follow'
        verbose_name_plural = 'Follows'
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Block(models.Model):
    """Modèle pour gérer les blocages entre utilisateurs"""
    blocker = models.ForeignKey(
        User, 
        related_name='user_blocking',  # CHANGÉ: related_name unique
        on_delete=models.CASCADE
    )
    blocked = models.ForeignKey(
        User, 
        related_name='user_blocked_by',  # CHANGÉ: related_name unique
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('blocker', 'blocked')
        verbose_name = 'Block'
        verbose_name_plural = 'Blocks'
    
    def __str__(self):
        return f"{self.blocker.username} blocks {self.blocked.username}"


# ============ SIGNALS ============

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


@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    """Créer une notification lorsqu'un utilisateur en suit un autre"""
    if created:
        Notification.objects.create(
            user=instance.following,
            from_user=instance.follower,
            notification_type='follow',
            post=None  # Pas de post associé pour les follows
        )


@receiver(post_save, sender=Block)
def handle_block_actions(sender, instance, created, **kwargs):
    """Gérer les actions lors du blocage d'un utilisateur"""
    if created:
        # Supprimer les relations de suivi réciproques
        Follow.objects.filter(
            follower=instance.blocker, 
            following=instance.blocked
        ).delete()
        Follow.objects.filter(
            follower=instance.blocked, 
            following=instance.blocker
        ).delete()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'posts_profile'):
        instance.posts_profile.save()

# ============ AI CONTENT VALIDATION MODELS ============

class CreativeCategory(models.Model):
    """Dynamic creative categories for AI validation"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    keywords = models.TextField(help_text="Comma-separated keywords for this category")
    is_active = models.BooleanField(default=True)
    weight = models.FloatField(default=1.0, help_text="Importance weight for validation")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Creative Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def keyword_list(self):
        """Convert comma-separated keywords to list"""
        if self.keywords:
            return [k.strip().lower() for k in self.keywords.split(',') if k.strip()]
        return []


class ContentValidationLog(models.Model):
    """Log of content validations"""
    post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True, related_name='validation_logs')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    content_type = models.CharField(max_length=20, choices=Post.POST_TYPES)
    score = models.FloatField()
    is_approved = models.BooleanField(default=False)
    detected_categories = models.JSONField(default=list)
    suggestions = models.JSONField(default=list)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Content Validation Log"
        verbose_name_plural = "Content Validation Logs"
    
    def __str__(self):
        return f"Validation {self.id} - Score: {self.score:.2f}"



class SavedPost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_posts')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saved_by')
    saved_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'post']  # Prevent duplicate saves
        ordering = ['-saved_at']
        
    def __str__(self):
        return f"{self.user.username} saved {self.post.title}"