from django.urls import path
from . import views_ai_validation
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
    
    #  Creator Management (ACTUAL IMPLEMENTATION)
    path('creators/', views.creator_management, name='creators'),
    path('creators/<int:creator_id>/', views.creator_detail, name='creator_detail'),
    path('creators/<int:creator_id>/verify/', views.verify_creator, name='verify_creator'),
    path('creators/<int:creator_id>/stats/', views.creator_stats, name='creator_stats'),

    #  Content Moderation (ACTUAL IMPLEMENTATION)
    path('moderation/', views.content_moderation, name='moderation'),
    path('moderation/posts/', views.post_moderation, name='post_moderation'),
    path('moderation/posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('moderation/posts/<int:post_id>/approve/', views.approve_post, name='approve_post'),
    path('moderation/posts/<int:post_id>/reject/', views.reject_post, name='reject_post'),
    path('moderation/posts/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    
    #  Reports (ACTUAL IMPLEMENTATION)
    path('reports/', views.reports_dashboard, name='reports'),
    path('reports/users/', views.user_reports, name='user_reports'),
    path('reports/content/', views.content_reports, name='content_reports'),
    path('reports/analytics/', views.analytics_reports, name='analytics_reports'),
    
    #  Analytics (ACTUAL IMPLEMENTATION)
    path('analytics/', views.site_analytics, name='analytics'),  # Make sure this exists
    path('analytics/users/', views.user_analytics, name='user_analytics'),
    path('analytics/content/', views.content_analytics, name='content_analytics'),
    path('analytics/engagement/', views.engagement_analytics, name='engagement_analytics'),
    
    #  Settings (ACTUAL IMPLEMENTATION)
    path('settings/', views.admin_settings, name='settings'),
    path('settings/general/', views.general_settings, name='general_settings'),
    path('settings/email/', views.email_settings, name='email_settings'),
    path('settings/ai/', views.ai_settings, name='ai_settings'),
path('settings/test-email/', views.test_email_connection, name='test_email_connection'),
    
    # Bulk Actions
    path('bulk/export-users/', views.export_users_csv, name='export_users'),
    path('bulk/send-notification/', views.bulk_send_notification, name='bulk_notification'),
    path('bulk/cleanup-inactive/', views.cleanup_inactive_users, name='cleanup_inactive'),

  
    # API Endpoints
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/activity/', views.api_recent_activity, name='api_activity'),
    path('api/chart-data/', views.api_chart_data, name='api_chart_data'),
    
    # Export
    path('export-users/', views.export_users_csv, name='export_users'),
   
    # AI Validation URLs
    path('ai-validation/', views_ai_validation.validation_dashboard, name='validation_dashboard'),
    path('ai-validation/categories/', views_ai_validation.creative_categories, name='creative_categories'),
    path('ai-validation/logs/', views_ai_validation.validation_logs, name='validation_logs'),
    path('ai-validation/settings/', views_ai_validation.validation_settings, name='validation_settings'),
    path('ai-validation/test/', views_ai_validation.test_validation, name='test_validation'),
    path('ai-validation/manual/<int:post_id>/', views_ai_validation.manual_validation, name='manual_validation'),
    path('ai-validation/overview/', views_ai_validation.validation_overview, name='validation_overview'),
    path('ai-validation/api/stats/', views_ai_validation.api_validation_stats, name='api_validation_stats'),
]