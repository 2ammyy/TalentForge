# utils/moderation.py - VERSION CORRIGÉE
import logging
import re
from typing import Tuple, Dict, List, Optional
import time
from functools import lru_cache

logger = logging.getLogger(__name__)

# Essayer d'importer les dépendances IA avec fallback
try:
    import torch
    from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
    import torch.nn.functional as F
    AI_AVAILABLE = True
    logger.info("✅ AI dependencies loaded successfully")
except ImportError as e:
    AI_AVAILABLE = False
    logger.warning(f"⚠️ AI dependencies not available: {e}")
    logger.warning("⚠️ Using keyword-based detection only")

try:
    from better_profanity import profanity
    PROFANITY_AVAILABLE = True
    profanity.load_censor_words()
    logger.info("✅ Better-profanity loaded successfully")
except ImportError:
    PROFANITY_AVAILABLE = False
    logger.warning("⚠️ Better-profanity not available")

# Global model instances
_toxicity_model = None
_model_loaded = False

def get_lightweight_toxicity_scores(text: str) -> Dict[str, float]:
    """Alternative légère utilisant better-profanity"""
    if not PROFANITY_AVAILABLE:
        return {}
    
    try:
        # better-profanity donne juste un booléen
        has_profanity = profanity.contains_profanity(text)
        
        # Retourner un score simulé
        if has_profanity:
            return {
                'toxic': 0.8,
                'profanity': 0.7,
                'offensive': 0.6
            }
        else:
            return {
                'non-toxic': 0.9,
                'clean': 0.8
            }
    except Exception as e:
        logger.error(f"Error in lightweight profanity check: {e}")
        return {}

def get_device():
    """Determine and set device properly"""
    if not AI_AVAILABLE:
        return "cpu"
    
    try:
        # First try to use MPS (Apple Silicon) if available
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            return torch.device("mps")
        # Then try CUDA
        elif torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")
    except Exception as e:
        logger.warning(f"Error detecting device: {e}")
        return torch.device("cpu")

def get_toxicity_model():
    """Lazy load model with proper device handling"""
    global _toxicity_model, _model_loaded
    
    if not AI_AVAILABLE:
        return None
    
    if _model_loaded and _toxicity_model is None:
        return None
    
    if _toxicity_model is None and not _model_loaded:
        try:
            logger.info("Loading toxicity model...")
            
            # ESSAYER LE MODÈLE LÉGER D'ABORD
            try:
                # Modèle très léger
                _toxicity_model = pipeline(
                    "text-classification",
                    model="mrm8488/bert-tiny-finetuned-spam",
                    device=-1,  # Toujours CPU pour éviter les problèmes
                    max_length=128,  # Plus court pour être plus rapide
                    truncation=True
                )
                logger.info("✅ Lightweight toxicity model loaded successfully")
                
            except Exception as light_error:
                logger.warning(f"Lightweight model failed: {light_error}")
                
                # ESSAYER UN MODÈLE ENCORE PLUS SIMPLE
                try:
                    tokenizer = AutoTokenizer.from_pretrained("cardiffnlp/twitter-roberta-base-offensive")
                    model = AutoModelForSequenceClassification.from_pretrained("cardiffnlp/twitter-roberta-base-offensive")
                    
                    # Créer une fonction personnalisée
                    def custom_pipeline(text):
                        inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
                        with torch.no_grad():
                            outputs = model(**inputs)
                        probs = F.softmax(outputs.logits, dim=-1)
                        return [{'label': model.config.id2label[i], 'score': prob.item()} 
                                for i, prob in enumerate(probs[0])]
                    
                    _toxicity_model = custom_pipeline
                    logger.info("✅ Custom lightweight model loaded")
                    
                except Exception as custom_error:
                    logger.error(f"Custom model also failed: {custom_error}")
                    _toxicity_model = None
            
            _model_loaded = True
            
        except Exception as e:
            logger.error(f"❌ All model loading attempts failed: {str(e)[:200]}")
            _model_loaded = True
            _toxicity_model = None
    
    return _toxicity_model

