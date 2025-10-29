from django.db import models
from django.contrib.auth.models import User

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

    def __str__(self):
        return f"{self.author.username} - {self.type}"

    def average_rating(self):
        return self.ratings.aggregate(models.Avg('score'))['score__avg'] or 0
        # Champ pour le post original si c'est un partage
    shared_post = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='shares')

    def __str__(self):
        return f"{self.author.username} - {self.type}"

    def average_rating(self):
        return self.ratings.aggregate(models.Avg('score'))['score__avg'] or 0

    @property
    def share_count(self):
        """Retourne le nombre de fois que ce post a été partagé"""
        return self.shares.count()


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
    reaction_type = models.CharField(max_length=10, choices=REACTIONS)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'user')  # 1 reaction per user/post



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