"""
AI Content Validator for Creative Fields
Improved version with better job detection
"""

import os
import re
from typing import List, Tuple, Dict, Any
import json

# For text analysis
try:
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    print("Warning: transformers not installed. Using manual validation only.")
    TRANSFORMERS_AVAILABLE = False

# Enhanced creative categories with more comprehensive keywords
DEFAULT_CREATIVE_CATEGORIES = {
    'visual_arts': [
        'painting', 'drawing', 'sculpture', 'illustration', 'digital art', 
        'photography', 'graphic design', 'animation', '3d modeling', 'concept art',
        'watercolor', 'oil painting', 'sketch', 'portrait', 'landscape',
        'character design', 'storyboard', 'comic', 'manga', 'anime',
        'fine arts', 'mixed media', 'printmaking', 'textile art', 'installation art',
        'art direction', 'art curation', 'exhibition design'
    ],
    'design': [
        'ui/ux design', 'web design', 'product design', 'fashion design', 
        'interior design', 'graphic design', 'industrial design', 'logo design',
        'brand identity', 'typography', 'layout', 'packaging design',
        'motion design', 'exhibition design', 'set design', 'costume design',
        'game design', 'level design', 'environment design', 'character design',
        'user interface', 'user experience', 'interactive design'
    ],
    'culinary_arts': [
        'cooking', 'baking', 'pastry', 'food styling', 'culinary arts', 
        'cake design', 'chocolate art', 'food photography', 'recipe development',
        'plating', 'gastronomy', 'mixology', 'food art', 'culinary arts',
        'chef', 'sous chef', 'pastry chef', 'culinary artist', 'food preparation'
    ],
    'performing_arts': [
        'music', 'dance', 'theater', 'acting', 'singing', 'instrument', 
        'performance art', 'stand-up comedy', 'orchestra', 'choir',
        'piano', 'guitar', 'violin', 'drums', 'composition', 'songwriting',
        'choreography', 'directing', 'producing', 'screenwriting',
        'musician', 'vocalist', 'dancer', 'actor', 'performer',
        'director', 'producer', 'stage manager', 'lighting design', 'sound design',
        'pianist', 'guitarist', 'violinist', 'drummer', 'saxophonist', 'cellist',
        'opera', 'ballet', 'musical theater', 'improv', 'storytelling'
    ],
    'literary_arts': [
        'writing', 'poetry', 'fiction', 'creative writing', 'screenwriting', 
        'copywriting', 'storytelling', 'novel', 'short story', 'playwriting',
        'blogging', 'journalism', 'editing', 'publishing', 'translation',
        'author', 'writer', 'poet', 'editor', 'content creator',
        'scriptwriting', 'ghostwriting', 'technical writing', 'creative non-fiction'
    ],
    'crafts': [
        'pottery', 'woodworking', 'jewelry making', 'textile arts', 
        'calligraphy', 'glass blowing', 'ceramics', 'knitting', 'crochet',
        'embroidery', 'weaving', 'leatherworking', 'metalworking', 'origami',
        'arabic calligraphy', 'خط عربي', 'handmade', 'artisan', 'craftsmanship'
    ],
    'media_entertainment': [
        'film making', 'video editing', 'game design', 'animation', 
        'video production', 'sound design', 'vfx', 'cinematography',
        'documentary', 'short film', 'music video', 'podcast', 'streaming',
        'film production', 'video editing', 'sound engineering', 'audio production',
        'cinematographer', 'editor', 'producer', 'director'
    ],
    'digital_creativity': [
        'motion graphics', 'digital painting', 'web design', 'app design', 
        'ar/vr design', 'interactive media', '3d animation', 'game development',
        'coding creative', 'creative coding', 'generative art', 'digital art',
        'ui design', 'ux design', 'interaction design', 'experience design'
    ]
}

# Enhanced job-specific keywords
CREATIVE_JOB_KEYWORDS = [
    'artist', 'designer', 'creative', 'animator', 'illustrator', 'photographer',
    'musician', 'writer', 'chef', 'baker', 'stylist', 'director', 'editor',
    'architect', 'interior designer', 'graphic designer', 'ui/ux', 'web designer',
    'video editor', 'sound designer', 'game designer', 'art director',
    'content creator', 'copywriter', 'artisan', 'craftsman', 'maker',
    'painter', 'sculptor', 'ceramist', 'calligrapher', 'filmmaker',
    'composer', 'choreographer', 'dancer', 'actor', 'performer',
    'pastry chef', 'food stylist', 'culinary artist', 'mixologist',
    'pianist', 'guitarist', 'violinist', 'drummer', 'singer', 'vocalist',
    'author', 'poet', 'playwright', 'screenwriter', 'novelist',
    'producer', 'cinematographer', 'sound engineer', 'lighting designer',
    'stage manager', 'costume designer', 'set designer', 'production designer',
    'creative director', 'art curator', 'exhibition designer', 'gallery manager'
]

