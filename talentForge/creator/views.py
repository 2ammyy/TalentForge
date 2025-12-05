# creator/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
import json
from .models import CreatorProfile
from .ai_utils import AICreatorAssistant 

@login_required
def creator_dashboard(request):
    """Main creator dashboard with AI features"""
    print(f"\n=== DASHBOARD ACCESS: {request.user.username} ===")
    
    creator_profile, created = CreatorProfile.objects.get_or_create(user=request.user)
    
    # Sync followers
    actual_followers = creator_profile.sync_with_user_profile()
    print(f"Followers after sync: {actual_followers}")
    
    # Check if user should have access
    if actual_followers < 1:
        from django.contrib import messages
        messages.error(request, f"You need at least 1 follower to access Creator Dashboard. You have {actual_followers} followers.")
        from django.shortcuts import redirect
        return redirect('home')
    
    # Auto-upgrade if eligible
    if actual_followers >= 1 and not creator_profile.is_verified:
        print(f"Auto-upgrading {request.user.username} to creator")
        creator_profile.upgrade_to_creator()
    
    # Refresh
    creator_profile.refresh_from_db()
    
    # =========== NEW AI FEATURES ===========
    # Initialize AI Assistant
    ai_assistant = AICreatorAssistant(creator_profile)
    
    # Get AI predictions and insights
    ai_predictions = ai_assistant.get_smart_predictions()
    performance_summary = ai_assistant.get_performance_summary()
    
    # Calculate engagement rate if needed
    if creator_profile.followers_count > 0:
        engagement_rate = round(creator_profile.engagement_rate, 1)
    else:
        engagement_rate = 0.0
    
    context = {
        'creator_profile': creator_profile,
        'real_time_stats': {
            'followers_count': actual_followers,
            'total_posts': creator_profile.total_posts,
            'total_likes': creator_profile.total_likes,
            'total_comments': creator_profile.total_comments,
            'engagement_rate': engagement_rate,
        },
        # ===== NEW AI CONTEXT =====
        'ai_predictions': ai_predictions,
        'performance_summary': performance_summary,
        'engagement_insights': ai_predictions['engagement_insights'],
    }
    
    print(f"Rendering dashboard for {request.user.username} with AI features")
    return render(request, 'creator/dashboard.html', context)

    
@login_required
def creator_analytics(request):
    """Page analytics simplifiée"""
    creator_profile, created = CreatorProfile.objects.get_or_create(user=request.user)
    
    # 🔥 ADD THIS LINE: Sync with actual follower count
    actual_followers = creator_profile.sync_with_user_profile()
    
    context = {
        'creator_profile': creator_profile,
        'real_time_stats': {
            'followers_count': actual_followers,  # Use the synced count
            'total_posts': creator_profile.total_posts,
            'total_likes': creator_profile.total_likes,
            'engagement_rate': round(creator_profile.engagement_rate, 1),
        }
    }
    
    return render(request, 'creator/analytics.html', context)

@login_required
def api_creator_stats(request):
    """API pour les données en temps réel (AJAX)"""
    creator_profile, created = CreatorProfile.objects.get_or_create(user=request.user)
    
    # 🔥 ADD THIS LINE: Sync with actual follower count
    actual_followers = creator_profile.sync_with_user_profile()
    
    data = {
        'followers_count': actual_followers,  # Use the synced count
        'total_posts': creator_profile.total_posts,
        'total_likes': creator_profile.total_likes,
        'total_comments': creator_profile.total_comments,
        'engagement_rate': round(creator_profile.engagement_rate, 1),
        'is_verified': creator_profile.is_verified,
    }
    
    return JsonResponse(data)

@login_required
@require_http_methods(["POST"])
def generate_prediction(request):
    """Prédictions IA basées sur les données réelles"""
    try:
        creator_profile, created = CreatorProfile.objects.get_or_create(user=request.user)
        
        # 🔥 ADD THIS LINE: Sync with actual follower count
        actual_followers = creator_profile.sync_with_user_profile()
        
        data = json.loads(request.body)
        prediction_type = data.get('prediction_type', 'follower_growth')
        
        # Prédictions basées sur les données réelles
        current_followers = actual_followers  # Use synced count
        current_engagement = creator_profile.engagement_rate
        
        if prediction_type == 'follower_growth':
            predicted_growth = max(1, current_followers // 10)  # Croissance minimale de 10%
            prediction = {
                'value': f"+{predicted_growth} followers",
                'confidence': min(85 + (current_followers // 10), 95),
                'explanation': f'Basé sur vos {current_followers} followers actuels'
            }
        elif prediction_type == 'engagement':
            predicted_engagement = current_engagement * 1.05  # 5% d'augmentation
            prediction = {
                'value': f"{predicted_engagement:.1f}%",
                'confidence': 78,
                'explanation': 'Amélioration attendue basée sur la performance de votre contenu'
            }
        else:
            prediction = {
                'value': "Données insuffisantes",
                'confidence': 50,
                'explanation': 'Collecte de données en cours...'
            }
        
        return JsonResponse({
            'success': True,
            'prediction': prediction,
            'based_on_real_data': True
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@login_required
def check_eligibility(request):
    """Vérifier l'éligibilité en temps réel"""
    creator_profile, created = CreatorProfile.objects.get_or_create(user=request.user)
    
    # 🔥 ADD THIS LINE: Sync with actual follower count
    actual_followers = creator_profile.sync_with_user_profile()
    
    # 1 seul follower suffit !
    eligible = actual_followers >= 1
    is_creator = creator_profile.is_verified
    
    return JsonResponse({
        'eligible': eligible,
        'is_creator': is_creator,
        'current_followers': actual_followers,
        'needed_followers': max(0, 1 - actual_followers)
    })

@login_required
def upgrade_to_creator(request):
    """Mise à niveau en créateur"""
    creator_profile, created = CreatorProfile.objects.get_or_create(user=request.user)
    
    # 🔥 ADD THIS LINE: Sync with actual follower count
    actual_followers = creator_profile.sync_with_user_profile()
    
    if actual_followers >= 1:
        success = creator_profile.upgrade_to_creator()
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Félicitations ! Vous êtes maintenant un créateur vérifié !'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Échec de la mise à niveau'
            })
    else:
        return JsonResponse({
            'success': False,
            'error': f'Vous avez {actual_followers} follower(s). 1 follower est requis.'
        })