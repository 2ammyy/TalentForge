import requests
import logging
import time
from typing import Dict, Tuple, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)

class PerspectiveAPI:
    """Client pour Perspective API de Google"""
    
    def __init__(self, api_key: str = None, use_cache: bool = True):
        self.api_key = api_key or self._get_api_key()
        self.base_url = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
        self.use_cache = use_cache
        self.rate_limit_delay = 1.0  # 1 seconde entre les requêtes
        self.last_request_time = 0
        
    def _get_api_key(self) -> str:
        """Récupère la clé API depuis les variables d'environnement"""
        import os
        api_key = os.environ.get('PERSPECTIVE_API_KEY')
        if not api_key:
            logger.warning("PERSPECTIVE_API_KEY non défini. Utilisation du mode local.")
        return api_key
    
    def _respect_rate_limit(self):
        """Respecte les limites de taux"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()
    
    @lru_cache(maxsize=1024)
    def analyze_cached(self, text: str) -> Optional[Dict]:
        """Version avec cache des résultats"""
        return self._analyze_uncached(text)
    
    def _analyze_uncached(self, text: str) -> Optional[Dict]:
        """Analyse sans cache"""
        if not self.api_key:
            return None
            
        if not text or len(text.strip()) < 3:
            return None
        
        # Respecter les limites de taux
        self._respect_rate_limit()
        
        payload = {
            "comment": {"text": text},
            "languages": ["en", "fr"],
            "requestedAttributes": {
                "TOXICITY": {},
                "SEVERE_TOXICITY": {},
                "INSULT": {},
                "PROFANITY": {},
                "THREAT": {},
                "IDENTITY_ATTACK": {},
                "SEXUALLY_EXPLICIT": {}
            },
            "doNotStore": True  # Important pour la confidentialité
        }
        
        try:
            response = requests.post(
                f"{self.base_url}?key={self.api_key}",
                json=payload,
                timeout=5.0
            )
            
            if response.status_code == 200:
                data = response.json()
                scores = {}
                for attr, details in data.get('attributeScores', {}).items():
                    scores[attr.lower()] = details['summaryScore']['value']
                return scores
            else:
                logger.error(f"API error {response.status_code}: {response.text[:200]}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning("Perspective API timeout, using local fallback")
            return None
        except Exception as e:
            logger.error(f"Perspective API error: {str(e)[:100]}")
            return None
    
    def analyze(self, text: str) -> Optional[Dict]:
        """Analyse principale avec cache optionnel"""
        if self.use_cache:
            return self.analyze_cached(text)
        else:
            return self._analyze_uncached(text)
    
    def is_toxic(self, text: str, threshold: float = 0.7) -> Tuple[bool, float]:
        """Vérifie si le texte est toxique"""
        scores = self.analyze(text)
        
        if scores:
            # Prendre le score maximum de toxicité
            max_score = max(
                scores.get('toxicity', 0),
                scores.get('severe_toxicity', 0),
                scores.get('insult', 0),
                scores.get('profanity', 0)
            )
            return max_score > threshold, max_score
        
        # Fallback local si API échoue
        return self._local_fallback(text, threshold)
    
    def _local_fallback(self, text: str, threshold: float) -> Tuple[bool, float]:
        """Fallback local simple"""
        # Liste de mots inappropriés
        bad_words = {
            'severe': ['fuck', 'shit', 'kill', 'rape', 'nazi', 'cunt'],
            'moderate': ['stupid', 'idiot', 'moron', 'hate', 'damn'],
            'mild': ['hell', 'bitch', 'bastard']
        }
        
        text_lower = text.lower()
        score = 0.0
        
        for severity, words in bad_words.items():
            for word in words:
                if word in text_lower:
                    if severity == 'severe':
                        score = max(score, 0.9)
                    elif severity == 'moderate':
                        score = max(score, 0.7)
                    else:
                        score = max(score, 0.5)
        
        return score > threshold, score

# Instance globale
perspective_client = PerspectiveAPI()

# Interface compatible avec votre code existant
def is_toxic_content(text: str, threshold: float = 0.7) -> Tuple[bool, float]:
    """Interface compatible avec votre code existant"""
    return perspective_client.is_toxic(text, threshold)

def get_toxicity_breakdown(text: str) -> Dict:
    """Retourne une analyse détaillée"""
    scores = perspective_client.analyze(text)
    
    if scores:
        max_score = max(scores.values()) if scores else 0.0
        return {
            'is_toxic': max_score > 0.7,
            'overall_score': max_score,
            'detailed_scores': scores,
            'source': 'perspective_api',
            'recommendation': 'block' if max_score > 0.7 else 'allow'
        }
    else:
        # Fallback local
        is_toxic, score = perspective_client._local_fallback(text, 0.7)
        return {
            'is_toxic': is_toxic,
            'overall_score': score,
            'detailed_scores': {},
            'source': 'local_fallback',
            'recommendation': 'block' if is_toxic else 'allow'
        }