from django.apps import AppConfig


class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'

    def ready(self):
        # Optional: Pre-warm the graph on startup
        # We use a try-except to avoid breaking migrations/management commands
        import sys
        if 'runserver' in sys.argv:
            try:
                from .graph import get_graph
                get_graph()
                print("Chatbot graph initialized successfully.")
            except Exception as e:
                print(f"Warning: Chatbot graph failed to initialize on startup: {e}")