def get_enhanced_toxicity_scores(text: str) -> Dict[str, float]:
    """Get detailed toxicity scores with proper error handling"""
    # Essayer d'abord better-profanity
    light_scores = get_lightweight_toxicity_scores(text)
    if light_scores:
        return light_scores
    
    # Essayer le modèle AI
    if AI_AVAILABLE:
        model = get_toxicity_model()
        if not model:
            logger.warning("Model not available for toxicity scoring")
            return {}
        
        try:
            # Clean the text
            if not text or len(text.strip()) < 3:
                return {}
            
            text = text.strip()
            
            # Use top_k=6 (plus stable que top_k=None)
            try:
                results = model(text, top_k=6)
                
                if results and isinstance(results, list):
                    # Convert to dictionary format
                    scores = {}
                    for item in results:
                        scores[item['label']] = item['score']
                    return scores
                    
            except Exception as e:
                logger.warning(f"top_k=6 failed: {e}")
                
                # Final fallback to single prediction
                try:
                    result = model(text)[0]
                    label = result.get('label', '')
                    score = result.get('score', 0.0)
                    
                    # Return single prediction
                    return {label: score}
                    
                except Exception as final_e:
                    logger.error(f"Even default prediction failed: {final_e}")
                    return {}
                
        except Exception as e:
            logger.error(f"Error getting toxicity scores: {str(e)[:200]}")
    
    return {}

def is_context_safe(text: str) -> Tuple[bool, str]:
    """Check if text is in a safe context that might cause false positives"""
    text_lower = text.lower()
    
    # Check for safe context indicators
    safe_indicators = {
        'academic': [
            r'\b(study|research|analysis|paper|thesis|dissertation|article)\b.*\b(of|on|about|regarding)\b.*\b(suicide|murder|kill|rape|violence)\b',
            r'\b(discussion|talk|lecture|presentation)\b.*\b(about|on|regarding)\b.*\b(racism|sexism|hate)\b',
        ],
        'medical': [
            r'\b(treatment|therapy|prevention|diagnosis|patient|clinical|medical)\b.*\b(of|for)\b.*\b(suicide|self.harm|violence)\b',
            r'\b(crisis|hotline|support|help|intervention)\b.*\b(for|regarding)\b.*\b(suicide|self.harm)\b',
        ],
        'legal': [
            r'\b(case|trial|investigation|evidence|testimony|court|legal)\b.*\b(of|regarding|about)\b.*\b(murder|kill|assault|rape)\b',
            r'\b(law|legislation|policy|regulation)\b.*\b(against|regarding|about)\b.*\b(racism|discrimination|hate)\b',
        ],
        'educational': [
            r'\b(education|teaching|learning|lesson|course|class)\b.*\b(about|on)\b.*\b(racism|sexism|history)\b',
            r'\b(awareness|prevention|campaign)\b.*\b(about|regarding)\b.*\b(suicide|violence|hate)\b',
        ],
        'literary': [
            r'\b(book|novel|story|movie|film|play|theater|character|plot)\b.*\b(about|featuring|with)\b.*\b(murder|kill|violence|suicide)\b',
            r'\b(scene|chapter|part|section)\b.*\b(about|featuring|depicting)\b.*\b(violence|murder)\b',
        ]
    }
    
    for context_type, patterns in safe_indicators.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True, context_type
    
    return False, ""