# More specific creative action verbs
CREATIVE_ACTION_VERBS = [
    'create', 'design', 'develop', 'compose', 'produce', 'direct',
    'perform', 'illustrate', 'animate', 'photograph', 'sculpt',
    'choreograph', 'arrange', 'orchestrate', 'write', 'paint',
    'edit', 'curate', 'style', 'craft', 'build', 'make',
    'innovate', 'imagine', 'visualize', 'conceptualize', 'storyboard'
]

# Creative skills and tools
CREATIVE_SKILLS = [
    'photoshop', 'illustrator', 'premiere pro', 'after effects', 'final cut',
    'maya', 'blender', 'unity', 'unreal engine', 'autocad', 'sketchup',
    'pro tools', 'logic pro', 'ableton', 'fl studio', 'cubase',
    'adobe creative suite', 'creative cloud', 'figma', 'sketch',
    'sight-reading', 'improvisation', 'composition', 'arrangement',
    'storytelling', 'character development', 'world building',
    'color theory', 'typography', 'layout', 'composition',
    'voice training', 'dance technique', 'acting method'
]

class ContentValidator:
    """
    Validates content against creative/artistic fields
    """
    
    def __init__(self, use_lightweight_model=True):
        """Initialize AI models"""
        self.model_loaded = False
        self.text_classifier = None
        self.creative_categories = DEFAULT_CREATIVE_CATEGORIES.copy()
        self.creative_job_keywords = CREATIVE_JOB_KEYWORDS.copy()
        self.creative_action_verbs = CREATIVE_ACTION_VERBS.copy()
        self.creative_skills = CREATIVE_SKILLS.copy()
        
        # Initialize AI model if available
        if TRANSFORMERS_AVAILABLE and not use_lightweight_model:
            try:
                model_name = "facebook/bart-large-mnli"
                self.text_classifier = pipeline(
                    "zero-shot-classification",
                    model=model_name,
                    device=-1  # Use CPU
                )
                self.model_loaded = True
                print(f"✅ AI model loaded successfully: {model_name}")
            except Exception as e:
                print(f"⚠️ Could not load AI model: {e}")
                self.model_loaded = False
        else:
            self.model_loaded = False
        
        # Validation thresholds - Adjusted for better job detection
        self.threshold_approve = 0.3  # Lower threshold for approval
        self.threshold_warning = 0.2  # Warning threshold
    
    def validate_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main validation function for posts
        """
        post_type = post_data.get('type', 'text')
        
        if post_type == 'text':
            return self._validate_text_post(post_data)
        elif post_type == 'image':
            return self._validate_image_post(post_data)
        elif post_type == 'video':
            return self._validate_video_post(post_data)
        elif post_type == 'job':
            return self._validate_job_post(post_data)
        else:
            return self._validate_text_post(post_data)
    
    def _validate_text_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate text-based posts"""
        title = post_data.get('title', '')
        content = post_data.get('content', '')
        
        # Combine title and content for analysis
        full_text = f"{title} {content}".strip()
        
        if not full_text:
            return {
                'is_valid': True,
                'score': 0.0,
                'confidence': 0.0,
                'reason': "Empty post - cannot validate",
                'suggestions': [],
                'detected_categories': []
            }
        
        # Manual classification
        ai_result = self._manual_classify_text(full_text)
        
        # Check against non-creative keywords
        non_creative_score = self._check_non_creative_keywords(full_text)
        
        # Calculate final score (weighted average)
        final_score = (ai_result['score'] * 0.7) + (non_creative_score * 0.3)
        
        # Determine if valid
        is_valid = final_score >= self.threshold_approve
        
        # Generate reason based on score
        if final_score >= 0.6:
            reason = "Excellent creative content!"
        elif final_score >= 0.4:
            reason = "Good creative content"
        elif final_score >= 0.3:
            reason = "Some creative elements"
        elif final_score >= 0.2:
            reason = "Limited creative elements, could be improved"
        else:
            reason = "Not creative enough for our platform"
        
        return {
            'is_valid': is_valid,
            'score': round(final_score, 3),
            'confidence': round(ai_result.get('confidence', 0.0), 3),
            'reason': reason,
            'suggestions': self._generate_suggestions(full_text, ai_result['categories'], final_score),
            'detected_categories': ai_result['categories'][:3] if ai_result['categories'] else []
        }
    
    def _validate_job_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate job posts - IMPROVED VERSION"""
        title = post_data.get('title', '')
        content = post_data.get('content', '')
        job_fields = post_data.get('job_fields', {})
        
        # Combine all text for analysis
        full_text = f"{title} {content} {job_fields.get('company', '')} {job_fields.get('skills_required', '')}".lower()
        
        if not full_text.strip():
            return {
                'is_valid': True,
                'score': 0.0,
                'confidence': 0.0,
                'reason': "Empty job post - cannot validate",
                'suggestions': [],
                'detected_categories': []
            }
        
        # Enhanced scoring for job posts
        scores = self._calculate_job_scores(title, content, job_fields)
        
        # Calculate final score with adjusted weights for jobs
        final_score = (
            scores['title_score'] * 0.25 +
            scores['content_score'] * 0.35 +
            scores['skills_score'] * 0.25 +
            scores['action_verbs_score'] * 0.15
        )
        
        # Normalize score (make it easier for jobs to pass)
        normalized_score = min(1.0, final_score * 1.5)  # Boost job scores
        
        # Get categories from the full text
        categories = self._extract_categories_from_text(full_text)
        
        # Determine if valid - LOWER THRESHOLD FOR JOBS
        is_valid = normalized_score >= 0.2  # Only 20% needed for jobs
        
        # Generate reason
        if normalized_score >= 0.6:
            reason = "Excellent creative job posting!"
        elif normalized_score >= 0.4:
            reason = "Good creative job posting"
        elif normalized_score >= 0.2:
            reason = "Creative job posting"
        else:
            reason = "Job posting may not be for creative/artistic roles"
        
        # Generate suggestions if score is low
        suggestions = []
        if normalized_score < 0.4:
            suggestions = self._generate_job_suggestions(title, content, job_fields, normalized_score)
        
        return {
            'is_valid': is_valid,
            'score': round(normalized_score, 3),
            'confidence': round(normalized_score, 3),
            'reason': reason,
            'suggestions': suggestions,
            'detected_categories': categories[:3],
            'score_breakdown': {
                'title': round(scores['title_score'], 3),
                'content': round(scores['content_score'], 3),
                'skills': round(scores['skills_score'], 3),
                'verbs': round(scores['action_verbs_score'], 3)
            }
        }
    
    def _calculate_job_scores(self, title: str, content: str, job_fields: Dict) -> Dict[str, float]:
        """Calculate detailed scores for job posts"""
        
        # Combine all text for analysis
        all_text = f"{title} {content} {job_fields.get('skills_required', '')}".lower()
        company = job_fields.get('company', '').lower()
        
        # 1. Title score - check for creative job titles
        title_score = self._score_creative_content(title, is_job=True)
        
        # 2. Content score - enhanced with context analysis
        content_score = self._score_creative_content(content, is_job=True)
        
        # 3. Skills score
        skills = job_fields.get('skills_required', '')
        skill_score = self._calculate_skills_score(skills)
        
        # 4. Action verbs score - check for creative action verbs
        action_verbs_score = self._score_action_verbs(all_text)
        
        # 5. Company name bonus
        company_bonus = 0.1 if self._is_creative_company(company) else 0
        
        return {
            'title_score': title_score,
            'content_score': content_score + company_bonus,
            'skills_score': skill_score,
            'action_verbs_score': action_verbs_score
        }
    
    def _score_action_verbs(self, text: str) -> float:
        """Score based on creative action verbs in text"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        verb_count = 0
        
        for verb in self.creative_action_verbs:
            if verb in text_lower:
                verb_count += 1
        
        # Normalize score
        return min(1.0, verb_count / 3)  # 3 verbs = 100% score
    
    def _calculate_skills_score(self, skills: str) -> float:
        """Calculate score based on creative skills mentioned"""
        if not skills:
            return 0.3  # Default score if no skills specified
        
        skills_lower = skills.lower()
        creative_skill_count = 0
        total_skills = 0
        
        # Count lines as potential skills
        skill_lines = [s.strip() for s in skills_lower.split('\n') if s.strip()]
        total_skills = len(skill_lines)
        
        for skill in skill_lines:
            # Check if this skill contains any creative keyword
            if any(keyword in skill for keyword in self.creative_skills):
                creative_skill_count += 1
            elif any(keyword in skill for keyword in self.creative_job_keywords):
                creative_skill_count += 0.5  # Partial credit for job keywords
        
        if total_skills == 0:
            return 0.3
        
        return creative_skill_count / max(total_skills, 1)
    
    def _extract_categories_from_text(self, text: str) -> List[str]:
        """Extract creative categories from text"""
        text_lower = text.lower()
        categories = []
        category_scores = {}
        
        for category, keywords in self.creative_categories.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            
            if score > 0:
                categories.append(category)
                category_scores[category] = score
        
        # Sort by score
        categories.sort(key=lambda x: category_scores.get(x, 0), reverse=True)
        return categories[:3]
    
    def _score_creative_content(self, text: str, is_job: bool = False) -> float:
        """Score how creative a piece of text is - IMPROVED"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        
        # Count matches from multiple sources
        matches = 0
        
        if is_job:
            # For jobs, check job keywords
            for keyword in self.creative_job_keywords:
                if keyword in text_lower:
                    matches += 1
        else:
            # For regular posts, check all creative keywords
            for keywords in self.creative_categories.values():
                for keyword in keywords:
                    if keyword in text_lower:
                        matches += 1
        
        # Also check for creative action verbs
        for verb in self.creative_action_verbs:
            if verb in text_lower:
                matches += 0.5  # Half weight for verbs
        
        # Normalize score
        max_matches = 5  # Cap at 5 matches for 100% score
        return min(matches / max_matches, 1.0)
    
    def _manual_classify_text(self, text: str) -> Dict[str, Any]:
        """Manual text classification using keywords"""
        text_lower = text.lower()
        
        # Count creative keyword matches
        creative_matches = 0
        detected_categories = []
        category_matches = {}
        
        for category, keywords in self.creative_categories.items():
            category_match_count = 0
            for keyword in keywords:
                if keyword in text_lower:
                    category_match_count += 1
                    creative_matches += 1
            
            if category_match_count > 0:
                detected_categories.append(category)
                category_matches[category] = category_match_count
        
        # Calculate score based on matches
        score = min(creative_matches / 3, 1.0)  # Cap at 3 matches = 100%
        
        # Sort categories by match count
        detected_categories.sort(key=lambda x: category_matches.get(x, 0), reverse=True)
        
        if score > 0.5:
            reason = f"Strong creative content detected"
        elif score > 0.2:
            reason = f"Creative content detected"
        else:
            reason = "Little to no creative content detected"
        
        return {
            'score': score,
            'confidence': score,
            'reason': reason,
            'categories': detected_categories[:3]
        }
    
    def _check_non_creative_keywords(self, text: str) -> float:
        """Check for non-creative keywords (returns penalty score)"""
        text_lower = text.lower()
        
        non_creative_keywords = [
            'business intelligence', 'business', 'finance', 'accounting', 'sales', 'marketing', 'real estate',
            'insurance', 'banking', 'stock', 'investment', 'trading', 'crypto', 'bitcoin',
            'medical', 'healthcare', 'doctor', 'nurse', 'hospital', 'pharmacy', 'surgery',
            'engineering', 'mechanical', 'civil', 'electrical', 'construction',
            'logistics', 'supply chain', 'manufacturing', 'factory', 'production', 'assembly',
            'legal', 'lawyer', 'attorney', 'court', 'law', 'regulation', 'contract',
            'science', 'research', 'laboratory', 'chemistry', 'physics', 'biology', 'mathematics',
            'administration', 'management', 'hr', 'human resources', 'recruitment', 'operations',
            'data analysis', 'data science', 'machine learning', 'ai engineering', 'software development',
            'customer service', 'support', 'technical support', 'it support'
        ]
        
        penalty = 0
        for keyword in non_creative_keywords:
            if keyword in text_lower:
                penalty += 0.1  # 10% penalty per non-creative keyword
        
        # Convert penalty to score (1 - penalty, min 0)
        return max(1.0 - min(penalty, 0.5), 0.0)  # Max 50% penalty
    
    def _is_creative_company(self, company_name: str) -> bool:
        """Check if company name suggests creative industry"""
        if not company_name:
            return False
            
        company_lower = company_name.lower()
        creative_company_keywords = [
            'studio', 'creative', 'design', 'art', 'media', 'production',
            'gallery', 'atelier', 'workshop', 'lab', 'collective', 'agency',
            'arts', 'creative', 'designs', 'productions', 'films', 'music',
            'publishing', 'fashion', 'interior', 'architecture', 'culinary',
            'theater', 'theatre', 'orchestra', 'opera', 'ballet', 'dance',
            'record', 'label', 'entertainment', 'creative', 'innovation'
        ]
        
        return any(keyword in company_lower for keyword in creative_company_keywords)
    
    def _generate_job_suggestions(self, title: str, content: str, job_fields: Dict, score: float) -> List[str]:
        """Generate suggestions for job posts"""
        suggestions = []
        full_text = f"{title} {content}".lower()
        
        # Check for missing elements
        has_specific_title = any(keyword in title.lower() for keyword in self.creative_job_keywords)
        has_creative_verbs = any(verb in full_text for verb in self.creative_action_verbs)
        has_skills = bool(job_fields.get('skills_required', '').strip())
        has_tools = any(tool in full_text for tool in self.creative_skills)
        
        if not has_specific_title:
            suggestions.append("Use a more specific creative job title (e.g., 'Pianist', 'Graphic Designer', 'Content Writer')")
        
        if not has_creative_verbs:
            suggestions.append("Include creative action verbs like 'create', 'design', 'compose', 'perform', 'develop'")
        
        if not has_skills:
            suggestions.append("List specific creative skills required (e.g., 'sight-reading', 'composition', 'improvisation')")
        
        if not has_tools:
            suggestions.append("Mention creative tools or software (e.g., 'Pro Tools', 'Adobe Creative Suite', 'specific instruments')")
        
        # Add general suggestions if still needed
        if len(suggestions) < 2:
            suggestions.append("Highlight creative benefits like artistic freedom, creative collaboration, or portfolio building")
            suggestions.append("Mention opportunities for creative growth or skill development")
        
        return suggestions[:3]
    
    def _generate_suggestions(self, text: str, categories: List[str], score: float) -> List[str]:
        """Generate suggestions to make content more creative"""
        suggestions = []
        text_lower = text.lower()
        
        if score < 0.3:
            # Very low score - basic suggestions
            suggestions = [
                "Consider adding more details about the creative process or inspiration",
                "Mention specific artistic techniques, tools, or software used",
                "Share what inspired this work or the story behind it",
                "Include more descriptive language about colors, textures, emotions, or style",
                "Reference other artists, art movements, or creative influences"
            ]
        elif score < 0.6:
            # Medium score - targeted suggestions
            
            # Check for specific missing elements
            has_visual_desc = any(word in text_lower for word in ['color', 'texture', 'style', 'design', 'shape', 'form'])
            has_process_desc = any(word in text_lower for word in ['create', 'make', 'build', 'design', 'draw', 'paint', 'sculpt'])
            has_inspiration = any(word in text_lower for word in ['inspire', 'influence', 'motivate', 'idea', 'concept'])
            
            if not has_visual_desc:
                suggestions.append("Describe visual elements like colors, textures, composition, or style")
            if not has_process_desc:
                suggestions.append("Explain your creative process - how you made this")
            if not has_inspiration:
                suggestions.append("Share what inspired this work - other artists, nature, emotions, etc.")
            
            # Add category-specific suggestions
            if categories:
                main_category = categories[0]
                if main_category == 'visual_arts':
                    suggestions.append("Mention the medium (oil, acrylic, digital, etc.) and techniques used")
                elif main_category == 'design':
                    suggestions.append("Explain the design problem you solved and your creative solution")
                elif main_category == 'culinary_arts':
                    suggestions.append("Describe flavors, ingredients, and presentation techniques")
                elif main_category == 'performing_arts':
                    suggestions.append("Share the emotion or story you're expressing through performance")
                elif main_category == 'literary_arts':
                    suggestions.append("Explain your writing style, voice, or narrative techniques")
            
            # If still empty, add general suggestions
            if not suggestions:
                suggestions.append("Try to make the creative aspect more explicit and detailed")
                suggestions.append("Use more descriptive and expressive language")
        
        else:
            # High score - minimal suggestions
            suggestions.append("Great job! Your content is already very creative.")
        
        return suggestions[:3]

# Singleton instance
_validator_instance = None

def get_validator():
    """Get or create validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = ContentValidator(use_lightweight_model=True)
    return _validator_instance

def validate_content(content_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main function to validate content"""
    validator = get_validator()
    return validator.validate_post(content_data)