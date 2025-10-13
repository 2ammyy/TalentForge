from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['type', 'title', 'content', 'image', 'video']
        widgets = {
            'type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'placeholder': 'Enter post title...',
                'class': 'form-control'
            }),
            'content': forms.Textarea(attrs={
                'placeholder': "What's on your mind?",
                'rows': 4,
                'class': 'form-control'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        post_type = cleaned_data.get('type')
        content = cleaned_data.get('content')
        image = cleaned_data.get('image')
        video = cleaned_data.get('video')
        
        # Validation selon le type de post
        if post_type == 'text' and not content:
            raise forms.ValidationError("Text content is required for text posts.")
        elif post_type == 'image' and not image:
            raise forms.ValidationError("Image is required for image posts.")
        elif post_type == 'video' and not video:
            raise forms.ValidationError("Video is required for video posts.")
        
        return cleaned_data

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