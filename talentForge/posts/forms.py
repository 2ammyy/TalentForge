# talentForge/posts/forms.py - CORRECTED VERSION
from django import forms
from django.contrib.auth.models import User  # CORRECT IMPORT
from django.core.validators import validate_email
from utils.content_validator import validate_content
import re
from .models import Post, Comment, JobPost, Share, Report, UserProfile, Message, Mention, Notification


class PostForm(forms.ModelForm):
    # Job-specific fields
    company = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control job-field',
            'placeholder': 'Company name',
            'style': 'display: none;'
        })
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control job-field',
            'placeholder': 'City, Country',
            'style': 'display: none;'
        })
    )
    work_mode = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Select work mode'),
            ('onsite', '🏢 On-site'),
            ('remote', '🏠 Remote'),
            ('hybrid', '🔀 Hybrid'),
            ('flexible', '⚡ Flexible'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control job-field',
            'style': 'display: none;'
        })
    )
    employment_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Select employment type'),
            ('full_time', '🕒 Full-time'),
            ('part_time', '⏰ Part-time'),
            ('contract', '📝 Contract'),
            ('internship', '🎓 Internship'),
            ('freelance', '💼 Freelance'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control job-field',
            'style': 'display: none;'
        })
    )
    salary_range = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Select salary range'),
            ('0-30k', '$0 - $30,000'),
            ('30k-50k', '$30,000 - $50,000'),
            ('50k-80k', '$50,000 - $80,000'),
            ('80k-120k', '$80,000 - $120,000'),
            ('120k+', '$120,000+'),
            ('negotiable', '💵 Negotiable'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-control job-field',
            'style': 'display: none;'
        })
    )
    application_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control job-field',
            'placeholder': 'application@company.com',
            'style': 'display: none;'
        })
    )
    skills_required = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control job-field',
            'placeholder': 'Required skills (one per line)...',
            'rows': 3,
            'style': 'display: none;'
        })
    )
    benefits = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control job-field',
            'placeholder': 'Company benefits...',
            'rows': 2,
            'style': 'display: none;'
        })
    )

    class Meta:
        model = Post
        fields = ['type', 'title', 'content', 'image', 'video']
        widgets = {
            'type': forms.HiddenInput(),
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter post title...',
                'class': 'form-control'
            }),
            'content': forms.Textarea(attrs={
                'placeholder': "What's on your mind? Use @ to mention someone...",
                'rows': 4,
                'class': 'form-control',
                'id': 'post-content'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial values for job fields if editing a job post
        if self.instance and self.instance.type == 'job' and hasattr(self.instance, 'job_details'):
            job_details = self.instance.job_details
            self.fields['company'].initial = job_details.company
            self.fields['location'].initial = job_details.location
            self.fields['work_mode'].initial = job_details.work_mode
            self.fields['employment_type'].initial = job_details.employment_type
            self.fields['salary_range'].initial = job_details.salary_range
            self.fields['application_email'].initial = job_details.application_email
            self.fields['skills_required'].initial = job_details.skills_required
            self.fields['benefits'].initial = job_details.benefits
    
    def clean(self):
        cleaned_data = super().clean()
        post_type = cleaned_data.get('type')
        image = cleaned_data.get('image')
        video = cleaned_data.get('video')
        
        # AUTO-DETECT POST TYPE BASED ON CONTENT
        if not post_type or post_type == 'text':
            if image:
                cleaned_data['type'] = 'image'
            elif video:
                cleaned_data['type'] = 'video'
        
        # Validation for job posts
        if post_type == 'job' or cleaned_data.get('type') == 'job':
            company = cleaned_data.get('company')
            location = cleaned_data.get('location')
            
            if not company:
                self.add_error('company', 'Company name is required for job posts.')
            if not location:
                self.add_error('location', 'Location is required for job posts.')
            if not cleaned_data.get('title'):
                self.add_error('title', 'Job title is required.')
            if not cleaned_data.get('content'):
                self.add_error('content', 'Job description is required.')
            
            # Validate application email
            application_email = cleaned_data.get('application_email')
            if application_email:
                try:
                    validate_email(application_email)
                except:
                    self.add_error('application_email', 'Enter a valid email address.')
        
        # ============ ADD AI CONTENT VALIDATION ============
        try:
            # Prepare data for validation
            validation_data = {
                'type': cleaned_data.get('type', 'text'),
                'title': cleaned_data.get('title', ''),
                'content': cleaned_data.get('content', ''),
                'image': cleaned_data.get('image'),
                'video': cleaned_data.get('video'),
            }
            
            # Add job fields if it's a job post
            if cleaned_data.get('type') == 'job':
                validation_data['job_fields'] = {
                    'company': cleaned_data.get('company', ''),
                    'location': cleaned_data.get('location', ''),
                    'skills_required': cleaned_data.get('skills_required', ''),
                    'employment_type': cleaned_data.get('employment_type', ''),
                }
            
            # Validate content
            validation_result = validate_content(validation_data)
            
            if not validation_result['is_valid']:
                # Store validation result in cleaned_data for template access
                cleaned_data['validation_result'] = validation_result
                
                # Create a user-friendly error message
                error_msg = (
                    f"🚫 Content not suitable for our creative community.\n"
                    f"Reason: {validation_result['reason']}\n"
                    f"Score: {validation_result['score']:.0%}\n\n"
                )
                
                if validation_result['suggestions']:
                    error_msg += "Suggestions:\n" + "\n".join(
                        f"• {suggestion}" 
                        for suggestion in validation_result['suggestions']
                    )
                
                # Add error to the form
                self.add_error(
                    None,  # Non-field error
                    forms.ValidationError(error_msg)
                )
            
            # Store validation result for template even if valid
            cleaned_data['validation_result'] = validation_result
            
        except Exception as e:
            # If validation fails, log but don't block posting
            print(f"Content validation error: {e}")
        
        return cleaned_data
    
    def save(self, commit=True):
        post = super().save(commit=False)
        post_type = self.cleaned_data.get('type')
        
        # Store validation result in post metadata if available
        if 'validation_result' in self.cleaned_data:
            # You might want to store this in a JSONField or similar
            pass
        
        if commit:
            post.save()
            
            # Process mentions after saving the post
            content = self.cleaned_data.get('content', '')
            if content:
                self.process_mentions(post, content)
            
            # Create JobPost if it's a job post
            if post_type == 'job':
                job_data = {
                    'company': self.cleaned_data.get('company'),
                    'location': self.cleaned_data.get('location'),
                    'work_mode': self.cleaned_data.get('work_mode') or 'onsite',
                    'employment_type': self.cleaned_data.get('employment_type') or 'full_time',
                    'salary_range': self.cleaned_data.get('salary_range'),
                    'application_email': self.cleaned_data.get('application_email'),
                    'skills_required': self.cleaned_data.get('skills_required'),
                    'benefits': self.cleaned_data.get('benefits'),
                }
                
                if hasattr(post, 'job_details'):
                    # Update existing JobPost
                    for key, value in job_data.items():
                        setattr(post.job_details, key, value)
                    post.job_details.save()
                else:
                    # Create new JobPost
                    JobPost.objects.create(post=post, **job_data)
        
        return post
    
    def process_mentions(self, post, content):
        """Extract mentions from content and create Mention objects"""
        # Find all @username patterns
        mention_pattern = r'@([a-zA-Z0-9_]+)'
        mentions = re.findall(mention_pattern, content)
        
        for username in set(mentions):  # Use set to avoid duplicates
            try:
                user = User.objects.get(username=username)
                # Don't create mention if it's the author mentioning themselves
                if user != post.author:
                    Mention.objects.create(
                        post=post,
                        mentioned_user=user,
                        position=content.find(f"@{username}")
                    )
                    
                    # Create notification
                    Notification.objects.create(
                        user=user,
                        from_user=post.author,
                        notification_type='mention',
                        post=post
                    )
            except User.DoesNotExist:
                continue


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'placeholder': 'Write a comment... (use @ to mention someone)',
                'rows': 2,
                'class': 'form-control',
                'id': 'comment-text'
            }),
        }
    
    def save(self, commit=True, post=None, author=None):
        comment = super().save(commit=False)
        
        if post:
            comment.post = post
        if author:
            comment.author = author
        
        if commit:
            comment.save()
            
            # Process mentions
            content = self.cleaned_data.get('text', '')
            if content:
                self.process_mentions(comment, content)
        
        return comment
    
    def process_mentions(self, comment, content):
        """Extract mentions from comment and create Mention objects"""
        mention_pattern = r'@([a-zA-Z0-9_]+)'
        mentions = re.findall(mention_pattern, content)
        
        for username in set(mentions):
            try:
                user = User.objects.get(username=username)
                # Don't create mention if it's the author mentioning themselves
                if user != comment.author:
                    Mention.objects.create(
                        comment=comment,
                        mentioned_user=user,
                        position=content.find(f"@{username}")
                    )
                    
                    # Create notification
                    Notification.objects.create(
                        user=user,
                        from_user=comment.author,
                        notification_type='mention',
                        post=comment.post
                    )
            except User.DoesNotExist:
                continue


class ShareForm(forms.ModelForm):
    class Meta:
        model = Share
        fields = ['caption']
        widgets = {
            'caption': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Add a comment...',
                'rows': 3
            }),
        }
        labels = {
            'caption': 'Your comment'
        }


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['reason', 'description']
        widgets = {
            'reason': forms.Select(attrs={
                'class': 'form-control',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please provide additional details...'
            }),
        }
        labels = {
            'reason': 'Reason for Reporting',
            'description': 'Additional Details (Optional)',
        }


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['bio', 'location', 'birth_date', 'profile_picture', 'website', 'github', 'linkedin']


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Type your message here...',
                'class': 'form-control'
            })
        }


class SearchForm(forms.Form):
    q = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'Search profiles...',
            'class': 'search-input'
        })
    )