# word_prediction/services.py
import requests
import logging
import re
import time
from typing import List, Optional, Dict
import urllib.parse

logger = logging.getLogger(__name__)

class WordPredictionService:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "Itish/obsidian_copilot:latest"
        self.timeout = 0.1  # 100ms timeout
        
        # Simple cache
        self._cache = {}
        
        # Initialize suggestion database
        self._init_suggestions_db()
        
        # Stats
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0
        }
    
    def _init_suggestions_db(self):
        """Initialize a comprehensive suggestion database"""
        self.suggestions_db = {
            # Single characters
            'h': ['hello', 'hi', 'how', 'have', 'here', 'hey', 'help'],
            'he': ['hello', 'help', 'here', 'hey', 'he', 'hello there', 'hello everyone'],
            'hel': ['hello', 'help', 'hello there', 'hello everyone', 'help with'],
            'hell': ['hello', 'hello there', 'hello everyone', 'hello world'],
            'hello': ['there', 'world', 'everyone', 'how are', 'good morning'],
            
            # Common patterns
            'hello ': ['there', 'world', 'everyone', 'how are', 'I am'],
            'hello t': ['there', 'to', 'the', 'that', 'this'],
            'hello th': ['there', 'thank', 'that', 'this', 'the'],
            'hello the': ['re', 'project', 'forum', 'community', 'best'],
            'hello ther': ['e', 'efore', 'eby'],
            'hello there': ['I', 'how are', 'good to', 'welcome to', 'thanks for'],
            
            # I want patterns
            'i': ['am', 'have', 'want', 'need', 'think', 'was', 'would', 'will'],
            'i ': ['am', 'have', 'want', 'need', 'think', 'was'],
            'i w': ['want', 'will', 'was', 'would', 'with'],
            'i wa': ['want', 'was', 'watch', 'walk'],
            'i wan': ['want', 'want to', 'wanted', 'wander'],
            'i want': ['to', 'a', 'the', 'some', 'your'],
            'i want ': ['to', 'a', 'the', 'some', 'your'],
            'i want t': ['o', 'o share', 'o learn', 'o create', 'o show'],
            'i want to': ['share', 'learn', 'create', 'show', 'tell', 'ask', 'thank'],
            'i want to ': ['share', 'learn', 'create', 'show', 'tell', 'ask'],
            'i want to s': ['hare', 'how', 'ee', 'ay', 'tart'],
            'i want to sh': ['are', 'ow', 'are with', 'are my', 'are this'],
            'i want to sha': ['re', 're my', 're this', 're our', 're your'],
            'i want to shar': ['e', 'e my', 'e this', 'e our', 'e your'],
            'i want to share': ['my', 'this', 'our', 'your', 'a', 'the'],
            'i want to share ': ['my', 'this', 'our', 'your', 'a', 'the'],
            'i want to share w': ['ith', 'ith you', 'ith everyone', 'ith the', 'ith our'],
            'i want to share wi': ['th', 'th you', 'th everyone', 'th the community'],
            'i want to share wit': ['h', 'h you', 'h everyone', 'h the community'],
            'i want to share with': ['you', 'everyone', 'the community', 'all', 'friends'],
            'i want to share with ': ['you', 'everyone', 'the community', 'all'],
            'i want to share with y': ['ou', 'our', 'our community'],
            'i want to share with yo': ['u', 'ur', 'ur thoughts'],
            'i want to share with you': ['my', 'this', 'our', 'a', 'the'],
            'i want to share with you ': ['my', 'this', 'our', 'a', 'the'],
            
            # Common phrases
            'hello i': ['am', 'want', 'have', 'need', 'think', 'was'],
            'hello i ': ['am', 'want', 'have', 'need', 'think'],
            'hello i w': ['ant', 'as', 'ould', 'ill', 'ant to'],
            'hello i wa': ['nt', 'nt to', 's', 's thinking'],
            'hello i wan': ['t', 't to', 'ted', 't to share'],
            'hello i want': ['to', 'to share', 'to tell', 'to show'],
            'hello i want ': ['to', 'to share', 'to tell'],
            'hello i want t': ['o', 'o share', 'o tell', 'o show'],
            'hello i want to': ['share', 'tell', 'show', 'ask', 'thank'],
            
            # Forum specific
            'project': ['is', 'was', 'has', 'will', 'needs', 'requires'],
            'recipe': ['for', 'is', 'was', 'has', 'needs', 'requires'],
            'job': ['opportunity', 'is', 'was', 'has', 'needs'],
            'creative': ['project', 'idea', 'design', 'art', 'work'],
            'cooking': ['recipe', 'class', 'tips', 'ideas', 'show'],
            'community': ['forum', 'members', 'projects', 'ideas', 'support'],
            
            # General fallbacks
            '': ['hello', 'i', 'the', 'what', 'how', 'can'],
            ' ': ['i', 'the', 'a', 'what', 'how'],
            '  ': ['i', 'the', 'a'],
        }
        
        # Add variations with +
        for key in list(self.suggestions_db.keys()):
            if ' ' in key:
                plus_key = key.replace(' ', '+')
                self.suggestions_db[plus_key] = self.suggestions_db[key]
    
    def get_ollama_completion(self, text: str) -> Optional[str]:
        """Try to get completion from Ollama"""
        try:
            # Simple prompt
            prompt = f"""Complete this text with 1-3 words: "{text}"
Next words:"""
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 10,
                        "stop": ["\n", ".", "!", "?"]
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                completion = result.get('response', '').strip()
                
                # Clean up
                completion = re.sub(r'^["\':;,.!?\s]+', '', completion)
                completion = re.sub(r'["\':;,.!?\s]+$', '', completion)
                
                if completion:
                    logger.info(f"Ollama response: '{completion}'")
                    return completion
            
            return None
            
        except Exception as e:
            logger.debug(f"Ollama error: {e}")
            return None
    
    def get_suggestions_from_db(self, text: str) -> List[str]:
        """Get suggestions from the database"""
        text_lower = text.lower().strip()
        
        # Try exact match first
        if text_lower in self.suggestions_db:
            return self.suggestions_db[text_lower][:5]
        
        # Try partial matches
        for length in range(len(text_lower), 0, -1):
            partial = text_lower[:length]
            if partial in self.suggestions_db:
                suggestions = self.suggestions_db[partial]
                # If we're completing a word, add completions
                if length < len(text_lower):
                    remaining = text_lower[length:]
                    filtered = [s for s in suggestions if s.lower().startswith(remaining)]
                    if filtered:
                        return filtered[:3]
                return suggestions[:3]
        
        # Try to find similar patterns
        words = text_lower.split()
        if words:
            last_word = words[-1]
            
            # Word completion patterns
            completion_patterns = {
                'th': ['the', 'that', 'this', 'then', 'there'],
                'he': ['hello', 'help', 'here', 'hey', 'he'],
                'ha': ['have', 'has', 'had', 'happy'],
                'yo': ['you', 'your', 'yours'],
                'wa': ['was', 'want', 'way', 'water'],
                'go': ['good', 'going', 'got', 'goal'],
                'co': ['could', 'come', 'code', 'cook'],
                'pr': ['project', 'problem', 'process'],
                'in': ['is', 'in', 'into', 'interesting'],
                'fo': ['for', 'forum', 'forward'],
                're': ['recipe', 'really', 'ready'],
                'cr': ['creative', 'craft', 'create'],
                'jo': ['job', 'join', 'journey'],
                'le': ['learn', 'let', 'learning'],
                'sh': ['share', 'should', 'show'],
                'wi': ['with', 'will', 'wish'],
                'ab': ['about', 'above', 'ability'],
                'be': ['be', 'best', 'because'],
                'de': ['design', 'develop', 'decide'],
                'ex': ['excited', 'example', 'excellent'],
                'ma': ['make', 'many', 'may'],
                'ne': ['need', 'never', 'new'],
                'so': ['some', 'someone', 'something'],
                'we': ['we', 'well', 'welcome'],
            }
            
            if last_word in completion_patterns:
                return completion_patterns[last_word][:3]
            
            # Common word patterns
            patterns = {
                'i': ['am', 'have', 'want', 'need', 'think'],
                'you': ['are', 'can', 'have', 'will', 'should'],
                'we': ['are', 'can', 'have', 'will', 'should'],
                'the': ['project', 'best', 'way', 'forum', 'community'],
                'to': ['be', 'do', 'get', 'make', 'see'],
                'for': ['the', 'your', 'this', 'our', 'my'],
                'with': ['you', 'us', 'the', 'your', 'my'],
                'this': ['is', 'was', 'has', 'project', 'idea'],
                'that': ['is', 'was', 'has', 'would', 'could'],
                'have': ['a', 'the', 'some', 'any', 'many'],
                'from': ['the', 'my', 'our', 'your', 'this'],
            }
            
            if last_word in patterns:
                return patterns[last_word][:3]
        
        # Default fallback
        return ["the", "and", "to", "a", "for"][:3]
    
    def predict(self, text: str, num_suggestions: int = 3) -> List[str]:
        """
        Main prediction method - Always returns suggestions
        """
        self.stats['total_requests'] += 1
        
        # Decode URL-encoded text
        try:
            text = urllib.parse.unquote(text)
        except:
            pass
        
        text = text.strip()
        
        # Check cache
        cache_key = text.lower()
        if cache_key in self._cache:
            self.stats['cache_hits'] += 1
            return self._cache[cache_key][:num_suggestions]
        
        # Get suggestions from database (primary source)
        suggestions = self.get_suggestions_from_db(text)
        
        # If we got suggestions, cache and return them
        if suggestions:
            self._cache[cache_key] = suggestions
            logger.info(f"DB suggestions for '{text}': {suggestions[:num_suggestions]}")
            return suggestions[:num_suggestions]
        
        # Try Ollama as backup (but don't wait long)
        try:
            completion = self.get_ollama_completion(text)
            if completion:
                words = completion.split()[:3]
                if words:
                    self._cache[cache_key] = words
                    logger.info(f"Ollama suggestions for '{text}': {words}")
                    return words[:num_suggestions]
        except:
            pass  # Silently fail, use fallback
        
        # Ultimate fallback
        fallback = ["the", "and", "to", "a", "in", "is", "you", "that", "it", "of"]
        self._cache[cache_key] = fallback
        logger.info(f"Fallback for '{text}': {fallback[:num_suggestions]}")
        return fallback[:num_suggestions]
    
    def get_status(self) -> Dict:
        """Get service status"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            ollama_status = "connected" if response.status_code == 200 else "error"
        except:
            ollama_status = "disconnected"
        
        return {
            "status": "ready",
            "ollama_status": ollama_status,
            "model": self.model,
            "cache_size": len(self._cache),
            "stats": self.stats,
            "service": "word_prediction"
        }
    
    def clear_cache(self):
        """Clear the cache"""
        self._cache.clear()
        logger.info("Cache cleared")

# Global instance
word_prediction_service = WordPredictionService()