def intelligent_keyword_check(text: str) -> Tuple[bool, float, Dict[str, List[str]]]:
    """
    Enhanced keyword detection with context awareness
    Returns: (is_toxic, confidence_score, matched_keywords_dict)
    """
    text_lower = text.lower()
    
    # First check if it's a safe context
    is_safe, context_type = is_context_safe(text)
    
    # Define keyword patterns with weights
    keyword_patterns = {
        'severe_violence': {
            'pattern': r'\b(kill(ing|ed|s|er)?|murder(ed|ing|s|er)?|suicide|assassinat(e|ion)|slaughter(ed)?)\b',
            'weight': 0.9 if not is_safe else 0.3,  # Lower weight for safe contexts
            'exceptions': [
                r'\b(character|story|plot|movie|film|novel|book|game|fiction)\b.*\b(kill|murder)\b',
                r'\b(kill|murder)\b.*\b(joy|pain|time|boredom|conversation)\b',
                r'\b(suicide)\b.*\b(prevention|awareness|rate|statistics|study|research|help)\b',
            ]
        },
        'sexual_violence': {
            'pattern': r'\b(rape(d|s)?|molest(ation|ed)?|sexual\s+assault)\b',
            'weight': 0.95 if not is_safe else 0.2,
            'exceptions': [
                r'\b(rape)\b.*\b(crisis|center|hotline|victim|survivor|awareness)\b',
                r'\b(sexual\s+assault)\b.*\b(awareness|prevention|support|help)\b',
            ]
        },
        'hate_speech': {
            'pattern': r'\b(racist|sexist|nazi|bigot(ed|ry)?|homophob(e|ic)|transphob(e|ic))\b',
            'weight': 0.85 if not is_safe else 0.4,
            'exceptions': [
                r'\b(discuss|discussion|talk|speak|write|study|research)\b.*\b(about|regarding|on)\b.*\b(racist|sexist|nazi)\b',
                r'\b(against|combat|fight|oppose|condemn)\b.*\b(racism|sexism|homophobia|nazism)\b',
                r'\b(education|teaching|learning)\b.*\b(about|on)\b.*\b(racism|sexism)\b',
            ]
        },
        'severe_insults': {
            'pattern': r'\b((mother|father)?fuck(er|ing|s)?|cunt|whore|slut|bastard)\b',
            'weight': 0.8,
            'exceptions': [
                r'\b(fucking)\b.*\b(awesome|amazing|great|incredible|brilliant)\b',
                r'\b(motherfucker)\b.*\b(song|movie|character|quote|reference)\b',
            ]
        },
        'moderate_insults': {
            'pattern': r'\b(stupid|idiot|moron|retard(ed)?|dumb(ass)?|asshole)\b',
            'weight': 0.7,
            'exceptions': [
                r'\b(called|labeled|considered|thought)\b.*\b(an?\s+)?(idiot|moron|stupid)\b',
                r'\b(feel|felt|feelings)\b.*\b(like\s+an?\s+)?(idiot|moron|stupid)\b',
            ]
        },
        'mild_profanity': {
            'pattern': r'\b(shit(ty)?|damn|hell|bitch|bastard)\b',
            'weight': 0.6,
            'exceptions': [
                r'\b(holy\s+shit|oh\s+shit|shit)\b.*\b(happened|wrong|sorry|apologies)\b',
                r'\b(damn)\b.*\b(good|great|awesome|amazing|right|cool)\b',
                r'\b(hell)\b.*\b(yeah|no|yes|of\s+a)\b',
                r'\b(bitch)\b.*\b(please|sorry|apology)\b',
            ]
        }
    }
    
    matched_keywords = {}
    total_confidence = 0.0
    max_confidence = 0.0
    
    for category, config in keyword_patterns.items():
        pattern = config['pattern']
        weight = config['weight']
        exceptions = config.get('exceptions', [])
        
        # Check if text matches the pattern
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        found_words = list(set([match.group() for match in matches]))  # Remove duplicates
        
        if found_words:
            # Check exceptions
            is_exception = False
            for exception_pattern in exceptions:
                if re.search(exception_pattern, text_lower):
                    is_exception = True
                    logger.debug(f"Exception matched for {category}: {exception_pattern}")
                    break
            
            if not is_exception:
                matched_keywords[category] = found_words
                total_confidence += weight * len(found_words)
                max_confidence = max(max_confidence, weight)
    
    # Calculate overall score (normalized with context adjustment)
    if is_safe:
        keyword_score = min(1.0, total_confidence / 10.0)  # Much lower for safe contexts
    else:
        keyword_score = min(1.0, total_confidence / 5.0)
    
    # Adjust threshold based on context
    threshold = 0.5 if not is_safe else 0.7
    is_toxic = keyword_score > threshold
    
    return is_toxic, keyword_score, matched_keywords

@lru_cache(maxsize=1024)
def cached_toxicity_check(text: str, threshold: float = 0.7) -> Tuple[bool, float]:
    """Cache results for frequently repeated texts"""
    return _is_toxic_content_impl(text, threshold)

