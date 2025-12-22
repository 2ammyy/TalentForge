"""
AI Content Validator for Creative Fields
Checks if posts are related to creative/artistic fields
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

# Default creative categories (used if database is not available)
DEFAULT_CREATIVE_CATEGORIES = {
    'visual_arts': [
        'painting', 'drawing', 'sculpture', 'illustration', 'digital art', 
        'photography', 'graphic design', 'animation', '3d modeling', 'concept art',
        'watercolor', 'oil painting', 'sketch', 'portrait', 'landscape',
        'character design', 'storyboard', 'comic', 'manga', 'anime'
    ],
    'design': [
        'ui/ux design', 'web design', 'product design', 'fashion design', 
        'interior design', 'graphic design', 'industrial design', 'logo design',
        'brand identity', 'typography', 'layout', 'packaging design',
        'motion design', 'exhibition design', 'set design', 'costume design'
    ],
    'culinary_arts': [
        'cooking', 'baking', 'pastry', 'food styling', 'culinary arts', 
        'cake design', 'chocolate art', 'food photography', 'recipe development',
        'plating', 'gastronomy', 'mixology', 'food art', 'culinary arts'
    ],
    'performing_arts': [
        'music', 'dance', 'theater', 'acting', 'singing', 'instrument', 
        'performance art', 'stand-up comedy', 'orchestra', 'choir',
        'piano', 'guitar', 'violin', 'drums', 'composition', 'songwriting',
        'choreography', 'directing', 'producing', 'screenwriting'
    ],
    'literary_arts': [
        'writing', 'poetry', 'fiction', 'creative writing', 'screenwriting', 
        'copywriting', 'storytelling', 'novel', 'short story', 'playwriting',
        'blogging', 'journalism', 'editing', 'publishing', 'translation'
    ],
    'crafts': [
        'pottery', 'woodworking', 'jewelry making', 'textile arts', 
        'calligraphy', 'glass blowing', 'ceramics', 'knitting', 'crochet',
        'embroidery', 'weaving', 'leatherworking', 'metalworking', 'origami',
        'arabic calligraphy', 'خط عربي'
    ],
    'media_entertainment': [
        'film making', 'video editing', 'game design', 'animation', 
        'video production', 'sound design', 'vfx', 'cinematography',
        'documentary', 'short film', 'music video', 'podcast', 'streaming'
    ],
    'digital_creativity': [
        'motion graphics', 'digital painting', 'web design', 'app design', 
        'ar/vr design', 'interactive media', '3d animation', 'game development',
        'coding creative', 'creative coding', 'generative art', 'digital art'
    ]
}

# Job-specific keywords to identify creative jobs
CREATIVE_JOB_KEYWORDS = [
    'artist', 'designer', 'creative', 'animator', 'illustrator', 'photographer',
    'musician', 'writer', 'chef', 'baker', 'stylist', 'director', 'editor',
    'architect', 'interior designer', 'graphic designer', 'ui/ux', 'web designer',
    'video editor', 'sound designer', 'game designer', 'art director',
    'content creator', 'copywriter', 'artisan', 'craftsman', 'maker',
    'painter', 'sculptor', 'ceramist', 'calligrapher', 'filmmaker',
    'composer', 'choreographer', 'dancer', 'actor', 'performer',
    'pastry chef', 'food stylist', 'culinary artist', 'mixologist'
]

# Negative keywords (non-creative fields)
NON_CREATIVE_KEYWORDS = [
    'business intelligence', 'business', 'finance', 'accounting', 'sales', 'marketing', 'real estate',
    'insurance', 'banking', 'stock', 'investment', 'trading', 'crypto', 'bitcoin',
    'medical', 'healthcare', 'doctor', 'nurse', 'hospital', 'pharmacy', 'surgery',
    'engineering', 'mechanical', 'civil', 'electrical', 'construction', 'architecture (non-art)',
    'logistics', 'supply chain', 'manufacturing', 'factory', 'production', 'assembly',
    'legal', 'lawyer', 'attorney', 'court', 'law', 'regulation', 'contract',
    'science', 'research', 'laboratory', 'chemistry', 'physics', 'biology', 'mathematics',
    'administration', 'management', 'hr', 'human resources', 'recruitment', 'operations',
    'data analysis', 'data science', 'machine learning', 'ai engineering', 'software development',
    'customer service', 'support', 'technical support', 'it support'
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
        self.non_creative_keywords = NON_CREATIVE_KEYWORDS.copy()
        
        # Initialize AI model if available
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use a MUCH SMALLER model (only 44MB instead of 1.63GB!)
                # This model is specifically trained for zero-shot classification
                if use_lightweight_model:
                    # OPTION 1: Tiny model (fastest)
                    model_name = "facebook/bart-large-mnli"
                    # Actually, let's use manual for now to avoid downloads
                    print("⚠️ Using manual validation to avoid model downloads")
                    self.model_loaded = False
                else:
                    # OPTION 2: Small efficient model
                    model_name = "typeform/distilbert-base-uncased-mnli"
                    self.text_classifier = pipeline(
                        "zero-shot-classification",
                        model=model_name,
                        device=-1  # Use CPU (faster for small models)
                    )
                    self.model_loaded = True
                    print(f"✅ AI model loaded successfully: {model_name}")
            except Exception as e:
                print(f"⚠️ Could not load AI model: {e}")
                print("   Using manual validation only")
                self.model_loaded = False
        else:
            print("⚠️ Transformers library not installed")
            print("   Using manual validation only")
            self.model_loaded = False
        
        # Validation thresholds
        self.threshold_approve = 0.5  # Score >= 0.5 = approved
        self.threshold_warning = 0.3  # Score >= 0.3 = warning, < 0.3 = rejected
    
    def validate_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main validation function for posts
        
        Args:
            post_data: Dictionary containing post information
                - type: 'text', 'image', 'video', 'job'
                - title: post title
                - content: post content
                - image: image file (optional)
                - video: video file (optional)
                - job_fields: dictionary with job-specific fields (for job posts)
        
        Returns:
            Dictionary with validation results
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
        
        # Always use manual classification for now (FASTER)
        # We can enable AI later if needed
        ai_result = self._manual_classify_text(full_text)
        
        # Check against non-creative keywords
        non_creative_score = self._check_non_creative_keywords(full_text)
        
        # Calculate final score (weighted average)
        final_score = (ai_result['score'] * 0.7) + (non_creative_score * 0.3)
        
        # Determine if valid
        is_valid = final_score >= self.threshold_approve
        
        # Generate reason based on score
        if final_score >= 0.7:
            reason = "Excellent creative content!"
        elif final_score >= 0.5:
            reason = "Good creative content"
        elif final_score >= 0.3:
            reason = "Some creative elements, could be improved"
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
    
    def _validate_image_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate image posts"""
        title = post_data.get('title', '')
        content = post_data.get('content', '')
        
        # First validate text content
        text_result = self._validate_text_post({'title': title, 'content': content, 'type': 'text'})
        
        # For now, we'll rely on text analysis
        image_score = 0.5  # Default neutral score
        
        # Combine scores (heavier weight on text)
        final_score = (text_result['score'] * 0.8) + (image_score * 0.2)
        is_valid = final_score >= self.threshold_approve
        
        result = {
            'is_valid': is_valid,
            'score': round(final_score, 3),
            'confidence': text_result['confidence'],
            'reason': text_result['reason'] + " (Image analysis limited)",
            'suggestions': text_result['suggestions'],
            'detected_categories': text_result.get('detected_categories', [])
        }
        
        return result
    
    def _validate_video_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate video posts"""
        title = post_data.get('title', '')
        content = post_data.get('content', '')
        
        # First validate text content
        text_result = self._validate_text_post({'title': title, 'content': content, 'type': 'text'})
        
        # For now, we'll rely on text analysis and filename
        video_score = 0.5
        
        # Check video filename for creative hints
        if 'video' in post_data and post_data['video']:
            filename = str(post_data['video']).lower()
            video_keywords = ['art', 'design', 'music', 'tutorial', 'demo', 'showcase', 'creative', 'animation']
            if any(keyword in filename for keyword in video_keywords):
                video_score = 0.7
        
        # Combine scores
        final_score = (text_result['score'] * 0.7) + (video_score * 0.3)
        is_valid = final_score >= self.threshold_approve
        
        result = {
            'is_valid': is_valid,
            'score': round(final_score, 3),
            'confidence': text_result['confidence'],
            'reason': text_result['reason'] + " (Video analysis limited)",
            'suggestions': text_result['suggestions'],
            'detected_categories': text_result.get('detected_categories', [])
        }
        
        return result
    
    def _validate_job_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate job posts"""
        title = post_data.get('title', '')
        content = post_data.get('content', '')
        job_fields = post_data.get('job_fields', {})
        
        # Check for creative job keywords in title
        title_score = self._score_creative_content(title, is_job=True)
        
        # Check job description
        content_score = self._score_creative_content(content, is_job=True)
        
        # Check company name and skills
        company = job_fields.get('company', '').lower()
        skills = job_fields.get('skills_required', '').lower()
        
        # Extract skills and check for creative skills
        creative_skills_count = 0
        total_skills = 0
        
        if skills:
            skill_list = [s.strip() for s in skills.split('\n') if s.strip()]
            total_skills = len(skill_list)
            for skill in skill_list:
                if self._is_creative_keyword(skill):
                    creative_skills_count += 1
        
        # Calculate skill score
        skill_score = creative_skills_count / max(total_skills, 1)
        
        # Company score (check if company name suggests creative industry)
        company_score = 0.1 if self._is_creative_company(company) else 0
        
        # Combine scores with weights
        scores = {
            'title': title_score * 0.3,
            'content': content_score * 0.4,
            'skills': skill_score * 0.2,
            'company': company_score * 0.1
        }
        
        final_score = sum(scores.values())
        is_valid = final_score >= self.threshold_warning  # Lower threshold for jobs
        
        # Generate reason
        if final_score >= 0.6:
            reason = "Excellent creative job posting!"
        elif final_score >= 0.4:
            reason = "Good creative job posting"
        elif final_score >= 0.3:
            reason = "Some creative elements in job posting"
        else:
            reason = "Job posting doesn't appear to be for creative/artistic roles"
        
        # Generate suggestions
        suggestions = []
        if final_score < 0.4:
            suggestions = [
                "Use more specific creative job titles (e.g., 'Graphic Designer' instead of 'Designer')",
                "Mention creative skills required (e.g., 'Photoshop', 'Illustration', 'UI Design')",
                "Specify creative tools or software used in the role",
                "Highlight creative benefits (e.g., 'creative freedom', 'artistic collaboration')",
                "Include examples of creative work expected"
            ]
        
        return {
            'is_valid': is_valid,
            'score': round(final_score, 3),
            'confidence': round(final_score, 3),
            'reason': reason,
            'suggestions': suggestions,
            'detected_categories': self._extract_categories_from_job(full_text=f"{title} {content}"),
            'score_breakdown': {k: round(v, 3) for k, v in scores.items()}
        }
    
    def _ai_classify_text(self, text: str) -> Dict[str, Any]:
        """Use AI model to classify text"""
        try:
            if not self.text_classifier:
                return self._manual_classify_text(text)
            
            # Define candidate labels based on creative categories
            candidate_labels = list(self.creative_categories.keys())
            
            # Add some negative labels
            candidate_labels.extend(['business', 'technology', 'science', 'other', 'education'])
            
            # Run classification
            result = self.text_classifier(
                text,
                candidate_labels,
                multi_label=False  # Single best label
            )
            
            # Get creative labels (filter out non-creative)
            creative_labels = []
            creative_scores = []
            
            for label, score in zip(result['labels'], result['scores']):
                if label in self.creative_categories:
                    creative_labels.append(label)
                    creative_scores.append(score)
            
            # Calculate average creative score
            creative_score = sum(creative_scores) / len(creative_scores) if creative_scores else 0
            
            # Get top 3 creative categories
            top_categories = creative_labels[:3]
            
            # Generate reason
            if creative_score > 0.7:
                reason = f"Strong creative content detected in: {', '.join(top_categories[:2])}"
            elif creative_score > 0.4:
                reason = f"Creative content detected in: {', '.join(top_categories[:1]) if top_categories else 'general creative'}"
            else:
                reason = "Little creative content detected"
            
            return {
                'score': creative_score,
                'confidence': max(creative_scores) if creative_scores else 0,
                'reason': reason,
                'categories': top_categories
            }
            
        except Exception as e:
            print(f"AI classification failed: {e}")
            return self._manual_classify_text(text)
    
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
        total_keywords_checked = sum(len(keywords) for keywords in self.creative_categories.values())
        score = min(creative_matches / 5, 1.0)  # Cap at 5 matches = 100%
        
        # Sort categories by match count
        detected_categories.sort(key=lambda x: category_matches.get(x, 0), reverse=True)
        
        if score > 0.5:
            reason = f"Creative content detected in: {', '.join(detected_categories[:2])}"
        elif score > 0.2:
            reason = "Some creative elements detected"
        else:
            reason = "Little to no creative content detected"
        
        return {
            'score': score,
            'confidence': score,  # Use score as confidence for manual classification
            'reason': reason,
            'categories': detected_categories[:3]
        }
    
    def _check_non_creative_keywords(self, text: str) -> float:
        """Check for non-creative keywords (returns penalty score)"""
        text_lower = text.lower()
        
        penalty = 0
        for keyword in self.non_creative_keywords:
            if keyword in text_lower:
                penalty += 0.2  # 20% penalty per non-creative keyword
                
                # Extra penalty for business/tech terms
                if keyword in ['business intelligence', 'data science', 'software development']:
                    penalty += 0.3
        
        # Convert penalty to score (1 - penalty, min 0)
        return max(1.0 - min(penalty, 1.0), 0.0)
    
    def _score_creative_content(self, text: str, is_job: bool = False) -> float:
        """Score how creative a piece of text is"""
        if not text:
            return 0.0
        
        text_lower = text.lower()
        
        # Count creative keyword matches
        creative_matches = 0
        
        if is_job:
            keywords = self.creative_job_keywords
        else:
            # Flatten all creative category keywords
            keywords = []
            for cat_keywords in self.creative_categories.values():
                keywords.extend(cat_keywords)
        
        # Check for keyword matches
        for keyword in keywords:
            if keyword in text_lower:
                creative_matches += 1
        
        # Normalize score (0-1)
        max_matches = 5  # Cap at 5 matches for 100% score
        score = min(creative_matches / max_matches, 1.0)
        
        return score
    
    def _is_creative_keyword(self, text: str) -> bool:
        """Check if text contains creative keywords"""
        text_lower = text.lower()
        
        # Check all creative categories
        for keywords in self.creative_categories.values():
            if any(keyword in text_lower for keyword in keywords):
                return True
        
        # Check creative job keywords
        if any(keyword in text_lower for keyword in self.creative_job_keywords):
            return True
        
        return False
    
    def _is_creative_company(self, company_name: str) -> bool:
        """Check if company name suggests creative industry"""
        if not company_name:
            return False
            
        company_lower = company_name.lower()
        creative_company_keywords = [
            'studio', 'creative', 'design', 'art', 'media', 'production',
            'gallery', 'atelier', 'workshop', 'lab', 'collective', 'agency',
            'arts', 'creative', 'designs', 'productions', 'films', 'music',
            'publishing', 'fashion', 'interior', 'architecture', 'culinary'
        ]
        
        return any(keyword in company_lower for keyword in creative_company_keywords)
    
    def _extract_categories_from_job(self, full_text: str) -> List[str]:
        """Extract creative categories from job text"""
        text_lower = full_text.lower()
        categories = []
        
        for category, keywords in self.creative_categories.items():
            for keyword in keywords:
                if keyword in text_lower and category not in categories:
                    categories.append(category)
                    break  # Found one keyword, move to next category
        
        return categories[:3]
    
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
        
        return suggestions[:3]  # Return top 3 suggestions

# Singleton instance
_validator_instance = None

def get_validator():
    """Get or create validator instance"""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = ContentValidator(use_lightweight_model=False)  # No AI model for now
    return _validator_instance

def validate_content(content_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main function to validate content"""
    validator = get_validator()
    return validator.validate_post(content_data)