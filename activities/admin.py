from django.contrib import admin

from .models import Activity


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['id', 'lead', 'activity_type', 'completed', 'created_at']
    list_filter = ['activity_type', 'completed', 'created_at']
    search_fields = ['title', 'notes', 'lead__first_name', 'lead__last_name']
    ordering = ['-created_at']
