from django.apps import AppConfig

class PostsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'posts'
    verbose_name = 'Posts'
    
    def ready(self):
        # Import signals module
        try:
            import posts.signals
        except ImportError as e:
            print(f"⚠️ Could not import posts signals: {e}")