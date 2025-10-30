# Dans base/urls.py
from django.urls import path
from .views import authView, home, custom_login, verify_email, edit_profile, view_profile, delete_profile, profile_settings, confirm_delete_profile, resend_delete_code
from django.contrib.auth.views import LogoutView
from .views import social_signup_redirect

app_name = 'base'

urlpatterns = [
    path('', home, name='home'),
    path('signup/', authView, name='signup'),
    path('verify-email/<str:email>/', verify_email, name='verify_email'),
    path('login/', custom_login, name='login'),
    path('logout/', LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    path('profile/edit/', edit_profile, name='edit_profile'),
    path('profile/', view_profile, name='view_profile'),
    path('profile/settings/', profile_settings, name='profile_settings'),
    path('profile/delete/', delete_profile, name='delete_profile'),
    path('profile/delete/confirm/', confirm_delete_profile, name='confirm_delete_profile'),
    path('profile/delete/resend-code/', resend_delete_code, name='resend_delete_code'),  # Nouvelle URL
    
    path('accounts/3rdparty/signup/', social_signup_redirect, name='social_signup_redirect'),
]