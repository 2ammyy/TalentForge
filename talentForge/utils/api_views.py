from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging

logger = logging.getLogger(__name__)

# Fonctions de secours temporaires
def dummy_is_toxic_content(text, threshold=0.7):
    """Fonction de secours pour tests"""
    logger.info(f"DEBUG: Checking toxicity for: {text[:50]}...")
    # Logique simple de secours
    bad_words = ['fuck', 'shit', 'stupid', 'idiot', 'kill', 'hate']
    text_lower = text.lower()
    
    for word in bad_words:
        if word in text_lower:
            return True, 0.8
    
    return False, 0.1

def dummy_get_toxicity_breakdown(text):
    """Fonction de secours pour tests"""
    is_toxic, score = dummy_is_toxic_content(text)
    return {
        'is_toxic': is_toxic,
        'overall_score': score,
        'source': 'dummy_check',
        'recommendation': 'block' if is_toxic else 'allow',
        'confidence': 'high' if score > 0.7 else 'low'
    }

# Essayer d'importer les vraies fonctions, sinon utiliser les fonctions de secours
try:
    from utils.moderation import is_toxic_content, get_toxicity_breakdown
    logger.info("✅ Moderation functions imported successfully")
except ImportError as e:
    logger.warning(f"⚠️ Could not import moderation functions: {e}")
    logger.warning("⚠️ Using dummy functions instead")
    is_toxic_content = dummy_is_toxic_content
    get_toxicity_breakdown = dummy_get_toxicity_breakdown
except SyntaxError as e:
    logger.error(f"❌ Syntax error in moderation module: {e}")
    logger.warning("⚠️ Using dummy functions instead")
    is_toxic_content = dummy_is_toxic_content
    get_toxicity_breakdown = dummy_get_toxicity_breakdown

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
            logger.error(f"Error in content safety check: {e}")
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