from django.urls import path
from . import views

urlpatterns = [
    path('predict/', views.predict_word, name='predict_word'),
    path('feedback/', views.feedback, name='feedback'),
    path('status/', views.status, name='status'),
    path('test/', views.test_creative, name='test'),
]