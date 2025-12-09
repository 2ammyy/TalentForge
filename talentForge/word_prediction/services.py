# word_prediction/services.py
import requests
import logging
import re
import time
from functools import lru_cache

logger = logging.getLogger(__name__)

class WordPredictionService:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "Itish/obsidian_copilot:latest"
        self.timeout = 0.05  # 50 millisecond timeout
        self.cache_duration = 60  # Cache results for 60 seconds
        
        # Cache for recent predictions
        self._cache = {}
        self._cache_timestamps = {}
    
    def _get_cache_key(self, text):
        """Generate cache key from text"""
        return text.strip().lower()
    
    def _get_cached_result(self, text):
        """Get cached result if available and fresh"""
        key = self._get_cache_key(text)
        current_time = time.time()
        
        if key in self._cache:
            timestamp = self._cache_timestamps.get(key, 0)
            if current_time - timestamp < self.cache_duration:
                return self._cache[key]
        
        return None
    
    def _set_cached_result(self, text, result):
        """Cache a result"""
        key = self._get_cache_key(text)
        self._cache[key] = result
        self._cache_timestamps[key] = time.time()
    
    def clean_word(self, word):
        """Clean a single word"""
        if not word or not isinstance(word, str):
            return None
        
        # Remove common unwanted characters
        word = re.sub(r'^[^\w\s]+', '', word)  # Remove leading non-word chars
        word = re.sub(r'[^\w\s]+$', '', word)  # Remove trailing non-word chars
        
        word = word.strip()
        
        # Skip if too short or just punctuation
        if len(word) < 2 or word.lower() in ['the', 'and', 'for', 'with', 'that']:
            return None
        
        return word
    
    def get_ollama_completion(self, text):
        """Get completion from Ollama with error handling"""
        try:
            # Use a prompt that encourages short completions
            prompt = f"Predict next expression after '{text}':"
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 12,
                        "stop": ["\n", ".", "!", "?", ",", ";", ":", "\"", "'"]
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            
            logger.warning(f"Ollama returned status {response.status_code}")
            return None
            
        except requests.exceptions.Timeout:
            logger.debug("Ollama request timeout")
            return None
        except Exception as e:
            logger.debug(f"Ollama request failed: {e}")
            return None
    
    def extract_suggestions(self, text, completion):
        """Extract clean suggestions from completion"""
        if not completion:
            return []
        
        # Clean the completion
        completion = completion.strip()
        
        # Remove the original text if present at start
        if completion.lower().startswith(text.lower()):
            completion = completion[len(text):].strip()
        
        # Split and clean words
        raw_words = completion.split()
        clean_words = []
        
        for word in raw_words:
            cleaned = self.clean_word(word)
            if cleaned:
                clean_words.append(cleaned)
                if len(clean_words) >= 4:  # We only need up to 4 words
                    break
        
        if not clean_words:
            return []
        
        # Generate suggestions
        suggestions = []
        
        # Single word suggestions
        for word in clean_words[:3]:
            suggestions.append(word)
        
        # Phrase suggestions
        if len(clean_words) >= 2:
            suggestions.append(f"{clean_words[0]} {clean_words[1]}")
        
        if len(clean_words) >= 3:
            suggestions.append(f"{clean_words[0]} {clean_words[1]} {clean_words[2]}")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                unique_suggestions.append(s)
        
        return unique_suggestions
    
    def get_smart_fallback(self, text):
        """Get intelligent fallback suggestions based on context"""
        text_lower = text.lower()
        words = text_lower.split()
        
        if not words:
            # return ["the", "and", "for"]
            return[]
        
        last_word = words[-1]
        
        # Context-aware fallback suggestions
        context_map = {
            # Common word endings
            "hello": ["there", "world", "everyone"],
            "hi": ["there", "how", "everyone"],
            "how": ["are", "do", "can", "is"],
            "are": ["you", "we", "they", "these"],
            "you": ["are", "can", "will", "have"],
            "the": ["best", "next", "way", "project"],
            "what": ["is", "are", "do", "can"],
            "when": ["will", "is", "are", "can"],
            "where": ["is", "are", "can", "do"],
            "why": ["is", "are", "do", "would"],
            "i": ["am", "have", "will", "want"],
            "we": ["are", "have", "will", "can"],
            "they": ["are", "have", "will", "can"],
            "can": ["you", "we", "i", "someone"],
            "need": ["to", "a", "the", "some"],
            "want": ["to", "a", "the", "some"],
            "project": ["is", "will", "has", "needs"],
            "weather": ["is", "today", "looks", "seems"],
            "is": ["good", "great", "done", "ready"],
            "to": ["be", "do", "get", "make"],
            "go": ["to", "for", "with", "and"],
            "let's": ["go", "do", "try", "see"],
            
            # Two-word patterns
            "how are": ["you", "things", "you doing"],
            "i want": ["to", "a", "some", "the"],
            "can you": ["help", "do", "tell", "show"],
            "the project": ["is", "will", "has", "needs"],
            "i need": ["to", "a", "some", "help"],
            "let's go": ["to", "for", "now", "there"],
            "what is": ["your", "the", "this", "that"],
            "when will": ["you", "we", "it", "they"],
            "how to": ["use", "do", "make", "fix"],
        }
        
        # Check two-word context first
        if len(words) >= 2:
            last_two = f"{words[-2]} {words[-1]}"
            if last_two in context_map:
                return context_map[last_two][:3]
        
        # Check single word
        if last_word in context_map:
            return context_map[last_word][:3]
        
        # Generic fallbacks
        return ["the", "and", "for"][:3]
    
    def predict(self, text, num_suggestions=3):
        """
        Main prediction method.
        Returns up to num_suggestions predictions.
        """
        text = text.strip()
        if len(text) < 2:
            return []
        
        # Check cache first
        cached = self._get_cached_result(text)
        if cached is not None:
            return cached[:num_suggestions]
        
        # Try to get completion from Ollama
        completion = self.get_ollama_completion(text)
        
        suggestions = []
        
        if completion:
            # Extract suggestions from completion
            suggestions = self.extract_suggestions(text, completion)
        
        # If no good suggestions from Ollama, use smart fallback
        if not suggestions:
            suggestions = self.get_smart_fallback(text)
        
        # Cache the result
        self._set_cached_result(text, suggestions)
        
        return suggestions[:num_suggestions]
    
    def batch_predict(self, texts):
        """Predict for multiple texts (for testing)"""
        results = {}
        for text in texts:
            results[text] = self.predict(text)
        return results
    
    def get_status(self):
        """Get service status"""
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            response_time = (time.time() - start_time) * 1000  # in ms
            
            if response.status_code == 200:
                return {
                    "status": "connected",
                    "model": self.model,
                    "response_time_ms": round(response_time, 2),
                    "cache_size": len(self._cache),
                    "service": "ollama"
                }
            return {
                "status": "error",
                "error": f"HTTP {response.status_code}",
                "service": "ollama"
            }
        except Exception as e:
            return {
                "status": "disconnected",
                "error": str(e),
                "service": "ollama"
            }

# Global instance
word_prediction_service = WordPredictionService()