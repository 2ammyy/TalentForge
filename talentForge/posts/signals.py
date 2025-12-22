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