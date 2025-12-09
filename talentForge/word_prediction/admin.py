from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from .services import word_prediction_service

class WordPredictionAdmin(admin.ModelAdmin):
    """Admin interface for word prediction"""
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('model-status/', self.admin_site.admin_view(self.model_status)),
            path('test-prediction/', self.admin_site.admin_view(self.test_prediction)),
        ]
        return custom_urls + urls
    
    def model_status(self, request):
        """Check model status in admin"""
        status = word_prediction_service.get_model_status()
        return JsonResponse(status)
    
    def test_prediction(self, request):
        """Test prediction from admin"""
        text = request.GET.get('text', '')
        if text:
            suggestions = word_prediction_service.predict_next_words(text)
            return JsonResponse({'suggestions': suggestions})
        return JsonResponse({'error': 'No text provided'})

# Register if you want an admin page
# admin.site.register(YourModel, WordPredictionAdmin)