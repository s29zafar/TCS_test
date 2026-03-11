from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.admin.site.urls),
    path('api/', include('chatbot.urls')),
]
