import requests
import logging
import re
import time
from typing import List, Optional, Dict, Tuple, Any
import urllib.parse
import json
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
import threading
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class Suggestion:
    text: str
    confidence: float
    source: str
    type: str  # 'creative_completion', 'art_term', 'phrase', 'next_word'

class CreativeWordPredictionService:
    def __init__(self):
        self.base_url = "http://localhost:11434"
        self.model = "llama2"
        self.timeout = 3.0
        
        # Cache
        self._cache = {}
        self._cache_timestamps = {}
        self._cache_ttl = 600
        self._max_cache_size = 500
        
        # Learning - only for user-specific patterns
        self._user_patterns = defaultdict(lambda: defaultdict(float))
        self._pattern_file = "creative_user_patterns.json"
        self._save_interval = 50
        
        # Creative context tracking
        self._creative_contexts = defaultdict(list)
        self._max_context_length = 100
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'llama2_success': 0,
            'llama2_failed': 0,
            'creative_hits': 0,
            'fallback_used': 0,
            'response_times': [],
            'average_response_time': 0
        }
        
        # Small set of core creative terms for fallback
        self._core_creative_terms = {
            'art': ['artist', 'artwork', 'artistic', 'artistry'],
            'crea': ['create', 'creative', 'creativity', 'creation'],
            'pain': ['painting', 'painter', 'paint'],
            'draw': ['drawing', 'draw'],
            'desi': ['design', 'designer'],
            'phot': ['photo', 'photography', 'photographer'],
            'musi': ['music', 'musician'],
            'writ': ['writing', 'writer'],
            'danc': ['dance', 'dancer'],
            'film': ['film', 'filmmaker'],
            'poet': ['poetry', 'poet'],
            'scul': ['sculpture', 'sculptor'],
            'craf': ['craft', 'craftsman'],
            'digi': ['digital', 'digital art'],
            'trad': ['traditional', 'tradition'],
            'cont': ['contemporary', 'contemporary art'],
            'abst': ['abstract', 'abstract art'],
            'real': ['realism', 'realistic'],
            'expr': ['expression', 'expressionism'],
            'surr': ['surreal', 'surrealism'],
            'min': ['minimal', 'minimalism'],
            'mod': ['modern', 'modernism'],
            'post': ['postmodern', 'postmodernism'],
            'colo': ['color', 'colorful'],
            'comp': ['composition', 'composer'],
            'insp': ['inspiration', 'inspired'],
            'inn': ['innovation', 'innovative'],
            'exhi': ['exhibition', 'exhibit'],
            'gall': ['gallery', 'gallerist'],
            'stud': ['studio', 'study'],
            'sket': ['sketch', 'sketching'],
            'canv': ['canvas', 'canvases'],
            'brus': ['brush', 'brushes'],
            'pale': ['palette', 'palettes'],
            'styl': ['style', 'stylistic'],
            'tech': ['technique', 'technical'],
            'mater': ['material', 'materials'],
            'medi': ['medium', 'media'],
            'form': ['form', 'formal'],
            'text': ['texture', 'textural']
        }
        
        # Common creative phrases for quick suggestions
        self._creative_phrases = {
            'I am': ['an artist', 'a creative', 'working on', 'inspired by'],
            'I create': ['art', 'designs', 'music', 'stories'],
            'My art': ['is about', 'explores', 'challenges', 'celebrates'],
            'The project': ['focuses on', 'explores', 'investigates', 'questions'],
            'This piece': ['represents', 'expresses', 'conveys', 'symbolizes'],
            'Inspired by': ['nature', 'emotions', 'society', 'dreams'],
            'Working with': ['paint', 'clay', 'digital media', 'found objects'],
            'Exploring': ['identity', 'memory', 'time', 'space'],
            'Challenging': ['norms', 'perceptions', 'boundaries', 'expectations'],
            'Celebrating': ['diversity', 'creativity', 'innovation', 'tradition']
        }
        
        # Load user patterns
        self._load_user_patterns()
        
        # Start maintenance thread
        self._cleanup_thread = threading.Thread(target=self._periodic_cleanup, daemon=True)
        self._cleanup_thread.start()
        
        logger.info("Creative Word Prediction Service initialized for TalentForge")

    def _load_user_patterns(self):
        """Load user-specific patterns from file"""
        try:
            if os.path.exists(self._pattern_file):
                with open(self._pattern_file, 'r') as f:
                    data = json.load(f)
                    
                    # Load user patterns
                    patterns = data.get('patterns', {})
                    for prefix, word_dict in patterns.items():
                        for word, weight in word_dict.items():
                            self._user_patterns[prefix][word] = float(weight)
                            
                logger.info(f"Loaded user patterns from {self._pattern_file}")
        except Exception as e:
            logger.warning(f"Failed to load user patterns: {e}")

    def _save_user_patterns(self):
        """Save user patterns to file"""
        try:
            data = {
                'patterns': {
                    k: {word: float(weight) for word, weight in v.items()}
                    for k, v in self._user_patterns.items() if v
                },
                'timestamp': datetime.now().isoformat(),
                'platform': 'TalentForge Creative Platform'
            }
            
            with open(self._pattern_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to save user patterns: {e}")

    def _create_creative_prompt(self, text: str, context: str = "") -> str:
        """Create a creative-focused prompt for Llama2"""
        
        creative_context = f"""
        You are a creative assistant for TalentForge, a platform for artists and creators.
        Your task is to help artists with creative writing and idea generation.
        
        Context: The user is working on creative content (art, writing, design, music, etc.).
        
        For partial words, complete them with creative/art-related terms.
        For phrases, suggest creative continuations.
        For complete words, suggest creative next words.
        
        Always prioritize creative, artistic, and innovative suggestions.
        
        User input: "{text}"
        """
        
        if context:
            creative_context += f"\nAdditional context: {context}\n"
        
        if ' ' not in text:  # Single word or partial word
            creative_context += f"""
            The user has typed: "{text}"
            If this looks like a partial word, suggest the most likely creative/art-related completion.
            If it's a complete word, suggest creative next words that artists might use.
            
            Suggestions:"""
        elif text.endswith(' '):  # Looking for next word
            creative_context += f"""
            The user wrote: "{text.strip()}"
            Suggest creative next words that would naturally follow in an artistic context.
            
            Next word suggestions:"""
        else:  # Partial phrase
            creative_context += f"""
            The user wrote: "{text}"
            Complete this phrase with creative, artistic suggestions.
            
            Completion suggestions:"""
        
        return creative_context

    def _get_llama2_creative_completion(self, text: str, context: str = "") -> List[Tuple[str, float]]:
        """Get creative completions from Llama2"""
        if not text.strip():
            return []
        
        start_time = time.time()
        prompt = self._create_creative_prompt(text, context)
        
        logger.info(f"Asking Llama2 for creative suggestions for: '{text}'")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Slightly creative temperature
                        "num_predict": 30,    # More tokens for creative suggestions
                        "stop": ["\n\n", "User:", "Assistant:", "Suggestions:", "Completion:"],
                        "top_p": 0.85,
                        "top_k": 30
                    }
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                completion = result.get("response", "").strip()
                
                logger.debug(f"Llama2 raw creative response: '{completion}'")
                
                # Parse suggestions from response
                suggestions = []
                
                # Extract suggested words/phrases
                lines = completion.split('\n')
                for line in lines:
                    line = line.strip()
                    
                    # Remove bullet points, numbers, etc.
                    line = re.sub(r'^[•\-*]\s*', '', line)
                    line = re.sub(r'^\d+[\.\)]\s*', '', line)
                    
                    # Extract potential words/phrases
                    words = re.findall(r'\b[a-zA-Z][a-zA-Z\s\-]*[a-zA-Z]\b', line)
                    
                    for word in words:
                        word = word.strip().lower()
                        if len(word) > 1 and len(word) < 25:  # Reasonable length
                            # Score based on position and relevance
                            score = 0.9 - (len(suggestions) * 0.1)
                            suggestions.append((word, min(max(score, 0.1), 0.9)))
                
                # Remove duplicates while preserving order
                seen = set()
                unique_suggestions = []
                for word, score in suggestions:
                    if word not in seen and word not in [text.lower(), text.lower() + ' ']:
                        seen.add(word)
                        unique_suggestions.append((word, score))
                
                if unique_suggestions:
                    elapsed = time.time() - start_time
                    self.stats['response_times'].append(elapsed)
                    self.stats['llama2_success'] += 1
                    self.stats['creative_hits'] += 1
                    return unique_suggestions[:5]
            
            self.stats['llama2_failed'] += 1
            return []
            
        except requests.exceptions.Timeout:
            logger.warning(f"Llama2 timeout for creative suggestion: '{text}'")
            self.stats['llama2_failed'] += 1
            return []
        except Exception as e:
            logger.warning(f"Llama2 error for creative suggestion '{text}': {e}")
            self.stats['llama2_failed'] += 1
            return []

    def _analyze_input_for_creativity(self, text: str) -> Dict[str, Any]:
        """Analyze input for creative prediction opportunities"""
        analysis = {
            'is_partial_word': False,
            'is_phrase': False,
            'needs_next_word': False,
            'is_creative_context': False,
            'creative_keywords': []
        }
        
        text = text.strip().lower()
        
        # Check for creative keywords
        creative_keywords = ['art', 'create', 'design', 'paint', 'draw', 'write', 
                           'music', 'dance', 'film', 'photo', 'sculpt', 'craft',
                           'creative', 'artist', 'painter', 'writer', 'maker',
                           'project', 'piece', 'work', 'studio', 'gallery',
                           'exhibit', 'show', 'performance', 'installation']
        
        for keyword in creative_keywords:
            if keyword in text:
                analysis['is_creative_context'] = True
                analysis['creative_keywords'].append(keyword)
        
        # Check input type
        if text.endswith(' '):
            analysis['needs_next_word'] = True
        elif ' ' in text:
            analysis['is_phrase'] = True
        else:
            analysis['is_partial_word'] = True
        
        return analysis

    def predict_creative(self, text: str, num_suggestions: int = 5, context: str = "") -> List[Suggestion]:
        """Main creative prediction method"""
        self.stats['total_requests'] += 1
        
        logger.info(f"Creative prediction request: '{text}' (context: '{context}')")
        
        try:
            text = urllib.parse.unquote(text)
        except:
            pass
        
        text = text.strip()
        
        if not text:
            # Default creative suggestions
            return [
                Suggestion(text="art", confidence=0.9, source="creative_default", type="creative_completion"),
                Suggestion(text="create", confidence=0.85, source="creative_default", type="creative_completion"),
                Suggestion(text="design", confidence=0.8, source="creative_default", type="creative_completion"),
                Suggestion(text="inspiration", confidence=0.75, source="creative_default", type="creative_completion"),
                Suggestion(text="studio", confidence=0.7, source="creative_default", type="creative_completion")
            ][:num_suggestions]
        
        # Check cache
        cache_key = hashlib.md5(f"creative_{text}_{context}".encode()).hexdigest()
        if cache_key in self._cache:
            self.stats['cache_hits'] += 1
            logger.debug(f"Cache hit for: '{text}'")
            cached = self._cache[cache_key]
            return cached[:num_suggestions]
        
        suggestions = []
        
        # Analyze input
        analysis = self._analyze_input_for_creativity(text)
        
        # 1. Try Llama2 for creative suggestions (primary)
        llama_suggestions = self._get_llama2_creative_completion(text, context)
        
        for word, confidence in llama_suggestions:
            if len(suggestions) < num_suggestions:
                suggestions.append(Suggestion(
                    text=word,
                    confidence=confidence,
                    source="llama2_creative",
                    type="creative_completion"
                ))
        
        # 2. Check core creative terms for partial words
        if analysis['is_partial_word']:
            text_lower = text.lower()
            for pattern, completions in self._core_creative_terms.items():
                if text_lower.startswith(pattern):
                    for comp in completions:
                        if len(suggestions) < num_suggestions and comp not in [s.text for s in suggestions]:
                            # Adjust confidence based on match quality
                            confidence = 0.8 if text_lower == pattern else 0.7
                            suggestions.append(Suggestion(
                                text=comp,
                                confidence=confidence,
                                source="core_creative",
                                type="art_term"
                            ))
        
        # 3. Check creative phrases
        if analysis['is_phrase']:
            text_lower = text.lower()
            for phrase, continuations in self._creative_phrases.items():
                if text_lower.startswith(phrase):
                    for cont in continuations:
                        if len(suggestions) < num_suggestions and cont not in [s.text for s in suggestions]:
                            suggestions.append(Suggestion(
                                text=cont,
                                confidence=0.75,
                                source="creative_phrase",
                                type="phrase"
                            ))
        
        # 4. Check user patterns (personalized learning)
        if text.lower() in self._user_patterns:
            common_words = sorted(
                self._user_patterns[text.lower()].items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            
            for word, freq in common_words:
                confidence = min(0.6 + (freq * 0.1), 0.85)
                if len(suggestions) < num_suggestions and word not in [s.text for s in suggestions]:
                    suggestions.append(Suggestion(
                        text=word,
                        confidence=confidence,
                        source="user_pattern",
                        type="personalized"
                    ))
        
        # 5. Creative fallback suggestions
        if len(suggestions) < num_suggestions:
            creative_fallbacks = [
                ("creative", 0.7),
                ("artist", 0.65),
                ("inspiration", 0.6),
                ("studio", 0.55),
                ("gallery", 0.5),
                ("exhibition", 0.45),
                ("painting", 0.4),
                ("sculpture", 0.35),
                ("photography", 0.3),
                ("performance", 0.25)
            ]
            
            for word, conf in creative_fallbacks:
                if len(suggestions) < num_suggestions and word not in [s.text for s in suggestions]:
                    suggestions.append(Suggestion(
                        text=word,
                        confidence=conf,
                        source="creative_fallback",
                        type="art_term"
                    ))
            self.stats['fallback_used'] += 1
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        # Cache results
        self._cache[cache_key] = suggestions
        self._cache_timestamps[cache_key] = time.time()
        
        # Clean cache if too large
        if len(self._cache) > self._max_cache_size:
            oldest = sorted(self._cache_timestamps.items(), key=lambda x: x[1])[:50]
            for key, _ in oldest:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)
        
        # Update stats
        if self.stats['response_times']:
            self.stats['average_response_time'] = sum(self.stats['response_times'][-10:]) / min(10, len(self.stats['response_times']))
        
        logger.info(f"Creative suggestions for '{text}': {[s.text for s in suggestions]}")
        
        return suggestions[:num_suggestions]

    def predict(self, text: str, num_suggestions: int = 3) -> List[str]:
        """Backward-compatible simple prediction"""
        suggestions = self.predict_creative(text, num_suggestions)
        return [s.text for s in suggestions]

    def feedback_accepted(self, prefix: str, accepted_word: str, context: str = ""):
        """Record user acceptance for personalized learning"""
        prefix = prefix.lower().strip()
        accepted_word = accepted_word.lower().strip()
        
        if not prefix or not accepted_word:
            return
        
        # Update user patterns
        current_weight = self._user_patterns[prefix].get(accepted_word, 0)
        self._user_patterns[prefix][accepted_word] = current_weight * 0.9 + 1.0
        
        # Update creative context
        if context:
            context_key = context[:50]  # Limit context length
            if context_key not in self._creative_contexts:
                self._creative_contexts[context_key] = []
            
            # Add to context history
            self._creative_contexts[context_key].append((prefix, accepted_word))
            if len(self._creative_contexts[context_key]) > self._max_context_length:
                self._creative_contexts[context_key].pop(0)
        
        # Save periodically
        if self.stats['total_requests'] % self._save_interval == 0:
            threading.Thread(target=self._save_user_patterns, daemon=True).start()
        
        logger.info(f"Feedback recorded: '{prefix}' -> '{accepted_word}'")

    def _periodic_cleanup(self):
        """Clean up expired cache entries"""
        while True:
            time.sleep(300)  # Run every 5 minutes
            now = time.time()
            expired = []
            
            for key, timestamp in list(self._cache_timestamps.items()):
                if now - timestamp > self._cache_ttl:
                    expired.append(key)
            
            for key in expired:
                self._cache.pop(key, None)
                self._cache_timestamps.pop(key, None)

    def get_status(self) -> Dict:
        """Get service status"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            ollama_ok = response.status_code == 200
            models = response.json().get('models', [])
            available_models = [m['name'] for m in models]
        except:
            ollama_ok = False
            available_models = []
        
        return {
            "status": "ready",
            "platform": "TalentForge Creative Platform",
            "ollama_available": ollama_ok,
            "model": self.model,
            "available_models": available_models,
            "cache_size": len(self._cache),
            "user_patterns": len(self._user_patterns),
            "creative_contexts": len(self._creative_contexts),
            "stats": {
                'total_requests': self.stats['total_requests'],
                'cache_hits': self.stats['cache_hits'],
                'llama2_success': self.stats['llama2_success'],
                'llama2_failed': self.stats['llama2_failed'],
                'creative_hits': self.stats['creative_hits'],
                'fallback_used': self.stats['fallback_used'],
                'avg_response_time_ms': round(self.stats.get('average_response_time', 0) * 1000, 2)
            }
        }

    def batch_predict(self, texts: List[str], num_suggestions: int = 3) -> Dict[str, List[Suggestion]]:
        """Batch prediction for multiple inputs"""
        results = {}
        for text in texts:
            results[text] = self.predict_creative(text, num_suggestions)
        return results

    def get_context_suggestions(self, context: str, num_suggestions: int = 5) -> List[Suggestion]:
        """Get suggestions based on creative context"""
        # Extract keywords from context
        words = re.findall(r'\b[a-zA-Z]{3,}\b', context.lower())
        
        # Look for creative keywords
        creative_words = [w for w in words if w in [
            'art', 'artist', 'creative', 'design', 'paint', 'draw',
            'music', 'write', 'sculpt', 'craft', 'photo', 'film'
        ]]
        
        if creative_words:
            # Use the most frequent creative word as base
            from collections import Counter
            word_counts = Counter(creative_words)
            most_common = word_counts.most_common(1)[0][0] if word_counts else 'art'
            
            return self.predict_creative(most_common, num_suggestions, context)
        
        # Default to general creative suggestions
        return self.predict_creative("creative", num_suggestions, context)

# Global instance
creative_word_prediction_service = CreativeWordPredictionService()