import requests
import logging
import re
import time
from typing import List, Optional, Dict, Tuple
import urllib.parse
import json
import os
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

@dataclass
class Suggestion:
    text: str
    confidence: float
    source: str

class IntelligentWordPredictionService:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "llama2"  # Changed to a more common model name
        self.timeout = 2.0  # Increased timeout
        
        # Cache with TTL
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = 300  # 5 minutes
        
        # Learning
        self._user_patterns = defaultdict(Counter)
        self._learned_ngrams = defaultdict(Counter)
        self._pattern_file = "word_patterns.json"
        self._save_interval = 10
        
        # Context
        self._recent_words = []
        self._max_recent = 8
        
        # Static suggestions
        self._common_continuations = self._load_common_continuations()
        
        self._init_suggestions_db()
        self._load_learned_patterns()
        
        # Stats
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'ollama_success': 0,
            'ollama_failed': 0,
            'ngram_hits': 0,
            'user_pattern_hits': 0,
            'fallback_used': 0
        }
        
        # Start cleanup thread
        self._cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self._cleanup_thread.start()
    
    def _load_common_continuations(self) -> Dict[str, List[Tuple[str, float]]]:
        """Common English word continuations"""
        return {
            "": [("the", 0.95), ("i", 0.90), ("you", 0.85), ("a", 0.80), ("to", 0.75)],
            "i": [("am", 0.92), ("have", 0.88), ("want", 0.85), ("need", 0.82)],
            "you": [("are", 0.93), ("can", 0.87), ("have", 0.85), ("should", 0.78)],
            "we": [("are", 0.90), ("can", 0.85), ("have", 0.80)],
            "they": [("are", 0.92), ("have", 0.85)],
            "the": [("best", 0.65), ("most", 0.60), ("first", 0.55)],
            "to": [("be", 0.90), ("do", 0.85), ("get", 0.80)],
            "in": [("the", 0.85), ("a", 0.75)],
            "for": [("the", 0.80), ("a", 0.75)],
            "hello": [("there", 0.95), ("world", 0.80)],
            "thank": [("you", 0.98)],
            "good": [("morning", 0.85), ("afternoon", 0.80)],
        }

    def _init_suggestions_db(self):
        """Initialize enhanced static suggestions database"""
        self.suggestions_db = {
            # Single letter predictions
            'a': [('and', 0.9), ('are', 0.85), ('about', 0.8), ('also', 0.75)],
            'b': [('but', 0.9), ('be', 0.85), ('by', 0.8), ('because', 0.75)],
            'c': [('can', 0.9), ('could', 0.85), ('come', 0.8)],
            'd': [('do', 0.9), ('did', 0.85), ('does', 0.8), ('don\'t', 0.75)],
            'e': [('every', 0.9), ('each', 0.85), ('even', 0.8)],
            'f': [('for', 0.9), ('from', 0.85), ('first', 0.8)],
            'g': [('go', 0.9), ('get', 0.85), ('good', 0.8)],
            'h': [('hello', 0.95), ('hi', 0.9), ('how', 0.85), ('have', 0.8), ('here', 0.75)],
            
            # Common partials
            'he': [('hello', 0.95), ('help', 0.9), ('here', 0.85), ('hello', 0.8)],
            'hel': [('hello', 0.98), ('help', 0.9), ('hello', 0.85)],
            'hell': [('hello', 0.99), ('hello', 0.95)],
            
            # Greetings
            'hello': [('there', 0.95), ('world', 0.9), ('everyone', 0.85), ('friend', 0.8)],
            'hi': [('there', 0.95), ('everyone', 0.9), ('how', 0.85)],
            
            # Common phrases
            'i': [('am', 0.95), ('have', 0.9), ('want', 0.85), ('need', 0.8), ('think', 0.75)],
            'i ': [('am', 0.95), ('have', 0.9), ('want', 0.85)],
            'i w': [('want', 0.95), ('will', 0.9), ('was', 0.85), ('would', 0.8)],
            'i want': [('to', 0.97), ('a', 0.9), ('the', 0.85), ('some', 0.8)],
            'i need': [('to', 0.95), ('help', 0.9), ('a', 0.85), ('some', 0.8)],
            
            'how': [('are', 0.95), ('to', 0.9), ('can', 0.85), ('do', 0.8)],
            'how ': [('are', 0.95), ('to', 0.9), ('can', 0.85)],
            'how a': [('are', 0.98), ('about', 0.9)],
            'how are': [('you', 0.98), ('things', 0.85), ('we', 0.8)],
            
            'thank': [('you', 0.98), ('god', 0.8), ('goodness', 0.75)],
            'thanks': [('for', 0.95), ('everyone', 0.85), ('a', 0.8)],
            
            # Question words
            'what': [('is', 0.95), ('are', 0.9), ('do', 0.85), ('can', 0.8)],
            'when': [('is', 0.95), ('will', 0.9), ('can', 0.85), ('do', 0.8)],
            'where': [('is', 0.95), ('are', 0.9), ('can', 0.85), ('do', 0.8)],
            'why': [('is', 0.95), ('are', 0.9), ('do', 0.85), ('can', 0.8)],
            
            # Project-related
            'project': [('update', 0.95), ('idea', 0.9), ('progress', 0.85), ('management', 0.8)],
            'recipe': [('for', 0.95), ('ideas', 0.9), ('sharing', 0.85), ('book', 0.8)],
            
            # Tech/common
            'can': [('you', 0.95), ('i', 0.9), ('we', 0.85), ('someone', 0.8)],
            'should': [('i', 0.95), ('we', 0.9), ('you', 0.85), ('they', 0.8)],
            'will': [('be', 0.95), ('have', 0.9), ('you', 0.85), ('i', 0.8)],
            
            # Platform context
            'platform': [('access', 0.95), ('features', 0.9), ('update', 0.85), ('integration', 0.8)],
            'access': [('to', 0.95), ('the', 0.9), ('control', 0.85), ('permissions', 0.8)],
        }

    def _load_learned_patterns(self):
        """Load learned patterns from file"""
        try:
            if os.path.exists(self._pattern_file):
                with open(self._pattern_file, 'r') as f:
                    data = json.load(f)
                    for prefix, counter in data.get('patterns', {}).items():
                        self._user_patterns[prefix] = Counter(counter)
                    for ngram, counter in data.get('ngrams', {}).items():
                        self._learned_ngrams[ngram] = Counter(counter)
                logger.info(f"Loaded learned patterns from {self._pattern_file}")
        except Exception as e:
            logger.warning(f"Failed to load patterns: {e}")

    def _save_learned_patterns(self):
        """Save learned patterns to file"""
        try:
            data = {
                'patterns': {k: dict(v) for k, v in self._user_patterns.items() if v},
                'ngrams': {k: dict(v) for k, v in self._learned_ngrams.items() if v},
                'timestamp': datetime.now().isoformat()
            }
            with open(self._pattern_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save patterns: {e}")

    def _learn_from_accepted(self, prefix: str, accepted_word: str):
        """Learn from user-accepted suggestions"""
        if not prefix or not accepted_word:
            return
        
        prefix_lower = prefix.lower().strip()
        word_lower = accepted_word.lower().strip()
        
        # Update user patterns
        self._user_patterns[prefix_lower][word_lower] += 1
        
        # Update n-grams
        recent = self._recent_words[-3:]
        if recent:
            # Create n-grams from recent context
            for i in range(1, min(3, len(recent) + 1)):
                ngram = " ".join(recent[-i:])
                if ngram:
                    self._learned_ngrams[ngram][word_lower] += 1
        
        # Save periodically
        if self.stats['total_requests'] % self._save_interval == 0:
            threading.Thread(target=self._save_learned_patterns, daemon=True).start()

    def _periodic_cleanup(self):
        """Clean up expired cache entries"""
        while True:
            time.sleep(60)
            now = time.time()
            expired = [k for k, t in self._cache_timestamps.items() 
                      if now - t > self._cache_ttl]
            for k in expired:
                self._cache.pop(k, None)
                self._cache_timestamps.pop(k, None)

    def _get_ollama_completion(self, text: str) -> Optional[str]:
        """Get completion from Ollama"""
        if not text.strip():
            return None
        
        # Simple prompt for better reliability
        prompt = f"""Complete this text with the most likely next word: "{text}"
        
        Next word:"""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 10
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                completion = result.get("response", "").strip()
                
                # Extract first word
                words = re.findall(r'\b[a-zA-Z]+\b', completion)
                if words:
                    word = words[0].lower()
                    # Clean word
                    word = re.sub(r'[^\w\s]', '', word)
                    if word and len(word) > 1:
                        self.stats['ollama_success'] += 1
                        return word
                
            self.stats['ollama_failed'] += 1
            return None
            
        except requests.exceptions.Timeout:
            logger.debug("Ollama timeout")
            self.stats['ollama_failed'] += 1
            return None
        except Exception as e:
            logger.debug(f"Ollama error: {e}")
            self.stats['ollama_failed'] += 1
            return None

    def predict(self, text: str, num_suggestions: int = 3) -> List[str]:
        """Main prediction method - enhanced for Google-style completion"""
        self.stats['total_requests'] += 1
        
        try:
            text = urllib.parse.unquote(text)
        except:
            pass
        
        text = text.strip()
        
        # Return defaults for empty text
        if not text:
            return ["the", "i", "you", "a", "to"][:num_suggestions]
        
        # Check cache
        cache_key = f"{text}_{num_suggestions}"
        if cache_key in self._cache:
            self.stats['cache_hits'] += 1
            return self._cache[cache_key]
        
        suggestions = []
        text_lower = text.lower()
        
        # 1. Try Ollama first for intelligent completion
        ollama_word = self._get_ollama_completion(text)
        if ollama_word and ollama_word not in suggestions:
            suggestions.append(ollama_word)
        
        # 2. Check for partial word completion
        if " " not in text_lower and len(text_lower) >= 2:
            # Look for words starting with the partial input
            possible_matches = []
            
            # Check static database for partial matches
            for key, items in self.suggestions_db.items():
                if key.startswith(text_lower) and key != text_lower:
                    for word, _ in items:
                        possible_matches.append(word)
            
            # Check common words for partial matches
            for common_word, _ in self._common_continuations.get("", []):
                if common_word.startswith(text_lower):
                    possible_matches.append(common_word)
            
            # Add unique matches
            for match in possible_matches:
                if len(suggestions) < num_suggestions and match not in suggestions:
                    suggestions.append(match)
        
        # 3. Check static database for exact matches
        if text_lower in self.suggestions_db:
            for word, _ in self.suggestions_db[text_lower]:
                if len(suggestions) < num_suggestions and word not in suggestions:
                    suggestions.append(word)
        
        # 4. Check user patterns
        if text_lower in self._user_patterns:
            common_words = self._user_patterns[text_lower].most_common(3)
            for word, _ in common_words:
                if len(suggestions) < num_suggestions and word not in suggestions:
                    suggestions.append(word)
            self.stats['user_pattern_hits'] += 1
        
        # 5. Check common continuations
        last_word = text_lower.split()[-1] if text_lower.split() else ""
        if last_word in self._common_continuations:
            for word, _ in self._common_continuations[last_word]:
                if len(suggestions) < num_suggestions and word not in suggestions:
                    suggestions.append(word)
        
        # 6. Final fallback
        if len(suggestions) < num_suggestions:
            fallback = [("the", 0.7), ("to", 0.65), ("a", 0.6), ("and", 0.55), 
                       ("in", 0.5), ("is", 0.45), ("you", 0.4), ("that", 0.35)]
            
            for word, _ in fallback:
                if len(suggestions) < num_suggestions and word not in suggestions:
                    suggestions.append(word)
            self.stats['fallback_used'] += 1
        
        # Cache the result
        self._cache[cache_key] = suggestions
        self._cache_timestamps[cache_key] = time.time()
        
        logger.debug(f"Google-style prediction: '{text}' -> {suggestions}")
        
        return suggestions[:num_suggestions]

    def feedback_accepted(self, prefix: str, accepted_word: str):
        """Record user acceptance for learning"""
        self._learn_from_accepted(prefix, accepted_word)
        
        # Also update recent words for context
        self._recent_words.append(accepted_word.lower())
        if len(self._recent_words) > self._max_recent:
            self._recent_words.pop(0)

    def get_status(self) -> Dict:
        """Get service status"""
        try:
            # Check Ollama
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            ollama_ok = response.status_code == 200
        except:
            ollama_ok = False
        
        return {
            "status": "ready",
            "ollama_available": ollama_ok,
            "model": self.model,
            "cache_size": len(self._cache),
            "learned_patterns": len(self._user_patterns),
            "stats": self.stats
        }

# Global instance
word_prediction_service = IntelligentWordPredictionService()