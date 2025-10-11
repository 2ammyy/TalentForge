from django.urls import path
from .views import authView, home, custom_login
from django.contrib.auth.views import LogoutView

app_name = 'base'

urlpatterns = [
    path('', home, name='home'),
    path('signup/', authView, name='signup'),
    # Use custom login view instead of Django's default
    path('login/', custom_login, name='login'),
    # Use Django's logout view but specify redirect URL
    path('logout/', LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
]