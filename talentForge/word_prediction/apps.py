from django.apps import AppConfig

class WordPredictionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'word_prediction'
    
    def ready(self):
        # Don't load model here - load only when needed
        pass