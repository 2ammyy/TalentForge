# Create: talentForge/posts/templatetags/mention_filters.py
from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()
@register.filter
def render_mentions(text):
    """Convert @username in text to clickable links"""
    if not text:
        return text
    
    def replace_mention(match):
        username = match.group(1)
        return f'<a href="/posts/profile/{username}/" class="mention">@{username}</a>'
    
    # Replace @username with links
    pattern = r'@([a-zA-Z0-9_]+)'
    text = re.sub(pattern, replace_mention, text)
    
    return mark_safe(text)