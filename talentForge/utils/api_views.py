# posts/api_views.py ou utils/api_views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from utils.moderation import is_toxic_content, get_toxicity_breakdown

@csrf_exempt
def check_content_safety(request):
    """API endpoint pour vérifier le contenu en temps réel"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            text = data.get('text', '')
            
            if not text:
                return JsonResponse({'error': 'No text provided'}, status=400)
            
            # Vérifier la toxicité
            is_toxic, score = is_toxic_content(text)
            breakdown = get_toxicity_breakdown(text)
            
            return JsonResponse({
                'is_toxic': is_toxic,
                'score': round(score, 3),
                'breakdown': breakdown,
                'warning': get_warning_message(is_toxic, score, breakdown)
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def get_warning_message(is_toxic, score, breakdown):
    """Générer un message d'avertissement adapté"""
    if not is_toxic:
        return None
    
    if score > 0.8:
        return "⚠️ Contenu fortement inapproprié. Ce contenu peut être bloqué."
    elif score > 0.6:
        return "⚠️ Contenu inapproprié détecté. Veuillez réviser votre message."
    else:
        return "⚠️ Langage potentiellement offensant. Soyez respectueux."