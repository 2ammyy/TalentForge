from .models import Message, Notification

def unread_counts(request):
    if request.user.is_authenticated:
        return {
            'unread_messages_count': Message.objects.filter(receiver=request.user, is_read=False).count(),
            'unread_notifications_count': Notification.objects.filter(user=request.user, is_read=False).count(),
        }
    return {
        'unread_messages_count': 0,
        'unread_notifications_count': 0,
    }