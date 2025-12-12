from django.contrib import messages
from django.shortcuts import redirect

def admin_required(view_func):
    """Decorator to require admin access"""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            from django.urls import reverse
            return redirect_to_login(reverse('admin_app:dashboard'))
        
        # Check if user is staff OR superuser
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, "❌ Admin access required. You need staff permissions.")
            return redirect('base:home')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view