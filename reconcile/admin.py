from django.contrib import admin
from .models import (
    ReconciliationConfig, ReconciliationField, FieldMapping, 
    ReconciliationRule, ReconciliationSession, ReconciliationResult
)


class ReconciliationFieldInline(admin.TabularInline):
    model = ReconciliationField
    extra = 1
    fields = ['field_name', 'data_type', 'sequence']


class FieldMappingInline(admin.TabularInline):
    model = FieldMapping
    extra = 1
    fields = ['field', 'file_type', 'excel_column']


class ReconciliationRuleInline(admin.TabularInline):
    model = ReconciliationRule
    extra = 1
    fields = ['left_field', 'right_field', 'operator', 'sequence']


@admin.register(ReconciliationConfig)
class ReconciliationConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    inlines = [ReconciliationFieldInline, FieldMappingInline, ReconciliationRuleInline]


@admin.register(ReconciliationField)
class ReconciliationFieldAdmin(admin.ModelAdmin):
    list_display = ['id', 'field_name', 'data_type', 'config', 'sequence']
    list_filter = ['data_type', 'config']
    search_fields = ['field_name']


@admin.register(FieldMapping)
class FieldMappingAdmin(admin.ModelAdmin):
    list_display = ['id', 'config', 'field', 'file_type', 'excel_column']
    list_filter = ['file_type', 'config']
    search_fields = ['excel_column']


@admin.register(ReconciliationRule)
class ReconciliationRuleAdmin(admin.ModelAdmin):
    list_display = ['id', 'config', 'left_field', 'right_field', 'operator', 'sequence']
    list_filter = ['config', 'operator']
    search_fields = ['left_field__excel_column', 'right_field__excel_column']


@admin.register(ReconciliationSession)
class ReconciliationSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'config', 'status', 'total_a', 'total_b', 
                    'matched', 'only_a', 'only_b', 'created_at']
    list_filter = ['status', 'created_at', 'config']
    search_fields = ['file_a', 'file_b']
    readonly_fields = ['created_at']


@admin.register(ReconciliationResult)
class ReconciliationResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['match_key']
    readonly_fields = ['created_at']