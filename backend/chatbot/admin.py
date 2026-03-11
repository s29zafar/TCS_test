from django.contrib import admin
from .models import Conversation, Message

class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('timestamp',)

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'created_at', 'updated_at')
    inlines = [MessageInline]

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'text_excerpt', 'timestamp')
    list_filter = ('sender', 'timestamp')
    
    def text_excerpt(self, obj):
        return obj.text[:50]
    text_excerpt.short_description = 'Text'