def _is_toxic_content_impl(text: str, threshold: float = 0.7) -> Tuple[bool, float]:
    """Internal implementation without cache"""
    # Pre-processing
    text = text.strip()
    
    # Basic validation
    if not text or len(text) < 5:
        return False, 0.0
    
    # Check if it's likely to be code or gibberish
    if is_likely_code_or_gibberish(text):
        logger.debug("Text appears to be code or gibberish, skipping toxicity check")
        return False, 0.0
    
    # Check for safe context first
    is_safe, context_type = is_context_safe(text)
    
    # Try to get scores from AI model or better-profanity
    scores = get_enhanced_toxicity_scores(text)
    
    if scores:
        # Extract toxic scores
        toxic_labels = ['toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate', 'profanity', 'offensive']
        
        toxic_scores = {label: scores.get(label, 0.0) for label in toxic_labels if label in scores}
        max_toxic_score = max(toxic_scores.values()) if toxic_scores else 0.0
        
        # Adjust threshold based on context
        adjusted_threshold = threshold
        if is_safe:
            # Higher threshold for safe contexts to reduce false positives
            adjusted_threshold = min(0.85, threshold + 0.15)
            logger.debug(f"Safe context '{context_type}', using threshold: {adjusted_threshold}")
        
        # Check if toxic
        is_toxic = max_toxic_score > adjusted_threshold
        
        # If borderline, do additional keyword check
        if 0.4 <= max_toxic_score <= 0.6:
            keyword_toxic, keyword_score, matched = intelligent_keyword_check(text)
            if keyword_toxic:
                # Weighted combination favoring model
                combined_score = (max_toxic_score * 0.6) + (keyword_score * 0.4)
                is_toxic = combined_score > adjusted_threshold
                max_toxic_score = combined_score
        
        # Log results for monitoring
        if is_toxic or max_toxic_score > 0.5:
            logger.info(f"Toxicity check - Text: '{text[:50]}...' | "
                       f"Score: {max_toxic_score:.3f} | "
                       f"Toxic: {is_toxic} | "
                       f"Context: {context_type if is_safe else 'unsafe'}")
        
        return is_toxic, max_toxic_score
    else:
        # Model failed, use intelligent keyword check
        logger.warning("Model unavailable, using intelligent keyword check")
        is_toxic, keyword_score, matched = intelligent_keyword_check(text)
        
        # Log the matched keywords for debugging
        if matched:
            logger.debug(f"Keyword check matched: {matched}")
        
        return is_toxic, keyword_score

def is_toxic_content(text: str, threshold: float = 0.7, use_cache: bool = True) -> Tuple[bool, float]:
    """
    Main toxicity check function
    
    Args:
        text: Text to check
        threshold: Confidence threshold (0.0-1.0)
        use_cache: Whether to use caching for repeated texts
    
    Returns:
        Tuple of (is_toxic, confidence_score)
    """
    if use_cache and len(text) < 1000:  # Don't cache very long texts
        return cached_toxicity_check(text, threshold)
    else:
        return _is_toxic_content_impl(text, threshold)

def get_toxicity_breakdown(text: str) -> Dict:
    """Get detailed breakdown of toxicity scores"""
    # Get keyword check results first
    keyword_toxic, keyword_score, matched = intelligent_keyword_check(text)
    
    # Try to get model scores
    scores = get_enhanced_toxicity_scores(text)
    
    if not scores:
        return {
            'is_toxic': keyword_toxic,
            'overall_score': keyword_score,
            'source': 'keyword_check',
            'matched_keywords': matched,
            'detailed_scores': {},
            'context_safe': is_context_safe(text)[0],
            'recommendation': 'block' if keyword_toxic else 'allow',
            'confidence': 'medium' if keyword_score > 0.3 else 'low'
        }
    
    toxic_labels = ['toxic', 'severe_toxic', 'obscene', 'threat', 'insult', 'identity_hate', 'profanity', 'offensive']
    toxic_scores = {label: scores.get(label, 0.0) for label in toxic_labels if label in scores}
    max_toxic_score = max(toxic_scores.values()) if toxic_scores else 0.0
    
    # Check context
    is_safe, context_type = is_context_safe(text)
    
    # Adjust threshold for safe contexts
    threshold = 0.7
    if is_safe:
        threshold = 0.85
    
    # Combined assessment
    model_toxic = max_toxic_score > threshold
    final_toxic = model_toxic or (keyword_toxic and keyword_score > 0.7)
    
    return {
        'is_toxic': final_toxic,
        'overall_score': max(max_toxic_score, keyword_score),
        'source': 'model' if scores else 'keyword_check',
        'model_score': max_toxic_score,
        'keyword_score': keyword_score,
        'toxic_scores': toxic_scores,
        'keyword_matches': matched,
        'context': {
            'is_safe': is_safe,
            'type': context_type
        },
        'recommendation': 'block' if final_toxic else 'allow',
        'confidence': 'high' if abs(max_toxic_score - keyword_score) < 0.2 else 'medium'
    }

