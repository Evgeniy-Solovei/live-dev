from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.decorators import display

from leads.models import Lead


@admin.register(Lead)
class LeadAdmin(ModelAdmin):
    list_display = ('name', 'contact', 'status_badge', 'country', 'city', 'created_at')
    list_filter = ('status', 'country', 'source')
    search_fields = ('name', 'contact', 'message', 'ip_address')
    readonly_fields = ('ip_address', 'user_agent', 'country', 'city', 'created_at', 'updated_at', 'page_url', 'source')
    list_editable = ()
    date_hierarchy = 'created_at'
    fieldsets = (
        (None, {'fields': ('name', 'contact', 'message', 'status', 'admin_note')}),
        ('Техданные', {'classes': ('collapse',), 'fields': ('source', 'page_url', 'ip_address', 'country', 'city', 'user_agent', 'created_at', 'updated_at')}),
    )

    @display(description='Статус')
    def status_badge(self, obj):
        return obj.get_status_display()
