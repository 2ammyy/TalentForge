# creator/admin.py
from django.contrib import admin
from .models import CreatorProfile, CreatorStat

# Modèles de base seulement pour l'instant
@admin.register(CreatorProfile)
class CreatorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_verified', 'followers_count', 'total_posts', 'engagement_rate']
    list_filter = ['is_verified', 'join_date']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['join_date']
    
    def followers_count(self, obj):
        return obj.followers_count
    followers_count.short_description = 'Followers'
    
    def total_posts(self, obj):
        return obj.total_posts
    total_posts.short_description = 'Posts'
    
    def engagement_rate(self, obj):
        return f"{obj.engagement_rate:.1f}%"
    engagement_rate.short_description = 'Engagement'

@admin.register(CreatorStat)
class CreatorStatAdmin(admin.ModelAdmin):
    list_display = ['creator', 'date', 'followers', 'posts', 'likes']
    list_filter = ['date']
    search_fields = ['creator__user__username']

# Commenter les autres modèles pour l'instant - nous les ajouterons plus tard
# @admin.register(Collaboration)
# class CollaborationAdmin(admin.ModelAdmin):
#     list_display = ['title', 'creator', 'collaborator', 'status', 'created_at']
#     list_filter = ['status', 'created_at']
#     search_fields = ['title', 'creator__user__username']

# @admin.register(AdCampaign)
# class AdCampaignAdmin(admin.ModelAdmin):
#     list_display = ['title', 'creator', 'budget', 'is_active', 'start_date']
#     list_filter = ['is_active', 'start_date']
#     search_fields = ['title', 'creator__user__username']