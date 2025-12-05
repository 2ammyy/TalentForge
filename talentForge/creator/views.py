# creator/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
import json
from .models import CreatorProfile

@login_required
def creator_dashboard(request):
    """Dashboard principal en temps réel"""
    creator_profile, created = CreatorProfile.objects.get_or_create(user=request.user)
    
    # Vérifier et mettre à niveau automatiquement si éligible
    if not creator_profile.is_verified and creator_profile.followers_count >= 1:
        creator_profile.upgrade_to_creator()
    
    # Données en temps réel
    real_time_stats = {
        'followers_count': creator_profile.followers_count,
        'total_posts': creator_profile.total_posts,
        'total_likes': creator_profile.total_likes,
        'total_comments': creator_profile.total_comments,
        'engagement_rate': round(creator_profile.engagement_rate, 1),
    }
    
    context = {
        'creator_profile': creator_profile,
        'real_time_stats': real_time_stats,
    }
    
    return render(request, 'creator/dashboard.html', context)

@login_required
def creator_analytics(request):
    """Page analytics simplifiée"""
    creator_profile, created = CreatorProfile.objects.get_or_create(user=request.user)
    
    context = {
        'creator_profile': creator_profile,
        'real_time_stats': {
            'followers_count': creator_profile.followers_count,
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
    
    data = {
        'followers_count': creator_profile.followers_count,
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
        data = json.loads(request.body)
        prediction_type = data.get('prediction_type', 'follower_growth')
        
        # Prédictions basées sur les données réelles
        current_followers = creator_profile.followers_count
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
    
    # 1 seul follower suffit !
    eligible = creator_profile.followers_count >= 1
    is_creator = creator_profile.is_verified
    
    return JsonResponse({
        'eligible': eligible,
        'is_creator': is_creator,
        'current_followers': creator_profile.followers_count,
        'needed_followers': max(0, 1 - creator_profile.followers_count)
    })

@login_required
def upgrade_to_creator(request):
    """Mise à niveau en créateur"""
    creator_profile, created = CreatorProfile.objects.get_or_create(user=request.user)
    
    if creator_profile.followers_count >= 1:
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
            'error': f'Vous avez {creator_profile.followers_count} follower(s). 1 follower est requis.'
        })