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
        # Normalize: trim, lowercase, and remove extra spaces
        return re.sub(r'\s+', ' ', text.strip().lower())
    
    def _get_cached_result(self, text):
        """Get cached result if available and fresh"""
        key = self._get_cache_key(text)
        current_time = time.time()
        
        if key in self._cache:
            timestamp = self._cache_timestamps.get(key, 0)
            if current_time - timestamp < self.cache_duration:
                logger.debug(f"Cache hit for: '{text}'")
                return self._cache[key]
        
        return None
    
    def _set_cached_result(self, text, result):
        """Cache a result"""
        key = self._get_cache_key(text)
        self._cache[key] = result
        self._cache_timestamps[key] = time.time()
        logger.debug(f"Cached result for: '{text}' -> {result}")
    
    def clean_word(self, word):
        """Clean a single word"""
        if not word or not isinstance(word, str):
            return None
        
        # Remove common unwanted characters
        word = re.sub(r'^[^\w\s-]+', '', word)  # Remove leading non-word chars
        word = re.sub(r'[^\w\s-]+$', '', word)  # Remove trailing non-word chars
        
        word = word.strip()
        
        # Skip if too short or just punctuation
        if len(word) < 2:
            return None
        
        # Common words to keep (they're useful for autocomplete)
        common_words = {'a', 'i', 'to', 'in', 'on', 'at', 'of', 'for', 'and', 'the', 'is', 'are', 'was', 'were'}
        if word.lower() in common_words and len(word) <= 3:
            return word
        
        return word
    
    def get_ollama_completion(self, text):
        """Get completion from Ollama with optimized prompt"""
        try:
            prompt = f"""You are an autocomplete assistant for TalentForge - a community forum about creativity, art, cooking, and job opportunities.           
            Suggest 1-3 words that would naturally continue this text in our creative community:
            "{text}"
            Next words:"""
            
            logger.info(f"Requesting prediction for: '{text}'")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,      # Lower for more predictable results
                        "top_p": 0.85,           # Focus on probable tokens
                        "num_predict": 8,        # Shorter to avoid long phrases
                        "stop": [
                            "\n", ".", "!", "?", ",", ";", ":", 
                            "\"", "'", ")", "]", "}", ">",
                            " -", "--", "---", "->", ":", ";",
                            "Next:", "Suggest:", "Completion:", "Output:"
                        ],
                        "repeat_penalty": 1.1,
                        "top_k": 30
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                completion = result.get('response', '').strip()
                
                # Additional cleaning
                completion = re.sub(r'^["\':;,.!?\s]+', '', completion)
                completion = re.sub(r'["\':;,.!?\s]+$', '', completion)
                
                logger.info(f"Raw completion for '{text}': '{completion}'")
                return completion
            
            logger.warning(f"Ollama returned status {response.status_code}")
            return None
            
        except requests.exceptions.Timeout:
            logger.debug(f"Ollama timeout for: '{text}'")
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
        
        logger.debug(f"Extracting from completion: '{completion}'")
        
        # Remove the original text if present at start
        if completion.lower().startswith(text.lower()):
            completion = completion[len(text):].strip()
        
        # Handle cases where completion might contain the prompt text
        prompt_indicators = ["next:", "suggest:", "completion:", "output:"]
        for indicator in prompt_indicators:
            if indicator in completion.lower():
                parts = completion.lower().split(indicator)
                if len(parts) > 1:
                    completion = parts[1].strip()
                    break
        
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
        
        # Generate suggestions - IMPROVED LOGIC
        suggestions = []
        
        # Start with single words (most useful for autocomplete)
        for word in clean_words[:3]:
            suggestions.append(word)
        
        # Add 2-word phrases if available
        if len(clean_words) >= 2:
            two_words = f"{clean_words[0]} {clean_words[1]}"
            if two_words not in suggestions:
                suggestions.append(two_words)
        
        # Add 3-word phrases if available and not too long
        if len(clean_words) >= 3:
            three_words = f"{clean_words[0]} {clean_words[1]} {clean_words[2]}"
            if len(three_words) <= 25:  # Don't suggest overly long phrases
                if three_words not in suggestions:
                    suggestions.append(three_words)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s not in seen:
                seen.add(s)
                unique_suggestions.append(s)
        
        logger.debug(f"Extracted suggestions: {unique_suggestions}")
        return unique_suggestions
    
    def get_smart_fallback(self, text):
        """Get intelligent fallback suggestions based on context"""
        text_lower = text.lower().strip()
        words = text_lower.split()
        
        if not words:
            return []
        
        last_word = words[-1]
        
        # Expanded context-aware fallback suggestions
        context_map = {
            # Common word endings
            "hello": ["there", "world", "everyone", "friend"],
            "hi": ["there", "how", "everyone", "friend"],
            "hey": ["there", "how", "you", "everyone"],
            "how": ["are", "do", "can", "is", "would"],
            "are": ["you", "we", "they", "these", "there"],
            "you": ["are", "can", "will", "have", "should"],
            "the": ["best", "next", "way", "project", "most"],
            "what": ["is", "are", "do", "can", "should"],
            "when": ["will", "is", "are", "can", "should"],
            "where": ["is", "are", "can", "do", "should"],
            "why": ["is", "are", "do", "would", "should"],
            "i": ["am", "have", "will", "want", "need"],
            "we": ["are", "have", "will", "can", "should"],
            "they": ["are", "have", "will", "can", "should"],
            "can": ["you", "we", "i", "someone", "anyone"],
            "need": ["to", "a", "the", "some", "help"],
            "want": ["to", "a", "the", "some", "more"],
            "project": ["is", "will", "has", "needs", "requires"],
            "weather": ["is", "today", "looks", "seems", "forecast"],
            "is": ["good", "great", "done", "ready", "awesome"],
            "to": ["be", "do", "get", "make", "see"],
            "go": ["to", "for", "with", "and", "now"],
            "let's": ["go", "do", "try", "see", "make"],
            
            # Two-word patterns
            "how are": ["you", "things", "you doing", "you today"],
            "i want": ["to", "a", "some", "the", "to go"],
            "can you": ["help", "do", "tell", "show", "please"],
            "the project": ["is", "will", "has", "needs", "requires"],
            "i need": ["to", "a", "some", "help", "assistance"],
            "let's go": ["to", "for", "now", "there", "outside"],
            "what is": ["your", "the", "this", "that", "happening"],
            "when will": ["you", "we", "it", "they", "this"],
            "how to": ["use", "do", "make", "fix", "improve"],
            "thank you": ["so", "very", "so much", "for", "thanks"],
            "good morning": ["everyone", "world", "team", "friends"],
            "happy birthday": ["to", "to you", "wishes", "my friend"],
        }
        
        # Check two-word context first
        if len(words) >= 2:
            last_two = f"{words[-2]} {words[-1]}"
            if last_two in context_map:
                return context_map[last_two][:3]
        
        # Check single word
        if last_word in context_map:
            return context_map[last_word][:3]
        
        # Check if last word is incomplete (user is typing a word)
        if len(last_word) <= 5:  # Short partial word
            common_completions = {
                "th": ["the", "that", "this", "then"],
                "he": ["hello", "help", "here", "he"],
                "ha": ["have", "has", "happy", "had"],
                "yo": ["you", "your", "yours", "yesterday"],
                "wa": ["was", "want", "water", "way"],
                "go": ["go", "good", "going", "gold"],
                "co": ["could", "come", "code", "computer"],
            }
            if last_word in common_completions:
                return common_completions[last_word][:3]
        
        # Generic fallbacks based on text length
        if len(text) < 10:
            return ["a", "the", "to"][:3]
        else:
            return ["and", "for", "with"][:3]
    
    def predict(self, text, num_suggestions=3):
        """
        Main prediction method.
        Returns up to num_suggestions predictions.
        """
        text = text.strip()
        if len(text) < 1:  # Changed from 2 to 1 to handle single character predictions
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
                    "cache_hit_rate": self._calculate_cache_hit_rate(),
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
    
    def _calculate_cache_hit_rate(self):
        """Calculate cache hit rate (simplified)"""
        if not self._cache:
            return 0
        # Simple calculation - in production, track actual hits/misses
        valid_entries = sum(1 for k in self._cache 
                          if time.time() - self._cache_timestamps.get(k, 0) < self.cache_duration)
        return round(valid_entries / max(len(self._cache), 1) * 100, 1)
    
    def clear_cache(self):
        """Clear the prediction cache"""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("Prediction cache cleared")

# Global instance
word_prediction_service = WordPredictionService()