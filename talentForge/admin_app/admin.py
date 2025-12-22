from django.contrib import admin
from posts.models import CreativeCategory, ContentValidationLog

@admin.register(CreativeCategory)
class CreativeCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'keyword_count', 'weight', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'keywords']
    list_editable = ['weight', 'is_active']
    
    def keyword_count(self, obj):
        return len(obj.keyword_list)
    keyword_count.short_description = 'Keywords'

@admin.register(ContentValidationLog)
class ContentValidationLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'post_title', 'user', 'score', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['post__title', 'user__username']
    readonly_fields = ['created_at']
    
    def post_title(self, obj):
        return obj.post.title if obj.post else 'N/A'
    post_title.short_description = 'Post'