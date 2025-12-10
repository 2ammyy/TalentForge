from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
from .services import word_prediction_service

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET", "POST"])  # Allow both GET and POST
def predict(request):
    """API endpoint for word prediction"""
    try:
        if request.method == 'GET':
            # Handle GET requests (from your JavaScript)
            text = request.GET.get('text', '').strip()
            num_suggestions = min(int(request.GET.get('num_suggestions', 3)), 5)
        else:
            # Handle POST requests (with JSON body)
            data = json.loads(request.body)
            text = data.get('text', '').strip()
            num_suggestions = min(int(data.get('num', 3)), 5)
        
        if not text or len(text) < 2:
            return JsonResponse({
                'success': True,
                'suggestions': [],
                'input': text,
                'count': 0
            })
        
        suggestions = word_prediction_service.predict(text, num_suggestions)
        
        return JsonResponse({
            'success': True,
            'suggestions': suggestions,
            'input': text,
            'count': len(suggestions)
        })
        
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({
            'success': False,
            'error': 'Invalid request parameters'
        }, status=400)
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)

def status(request):
    """Service status endpoint"""
    status_info = word_prediction_service.get_status()
    return JsonResponse(status_info)

@csrf_exempt
def test(request):
    """Test endpoint"""
    test_cases = ["Hello", "How are", "The project", "I need"]
    results = {}
    
    for text in test_cases:
        suggestions = word_prediction_service.predict(text, 2)
        results[text] = suggestions
    
    return JsonResponse({
        'success': True,
        'test_results': results,
        'service': 'word_prediction'
    })