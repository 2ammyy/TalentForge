from django.urls import path
from .views import authView, home, custom_login, verify_email, edit_profile, view_profile
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
    path('accounts/3rdparty/signup/', social_signup_redirect, name='social_signup_redirect'),
]