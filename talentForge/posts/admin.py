from django.contrib import admin
from .models import Post, Comment, Reaction, Notification  

# Register your models here.

admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Reaction)
admin.site.register(Notification)