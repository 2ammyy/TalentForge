from django.urls import path
from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('create/', views.post_create, name='post_create'),
    path('<int:pk>/', views.post_detail, name='post_detail'),
    path('<int:pk>/react/', views.react_post, name='react_post'),
    path('notifications/', views.notifications, name='notifications'),
    #path('notifications/<int:pk>/clear/', views.clear_notification, name='clear_notification'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('<int:pk>/share/', views.share_post, name='share_post'),
    path('<int:pk>/report/', views.report_post, name='report_post'),    
    #path('<int:pk>/comment/', views.add_comment, name='add_comment'),
    #path('my_posts/', views.user_posts, name='user_posts'),
]
