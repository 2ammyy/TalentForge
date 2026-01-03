from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    # ============ POSTS URLs ============
    path('', views.post_list, name='post_list'),
    path('create/', views.post_create, name='post_create'),
    path('<int:pk>/', views.post_detail, name='post_detail'),
    path('<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('<int:pk>/update/', views.post_update, name='post_update'),
    path('<int:pk>/delete/', views.post_delete, name='post_delete'),
    # Content validation API
    path('check-creative-content/', views.check_creative_content, name='check_creative_content'),

    # ============ REACTIONS & INTERACTIONS ============
    path('reaction/<int:post_id>/', views.add_reaction, name='add_reaction'),
    path('share/<int:post_id>/', views.share_post, name='share_post'),
    path('unshare/<int:post_id>/', views.unshare_post, name='unshare_post'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    # ============ REPORTS ============
    path('report/<int:post_id>/', views.report_post, name='report_post'),
    path('my-reports/', views.my_reports, name='my_reports'),

    # ============ PROFILES ============
    path('profile/', views.my_profile, name='my_profile'),  # Own profile
    path('profile/<str:username>/', views.user_profile, name='user_profile'),  # Other users
    path('profile/edit/', views.edit_profile, name='edit_profile'),  # AJOUTÉ: Edit profile

    # ============ SOCIAL ACTIONS ============
    path('follow/<str:username>/', views.follow_user, name='follow_user'),
    path('unfollow/<str:username>/', views.unfollow_user, name='unfollow_user'),
    path('block/<str:username>/', views.block_user, name='block_user'),
    path('unblock/<str:username>/', views.unblock_user, name='unblock_user'),
    path('report-user/<str:username>/', views.report_user, name='report_user'),

    # ============ SEARCH ============
    path('search/', views.search_view, name='search'),

    # ============ MESSAGING ============
    path('messages/', views.messages_view, name='messages'),
    path('messages/<str:username>/', views.conversation_view, name='conversation'),

    # ============ NOTIFICATIONS ============
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/clear-all/', views.clear_all_notifications, name='clear_all_notifications'),


    # ============ API ENDPOINTS ============
    path('api/unread-counts/', views.get_unread_counts, name='unread_counts'),

    # ============ UTILITY ============
    path('test-email/', views.test_email_view, name='test_email'),
    path('feed/', views.feed, name='feed'),

    path('check-toxicity/', views.check_toxicity_api, name='check_toxicity_api'),

    path('notifications/mark-read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/clear-all/', views.clear_all_notifications, name='clear_all_notifications'),

    # ============ SAVED/UNSAVED POSTS ============
    path('save/<int:post_id>/', views.save_post, name='save_post'),
    path('unsave/<int:post_id>/', views.unsave_post, name='unsave_post'),
    path('saved/', views.saved_posts_view, name='saved_posts'),
]