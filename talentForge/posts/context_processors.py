from .models import Message, Notification

# def unread_counts(request):
#     if request.user.is_authenticated:
#         return {
#             'unread_messages_count': Message.objects.filter(receiver=request.user, is_read=False).count(),
#             'unread_notifications_count': Notification.objects.filter(user=request.user, is_read=False).count(),
#         }
#     return {
#         'unread_messages_count': 0,
#         'unread_notifications_count': 0,
#     }

def notifications_context(request):
    """
    Context processor to add unread notifications count to all templates
    """
    context = {}
    
    if request.user.is_authenticated:
        try:
            unread_count = Notification.objects.filter(
                user=request.user,
                is_read=False
            ).count()
            context['unread_notifications_count'] = unread_count
        except Exception as e:
            print(f"Error getting notifications: {e}")
            context['unread_notifications_count'] = 0
    else:
        context['unread_notifications_count'] = 0
    
    return context