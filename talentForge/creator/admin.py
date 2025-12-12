# creator/admin.py - SIMPLEST VERSION
from django.contrib import admin
from .models import CreatorProfile, CreatorStat

@admin.register(CreatorProfile)
class CreatorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_verified', 'followers_count', 'total_posts', 'engagement_rate_display', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def engagement_rate_display(self, obj):
        return f"{obj.engagement_rate:.1f}%"
    engagement_rate_display.short_description = 'Engagement'

@admin.register(CreatorStat)
class CreatorStatAdmin(admin.ModelAdmin):
    list_display = ['creator', 'date', 'followers', 'posts', 'likes']
    list_filter = ['date']
    search_fields = ['creator__user__username']