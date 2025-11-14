from django import forms
from .models import Post, Comment, JobPost , Share,Report

class PostForm(forms.ModelForm):
    
    # Champs pour les offres d'emploi
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
            'type': forms.Select(attrs={
                'class': 'form-control',
                'id': 'post-type-select'
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter post title...',
                'class': 'form-control'
            }),
            'content': forms.Textarea(attrs={
                'placeholder': "What's on your mind?",
                'rows': 4,
                'class': 'form-control',
                'id': 'post-content'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        post_type = cleaned_data.get('type')
        
        # CORRECTION CRITIQUE : Gérer les valeurs multiples pour title et content
        if 'title' in self.data:
            title_values = self.data.getlist('title')
            if title_values:
                # Prendre la première valeur non vide
                for value in title_values:
                    if value and value.strip():  # Prendre la première valeur non vide
                        cleaned_data['title'] = value
                        break
                else:
                    cleaned_data['title'] = ''  # Toutes les valeurs sont vides
        
        if 'content' in self.data:
            content_values = self.data.getlist('content')
            if content_values:
                # Prendre la première valeur non vide
                for value in content_values:
                    if value and value.strip():  # Prendre la première valeur non vide
                        cleaned_data['content'] = value
                        break
                else:
                    cleaned_data['content'] = ''  # Toutes les valeurs sont vides
        
        # Récupérer les valeurs corrigées
        content = cleaned_data.get('content')
        image = cleaned_data.get('image')
        video = cleaned_data.get('video')
        
        # Validation de base selon le type de post
        if post_type == 'text' and not content:
            raise forms.ValidationError("Text content is required for text posts.")
        elif post_type == 'image' and not image:
            raise forms.ValidationError("Image is required for image posts.")
        elif post_type == 'video' and not video:
            raise forms.ValidationError("Video is required for video posts.")
        
        # Validation pour les offres d'emploi
        elif post_type == 'job':
            company = cleaned_data.get('company')
            location = cleaned_data.get('location')
            
            if not company:
                raise forms.ValidationError("Company name is required.")
            if not location:
                raise forms.ValidationError("Location is required.")
            if not cleaned_data.get('title'):
                raise forms.ValidationError("Job title is required.")
        
        return cleaned_data
    
    def save(self, commit=True):
        post = super().save(commit=False)
        post_type = self.cleaned_data.get('type')
        
        if commit:
            post.save()
            
            # Créer les détails de l'offre d'emploi
            if post_type == 'job':
                JobPost.objects.create(
                    post=post,
                    company=self.cleaned_data.get('company'),
                    location=self.cleaned_data.get('location'),
                    work_mode=self.cleaned_data.get('work_mode'),
                    employment_type=self.cleaned_data.get('employment_type'),
                    salary_range=self.cleaned_data.get('salary_range'),
                    application_email=self.cleaned_data.get('application_email'),
                    skills_required=self.cleaned_data.get('skills_required'),
                    benefits=self.cleaned_data.get('benefits')
                )
        
        return post


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'placeholder': 'Write a comment...',
                'rows': 2,
                'class': 'form-control'
            }),
        }

class ShareForm(forms.ModelForm):
    class Meta:
        model = Share
        fields = ['caption']
        widgets = {
            'caption': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Ajouter un commentaire...',
                'rows': 3
            }),
        }
        labels = {
            'caption': 'Votre commentaire'
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
                'placeholder': 'Please provide additional details about why you are reporting this post...'
            }),
        }
        labels = {
            'reason': 'Reason for Reporting',
            'description': 'Additional Details (Optional)',
        }

