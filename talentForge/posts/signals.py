"""
Signals for content validation logging
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

@receiver(post_save, sender='posts.Post')
def log_content_validation_on_post_save(sender, instance, created, **kwargs):
    """
    Log content validation when post is created or updated
    """
    try:
        # Import here to avoid circular imports
        from utils.content_validator import validate_content
        from .models import ContentValidationLog
        
        # Only validate on creation
        if created:
            try:
                # Prepare validation data
                validation_data = {
                    'type': instance.type,
                    'title': instance.title or '',
                    'content': instance.content or '',
                }
                
                # Add job fields if job post
                if instance.type == 'job' and hasattr(instance, 'job_details'):
                    validation_data['job_fields'] = {
                        'company': instance.job_details.company,
                        'location': instance.job_details.location,
                        'skills_required': instance.job_details.skills_required or '',
                    }
                
                # Run validation
                result = validate_content(validation_data)
                
                # Create validation log
                ContentValidationLog.objects.create(
                    post=instance,
                    user=instance.author,
                    content_type=instance.type,
                    score=result['score'],
                    is_approved=result['is_valid'],
                    detected_categories=result.get('detected_categories', []),
                    suggestions=result.get('suggestions', []),
                    notes=f"Auto-validated on {timezone.now().strftime('%Y-%m-%d %H:%M')}"
                )
                
                print(f"✅ Validation logged for post {instance.id} - Score: {result['score']:.2f}")
                
            except Exception as e:
                print(f"❌ Error logging validation for post {instance.id}: {e}")
    except ImportError as e:
        print(f"❌ Could not import validation module: {e}")
# talentForge/posts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Post, Mention, Notification
import re
from django.contrib.auth.models import User

@receiver(post_save, sender=Post)
def process_post_mentions(sender, instance, created, **kwargs):
    """Process mentions when a post is created or updated"""
    if created or instance.content:  # Only process if new or content exists
        print(f"DEBUG: Processing mentions for post {instance.id} (created: {created})")
        
        # Find all @username patterns
        mention_pattern = r'@([a-zA-Z0-9_]+)'
        mentions = re.findall(mention_pattern, instance.content or '')
        
        for username in set(mentions):  # Use set to avoid duplicates
            try:
                user = User.objects.get(username=username)
                # Don't create mention if it's the author mentioning themselves
                if user != instance.author:
                    # Check if mention already exists
                    existing_mention = Mention.objects.filter(
                        post=instance,
                        mentioned_user=user
                    ).first()
                    
                    if not existing_mention:
                        # Create mention
                        Mention.objects.create(
                            post=instance,
                            mentioned_user=user,
                            position=(instance.content or '').find(f"@{username}")
                        )
                        
                        # Create notification
                        Notification.objects.create(
                            user=user,
                            from_user=instance.author,
                            notification_type='mention',
                            post=instance
                        )
                        print(f"DEBUG: Created mention notification for {username}")
                        
            except User.DoesNotExist:
                continue
            except Exception as e:
                print(f"ERROR: Failed to process mention for {username}: {e}")