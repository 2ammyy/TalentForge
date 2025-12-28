# word_prediction/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('predict/', views.predict_view, name='word_prediction_predict'),
    path('learn/', views.learn_view, name='word_prediction_learn'),
    path('status/', views.status_view, name='word_prediction_status'),
]