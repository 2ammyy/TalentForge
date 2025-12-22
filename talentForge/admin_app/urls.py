from django.urls import path
from . import views

app_name = 'admin_app'

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='dashboard'),
    
    # User Management
    path('users/', views.user_management, name='users'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/toggle-active/', views.toggle_user_active, name='toggle_user_active'),
    path('users/<int:user_id>/make-staff/', views.make_user_staff, name='make_user_staff'),
    
    # Placeholder pages (coming soon)
    path('creators/', views.placeholder_page, {'page_name': 'creators'}, name='creators'),
    path('moderation/', views.placeholder_page, {'page_name': 'moderation'}, name='moderation'),
    path('analytics/', views.placeholder_page, {'page_name': 'analytics'}, name='analytics'),
    path('reports/', views.placeholder_page, {'page_name': 'reports'}, name='reports'),
    path('settings/', views.placeholder_page, {'page_name': 'settings'}, name='settings'),
    
    # API Endpoints
    path('api/stats/', views.api_stats, name='api_stats'),
    
    # Export
    path('export-users/', views.export_users_csv, name='export_users'),
   # AI Content Validation
   #path('validation/', views.validation_analytics, name='validation_dashboard'),
    #path('validation/', views_ai_validation.validation_dashboard, name='validation_dashboard'),
    # path('validation/categories/', views_ai_validation.creative_categories, name='creative_categories'),
    # path('validation/logs/', views_ai_validation.validation_logs, name='validation_logs'),
    # path('validation/settings/', views_ai_validation.validation_settings, name='validation_settings'),
    # path('validation/manual/<int:post_id>/', views_ai_validation.manual_validation, name='manual_validation'),
    # path('validation/test/', views_ai_validation.test_validation, name='test_validation'),
    # path('validation/api/stats/', views_ai_validation.api_validation_stats, name='validation_api_stats'),

]