# creator/ai_utils.py
from datetime import datetime, timedelta
from django.utils import timezone
from posts.models import Follow, Post

class AICreatorAssistant:
    """AI Assistant for Creators - Simple & Effective"""
    
    def __init__(self, creator_profile):
        self.profile = creator_profile
        self.user = creator_profile.user
        
    def get_smart_predictions(self):
        """Get smart predictions based on current data"""
        current_followers = self.profile.followers_count
        current_engagement = self.profile.engagement_rate
        
        return {
            'next_7_days': self._predict_7day_growth(current_followers),
            'next_30_days': self._predict_30day_growth(current_followers),
            'best_posting_times': self._analyze_best_times(),
            'content_recommendations': self._recommend_content(current_engagement),
            'growth_strategy': self._create_strategy(current_followers),
            'calculated_at': datetime.now().strftime("%I:%M %p"),  # 12-hour format
            'engagement_insights': self.get_engagement_insights(),
        }
    
    def _predict_7day_growth(self, current):
        """Predict growth for next 7 days"""
        # Smart algorithm based on follower count
        if current < 10:
            growth_rate = 0.15  # 15% for small accounts
        elif current < 100:
            growth_rate = 0.10  # 10% for growing accounts
        elif current < 1000:
            growth_rate = 0.05  # 5% for established accounts
        else:
            growth_rate = 0.02  # 2% for large accounts
            
        predicted = int(current * growth_rate)
        return f"+{max(1, predicted)}"
    
    def _predict_30day_growth(self, current):
        """Predict growth for next 30 days"""
        weekly = self._predict_7day_growth(current)
        weekly_num = int(''.join(filter(str.isdigit, weekly)))
        monthly = weekly_num * 4  # 4 weeks
        return f"+{max(5, monthly)}"
    
    def _analyze_best_times(self):
        """Analyze best times to post based on engagement patterns"""
        # Get current day and time
        now = datetime.now()
        current_day = now.strftime("%A")
        current_hour = now.hour
        
        # Best times by platform research
        times_by_day = {
            'Monday': ['18:00', '20:00', '22:00'],
            'Tuesday': ['17:00', '19:00', '21:00'],
            'Wednesday': ['18:00', '20:00', '22:00'],
            'Thursday': ['17:00', '19:00', '21:00'],
            'Friday': ['16:00', '18:00', '20:00'],
            'Saturday': ['14:00', '16:00', '18:00'],
            'Sunday': ['15:00', '17:00', '19:00'],
        }
        
        return {
            'today': times_by_day.get(current_day, ['18:00', '20:00']),
            'best_days': ['Friday', 'Saturday', 'Sunday'],
            'peak_hours': ['18:00-20:00', '20:00-22:00'],
            'current_best': f"Today {current_day} at {times_by_day[current_day][0] if current_day in times_by_day else '18:00'}"
        }
    
    def _recommend_content(self, engagement_rate):
        """Personalized content recommendations"""
        recommendations = []
        
        # Based on engagement rate
        if engagement_rate < 2:
            recommendations.extend([
                "Post images with descriptive text",
                "Use 5-7 relevant hashtags",
                "Ask questions to encourage comments",
                "Create simple how-to guides"
            ])
        elif engagement_rate < 5:
            recommendations.extend([
                "Create educational carousel posts",
                "Share daily stories",
                "Do weekly Q&A live sessions",
                "Collaborate with similar creators"
            ])
        else:
            recommendations.extend([
                "Produce video tutorials",
                "Create exclusive content for followers",
                "Start a content series",
                "Host community challenges"
            ])
        
        # Add general tips
        recommendations.extend([
            "Post consistently (3-4 times per week)",
            "Engage with comments within 1 hour",
            "Use trending audio for videos",
            "Share behind-the-scenes content"
        ])
        
        return recommendations[:4]  # Return top 4
    
    def _create_strategy(self, followers):
        """Create personalized growth strategy"""
        if followers < 10:
            return [
                "Goal: Reach 50 followers",
                "Action: Post 1x daily for 30 days",
                "Focus: Short educational content",
                "Metric: Aim for 5% engagement rate"
            ]
        elif followers < 100:
            return [
                "Goal: Reach 500 followers",
                "Action: Engage with 10 similar accounts daily",
                "Focus: Collaborate with micro-influencers",
                "Metric: Grow 10% weekly"
            ]
        elif followers < 1000:
            return [
                "Goal: Reach 5000 followers",
                "Action: Create 1 content series per week",
                "Focus: Monetization through partnerships",
                "Metric: Maintain 3%+ engagement"
            ]
        else:
            return [
                "Goal: Reach 10,000 followers",
                "Action: Build community through exclusive content",
                "Focus: Brand partnerships & sponsorships",
                "Metric: 50% monthly revenue growth"
            ]
    
    def get_engagement_insights(self):
        """Get engagement level insights"""
        engagement = self.profile.engagement_rate
        
        if engagement < 1:
            return {
                'level': 'Low',
                'emoji': '📉',
                'advice': 'Increase posting frequency to 3-4 times weekly',
                'target': 'Target: 3%',
                'color': '#dc3545',  # Red
                'score': 'Needs Improvement'
            }
        elif engagement < 3:
            return {
                'level': 'Average',
                'emoji': '📊',
                'advice': 'Improve visual quality and use more CTAs',
                'target': 'Target: 5%',
                'color': '#ffc107',  # Yellow
                'score': 'Good'
            }
        elif engagement < 6:
            return {
                'level': 'Good',
                'emoji': '🚀',
                'advice': 'Maintain content quality and experiment with new formats',
                'target': 'Target: 8%',
                'color': '#28a745',  # Green
                'score': 'Excellent'
            }
        else:
            return {
                'level': 'Excellent',
                'emoji': '🏆',
                'advice': 'Youre doing great! Consider monetizing your engaged audience',
                'target': 'Target: 10%',
                'color': '#007bff',  # Blue
                'score': 'Outstanding'
            }
    
    def get_performance_summary(self):
        """Get overall performance summary"""
        followers = self.profile.followers_count
        engagement = self.profile.engagement_rate
        
        summary = {
            'followers_status': 'Growing' if followers > 0 else 'Starting',
            'engagement_status': 'High' if engagement > 3 else 'Medium' if engagement > 1 else 'Low',
            'content_score': min(100, max(20, int(engagement * 20))),  # Score out of 100
            'growth_potential': 'High' if followers < 100 else 'Medium' if followers < 1000 else 'Stable',
            'next_milestone': f"{((followers // 100) + 1) * 100} followers",
        }
        
        return summary