from django.urls import path
from .views import authView, home, custom_login, verify_email, CustomPasswordResetView, CustomPasswordResetDoneView, CustomPasswordResetConfirmView, CustomPasswordResetCompleteView
from django.contrib.auth.views import LogoutView

app_name = 'base'

urlpatterns = [
    path('', home, name='home'),
    path('signup/', authView, name='signup'),
    path('verify-email/<str:email>/', verify_email, name='verify_email'),
    path('login/', custom_login, name='login'),
    path('logout/', LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    
    # Password reset URLs
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
]