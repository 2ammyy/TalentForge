from django import forms
from .models import Post, Comment, PollOption, JobPost

class PostForm(forms.ModelForm):
    # Champs pour les polls avec options dynamiques
    poll_question = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control poll-field',
            'placeholder': 'Ask a question...',
            'style': 'display: none;'
        })
    )
    poll_option_1 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control poll-option',
            'placeholder': 'Option 1',
            'style': 'display: none;'
        })
    )
    poll_option_2 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control poll-option',
            'placeholder': 'Option 2',
            'style': 'display: none;'
        })
    )
    poll_option_3 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control poll-option',
            'placeholder': 'Option 3 (optional)',
            'style': 'display: none;'
        })
    )
    poll_option_4 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control poll-option',
            'placeholder': 'Option 4 (optional)',
            'style': 'display: none;'
        })
    )
    poll_duration = forms.ChoiceField(
        required=False,
        choices=[
            ('1', '1 day'),
            ('3', '3 days'),
            ('7', '1 week'),
            ('30', '1 month'),
        ],
        initial='7',
        widget=forms.Select(attrs={
            'class': 'form-control poll-field',
            'style': 'display: none;'
        })
    )
    
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
        
        # Validation pour les polls
        if post_type == 'poll':
            poll_question = cleaned_data.get('poll_question')
            poll_option_1 = cleaned_data.get('poll_option_1')
            poll_option_2 = cleaned_data.get('poll_option_2')
            
            if not poll_question:
                raise forms.ValidationError("Poll question is required.")
            if not poll_option_1 or not poll_option_1.strip():
                raise forms.ValidationError("Option 1 is required and cannot be empty.")
            if not poll_option_2 or not poll_option_2.strip():
                raise forms.ValidationError("Option 2 is required and cannot be empty.")
        
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
        
        # Pour les polls, utiliser la question comme contenu
        if post_type == 'poll':
            poll_question = self.cleaned_data.get('poll_question')
            if poll_question:
                post.content = poll_question
        
        if commit:
            post.save()
            
            # Créer les options du poll - CORRECTION CRITIQUE
            if post_type == 'poll':
                print(f"🎯 Création des options pour: {post.content}")
                
                # Récupérer les options
                options = [
                    self.cleaned_data.get('poll_option_1', ''),
                    self.cleaned_data.get('poll_option_2', ''),
                    self.cleaned_data.get('poll_option_3', ''),
                    self.cleaned_data.get('poll_option_4', ''),
                ]
                
                print(f"🎯 Options brutes: {options}")
                
                # Filtrer les options vides
                valid_options = []
                for opt in options:
                    if opt and opt.strip():  # Vérifier que l'option n'est pas None et pas vide
                        valid_options.append(opt.strip())
                        print(f"   ✅ Option valide: '{opt.strip()}'")
                    else:
                        print(f"   ❌ Option vide ignorée: '{opt}'")
                
                print(f"🎯 Nombre d'options valides: {len(valid_options)}")
                
                # GARANTIR qu'on a au moins 2 options (ne pas lever d'exception)
                if len(valid_options) < 2:
                    print("⚠️ Moins de 2 options valides - utilisation d'options par défaut")
                    valid_options = ["Choice 1", "Choice 2", "Choice 3", "Choice 4"]
                    print(f"🔄 Options par défaut: {valid_options}")
                
                # Créer les options dans la base de données
                for option_text in valid_options:
                    try:
                        PollOption.objects.create(
                            post=post,
                            text=option_text,
                            votes=0
                        )
                        print(f"   ✅ Option créée en base: '{option_text}'")
                    except Exception as e:
                        print(f"   💥 Erreur création option: {e}")
                
                # Vérification finale
                final_count = post.poll_options.count()
                print(f"📊 VÉRIFICATION: {final_count} options créées pour le poll")
                
                # Dernière sécurité si aucune option n'a été créée
                if final_count == 0:
                    print("🚨 CRITIQUE: Aucune option créée - création d'urgence")
                    emergency_options = ["Option A", "Option B", "Option C", "Option D"]
                    for opt in emergency_options:
                        PollOption.objects.create(post=post, text=opt, votes=0)
                        print(f"   🚨 Option d'urgence: '{opt}'")
            
            # Créer les détails de l'offre d'emploi
            elif post_type == 'job':
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


class PollPostForm(forms.ModelForm):
    option_1 = forms.CharField(max_length=200, required=True, label="Option 1")
    option_2 = forms.CharField(max_length=200, required=True, label="Option 2")
    option_3 = forms.CharField(max_length=200, required=False, label="Option 3 (optional)")
    option_4 = forms.CharField(max_length=200, required=False, label="Option 4 (optional)")
    
    class Meta:
        model = Post
        fields = ['content']
    
    def save(self, commit=True):
        post = super().save(commit=False)
        post.type = 'poll'
        
        if commit:
            post.save()
            
            # Créer les options
            options = [
                self.cleaned_data['option_1'],
                self.cleaned_data['option_2'],
            ]
            
            if self.cleaned_data.get('option_3'):
                options.append(self.cleaned_data['option_3'])
            if self.cleaned_data.get('option_4'):
                options.append(self.cleaned_data['option_4'])
            
            for option_text in options:
                PollOption.objects.create(
                    post=post,
                    text=option_text,
                    votes=0
                )
        
        return post