# word_prediction/views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .services import word_prediction_service
import logging

logger = logging.getLogger(__name__)

@require_http_methods(["GET"])
def predict_view(request):
    """Handle word prediction requests"""
    try:
        text = request.GET.get('text', '').strip()
        num_suggestions = int(request.GET.get('num_suggestions', 3))
        
        if not text:
            return JsonResponse({
                'success': True,
                'suggestions': ['the', 'i', 'you', 'a', 'to'][:num_suggestions]
            })
        
        # Get predictions
        suggestions = word_prediction_service.predict(text, num_suggestions)
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions,
            'original_text': text
        })
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'suggestions': []
        })

@csrf_exempt
@require_http_methods(["POST"])
def learn_view(request):
    """Handle learning from user selections"""
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
        selected = data.get('selected', '').strip()
        
        if text and selected:
            word_prediction_service.feedback_accepted(text, selected)
            logger.info(f"Learned: '{selected}' for context '{text}'")
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Learning error: {e}")
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["GET"])
def status_view(request):
    """Get service status"""
    status = word_prediction_service.get_status()
    return JsonResponse({'success': True, 'status': status})