from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.posts_list, name='posts_list'),
    path('create/', views.post_create, name='post_create'),
    path('<int:pk>/', views.post_detail, name='post_detail'),
    path('reaction/<int:post_id>/', views.add_reaction, name='add_reaction'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('<int:pk>/share/', views.share_post, name='share_post'),
    path('<int:pk>/report/', views.report_post, name='report_post'),  
]
