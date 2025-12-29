import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
import logging
from .services import creative_word_prediction_service

logger = logging.getLogger(__name__)

@require_GET
def predict_word(request):
    """Creative word prediction endpoint for TalentForge"""
    text = request.GET.get('text', '').strip()
    num_suggestions = int(request.GET.get('num_suggestions', 3))
    context = request.GET.get('context', '')
    
    logger.info(f"Creative prediction request: text='{text}', context='{context}'")
    
    try:
        # Use creative prediction
        suggestions = creative_word_prediction_service.predict_creative(text, num_suggestions, context)
        
        # Convert to serializable format
        suggestions_data = []
        for suggestion in suggestions:
            suggestions_data.append({
                'text': suggestion.text,
                'confidence': round(suggestion.confidence, 2),
                'source': suggestion.source,
                'type': suggestion.type
            })
        
        # Get service status
        status = creative_word_prediction_service.get_status()
        
        response_data = {
            'success': True,
            'input': text,
            'suggestions': suggestions_data,
            'total_suggestions': len(suggestions_data),
            'platform': 'TalentForge Creative Platform',
            'service_status': {
                'ollama_available': status['ollama_available'],
                'llama2_success': status['stats']['llama2_success'],
                'creative_hits': status['stats']['creative_hits'],
                'avg_response_ms': status['stats']['avg_response_time_ms']
            }
        }
        
        logger.info(f"Creative prediction response for '{text}': {[s['text'] for s in suggestions_data]}")
        
        return JsonResponse(response_data)
        
    except Exception as e:
        logger.error(f"Error in creative word prediction: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'suggestions': [],
            'fallback': ['art', 'create', 'design'][:num_suggestions]
        })

@require_POST
@csrf_exempt
def feedback(request):
    """Receive feedback on accepted suggestions"""
    try:
        data = json.loads(request.body)
        prefix = data.get('prefix', '')
        accepted_word = data.get('accepted_word', '')
        context = data.get('context', '')
        
        creative_word_prediction_service.feedback_accepted(prefix, accepted_word, context)
        
        return JsonResponse({
            'success': True,
            'message': 'Creative feedback recorded',
            'platform': 'TalentForge'
        })
    except Exception as e:
        logger.error(f"Error recording creative feedback: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@require_GET
def status(request):
    """Get service status"""
    try:
        status_info = creative_word_prediction_service.get_status()
        return JsonResponse({
            'success': True,
            'status': status_info,
            'platform': 'TalentForge Creative Platform'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_GET
def test_creative(request):
    """Test creative predictions"""
    test_cases = [
        'art',
        'crea',
        'paint',
        'I am ',
        'My art ',
        'digital ',
        'insp'
    ]
    
    results = {}
    for text in test_cases:
        suggestions = creative_word_prediction_service.predict_creative(text, 3)
        results[text] = [s.text for s in suggestions]
    
    return JsonResponse({
        'success': True,
        'test_cases': results,
        'service_status': creative_word_prediction_service.get_status()
    })