def is_likely_code_or_gibberish(text: str) -> bool:
    """Detect if text is likely code, gibberish, or non-language content"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    if len(text) < 10:
        return False
    
    # Check for high percentage of special characters
    special_chars = re.findall(r'[^\w\s.,!?\-@#$%^&*()]', text)
    if len(special_chars) / max(len(text), 1) > 0.4:
        return True
    
    # Check for code-like patterns
    code_patterns = [
        r'(\w+\.\w+\(.*\))',  # Function calls
        r'(def\s+\w+|class\s+\w+|import\s+\w+)',  # Python
        r'(if\s*\(|for\s*\(|while\s*\(|switch\s*\()',  # Control structures
        r'(\$\w+|\{\{.*\}\}|<%.*%>|<\?php)',  # Template/PHP
        r'(public|private|protected|void|int|string|boolean)\s+\w+\s*\(',  # Java/C#
    ]
    
    for pattern in code_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    
    # Check for repeated patterns (might be gibberish)
    words = re.findall(r'\b\w+\b', text)
    if len(words) > 15:
        unique_words = set(words)
        if len(unique_words) / len(words) < 0.3:  # High repetition
            return True
    
    return False

# Backward compatibility
def keyword_check(text: str) -> bool:
    """Legacy function for backward compatibility"""
    is_toxic, _, _ = intelligent_keyword_check(text)
    return is_toxic

def test_moderation_system():
    """Test the moderation system"""
    print("Testing moderation system...")
    
    if AI_AVAILABLE:
        print(f"✅ AI dependencies available")
        # Test model loading
        print("\nLoading toxicity model...")
        model = get_toxicity_model()
        if model:
            print("✅ Model loaded successfully")
        else:
            print("❌ Model failed to load")
    else:
        print("⚠️ AI dependencies not available, using keyword-based detection")
    
    if PROFANITY_AVAILABLE:
        print("✅ Better-profanity available")
    
    # Test toxicity checking
    test_cases = [
        ("Hello world!", False),
        ("You are fucking stupid!", True),
        ("This is a test message.", False),
        ("I love this platform!", False),
        ("Go to hell you idiot!", True),
        ("This is a discussion about suicide prevention.", False),
    ]
    
    print("\n" + "="*50)
    print("Testing toxicity detection:")
    
    for text, expected_toxic in test_cases:
        print(f"\nTesting: '{text}'")
        is_toxic, score = is_toxic_content(text, use_cache=False)
        print(f"Result: Toxic={is_toxic}, Score={score:.3f}")
        print(f"Expected: Toxic={expected_toxic}")
        match = "✓" if is_toxic == expected_toxic else "✗"
        print(f"Match: {match}")
    
    # Test breakdown
    print("\n" + "="*50)
    print("Detailed breakdown test:")
    test_text = "This is a really stupid idea"
    breakdown = get_toxicity_breakdown(test_text)
    print(f"Text: '{test_text}'")
    print(f"Toxic: {breakdown['is_toxic']}")
    print(f"Score: {breakdown['overall_score']:.3f}")
    print(f"Source: {breakdown['source']}")
    print(f"Recommendation: {breakdown['recommendation']}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_moderation_system()