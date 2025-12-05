# creator/urls.py
from django.urls import path
from . import views

app_name = 'creator'

urlpatterns = [
    # Dashboard
    path('dashboard/', views.creator_dashboard, name='dashboard'),
    path('analytics/', views.creator_analytics, name='analytics'),
    
    # API Temps Réel
    path('api/stats/', views.api_creator_stats, name='api_stats'),
    
    # Fonctionnalités IA
    path('predict/', views.generate_prediction, name='generate_prediction'),
    
    # Statut Creator
    path('check-eligibility/', views.check_eligibility, name='check_eligibility'),
    path('upgrade/', views.upgrade_to_creator, name='upgrade'),
]