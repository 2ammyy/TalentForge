# utils/moderation.py
from transformers import pipeline
import logging
import re

logger = logging.getLogger(__name__)

# Global model instance (loaded once)
_toxicity_model = None

def get_toxicity_model():
    """Lazy load the model"""
    global _toxicity_model
    if _toxicity_model is None:
        try:
            logger.info("Loading toxicity model...")
            _toxicity_model = pipeline(
                "text-classification",
                model="unitary/toxic-bert",
                device=-1,  # CPU
                max_length=512,
                truncation=True
            )
            logger.info("✅ Toxicity model loaded")
        except Exception as e:
            logger.error(f"❌ Failed to load model: {e}")
    return _toxicity_model

def is_toxic_content(text, threshold=0.7):
    """Check if text contains toxic content"""
    if not text or len(text.strip()) < 5:
        return False, 0.0
    
    try:
        model = get_toxicity_model()
        
        # Fallback to keyword check if model fails
        if not model:
            return keyword_check(text), 0.8 if keyword_check(text) else 0.0
        
        result = model(text)[0]
        
        # Toxic categories to check
        toxic_labels = ['toxic', 'severe_toxic', 'obscene', 
                       'threat', 'insult', 'identity_hate']
        
        # Find highest toxic score
        max_toxic_score = 0.0
        for item in result:
            if item['label'] in toxic_labels:
                if item['score'] > max_toxic_score:
                    max_toxic_score = item['score']
        
        return max_toxic_score > threshold, max_toxic_score
        
    except Exception as e:
        logger.error(f"Error in toxicity check: {e}")
        return keyword_check(text), 0.8 if keyword_check(text) else 0.0

def keyword_check(text):
    """Fallback keyword detection"""
    toxic_patterns = [
        r'\b(kill(ing|ed|s)?|murder(ed|ing|s)?|suicide|rape)\b',
        r'\b(hate(s|ful)?|racist|sexist|nazi)\b',
        r'\b(stupid|idiot|moron|retard)\b',
        r'\b((mother|father)?fuck(er|ing)?|shit(ty)?|damn)\b',
    ]
    
    text_lower = text.lower()
    for pattern in toxic_patterns:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False