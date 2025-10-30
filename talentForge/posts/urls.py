from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.posts_list, name='post_list'),
    path('create/', views.post_create, name='post_create'),
    path('<int:pk>/', views.post_detail, name='post_detail'),
    path('reaction/<int:post_id>/', views.add_reaction, name='add_reaction'),
    path('share/<int:post_id>/', views.share_post, name='share_post'),
    path('unshare/<int:post_id>/', views.unshare_post, name='unshare_post'),
    # path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/', views.notifications, name='notifications'),
    path('report/<int:post_id>/', views.report_post, name='report_post'),
    path('my-reports/', views.my_reports, name='my_reports'),
]
