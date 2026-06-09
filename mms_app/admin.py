from django.contrib import admin
from .models import Material, MaintenanceTask, SystemAlert, AIConversation

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity', 'unit', 'min_required', 'status')
    list_filter = ('category',)
    search_fields = ('name',)

@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'priority', 'assigned_to', 'due_date')
    list_filter = ('status', 'priority', 'due_date')
    search_fields = ('title', 'description')

@admin.register(SystemAlert)
class SystemAlertAdmin(admin.ModelAdmin):
    list_display = ('message', 'alert_type', 'is_active', 'created_at')
    list_filter = ('alert_type', 'is_active')
    search_fields = ('message',)

@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user_message_excerpt', 'ai_response_excerpt')
    readonly_fields = ('created_at', 'user_message', 'ai_response')

    def user_message_excerpt(self, obj):
        return obj.user_message[:50] + '...' if len(obj.user_message) > 50 else obj.user_message
    user_message_excerpt.short_description = 'User Message'

    def ai_response_excerpt(self, obj):
        return obj.ai_response[:50] + '...' if len(obj.ai_response) > 50 else obj.ai_response
    ai_response_excerpt.short_description = 'AI Response'
