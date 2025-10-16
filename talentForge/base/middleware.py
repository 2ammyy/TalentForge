from django.shortcuts import redirect
from django.urls import reverse

class SocialSignupRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Si l'utilisateur arrive sur la page 3rdparty/signup et est authentifié
        if request.path == '/accounts/3rdparty/signup/' and request.user.is_authenticated:
            return redirect('base:home')
        
        response = self.get_response(request)
        return response