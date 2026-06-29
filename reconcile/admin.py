from django.contrib import admin
from .models import ReconciliationConfig, ReconciliationField, ReconciliationSession, ReconciliationResult


class ReconciliationFieldInline(admin.TabularInline):
    model = ReconciliationField
    extra = 0


@admin.register(ReconciliationConfig)
class ReconciliationConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['name']
    inlines = [ReconciliationFieldInline]


@admin.register(ReconciliationSession)
class ReconciliationSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'config', 'status', 'total_records_a', 'total_records_b', 
                    'matched_count', 'only_a_count', 'only_b_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['file_a_name', 'file_b_name']
    readonly_fields = ['created_at', 'completed_at']


@admin.register(ReconciliationResult)
class ReconciliationResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['match_key']
    readonly_fields = ['created_at']