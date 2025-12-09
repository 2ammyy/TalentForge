from django.urls import path
from . import views

urlpatterns = [
    path('predict/', views.predict, name='predict'),
    path('status/', views.status, name='status'),
    path('test/', views.test, name='test'),
]