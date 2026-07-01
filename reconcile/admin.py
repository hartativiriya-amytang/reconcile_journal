from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import json
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
    list_display = ['id', 'name', 'description', 'is_active', 'fields_count', 'sessions_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    inlines = [ReconciliationFieldInline, FieldMappingInline, ReconciliationRuleInline]
    list_select_related = True

    def fields_count(self, obj):
        return obj.fields.count()
    fields_count.short_description = 'Fields'

    def sessions_count(self, obj):
        count = obj.reconciliationsession_set.count()
        url = reverse('admin:reconcile_reconciliationsession_changelist') + f'?config__id__exact={obj.id}'
        return format_html('<a href="{}">{}</a>', url, count)
    sessions_count.short_description = 'Sessions'


@admin.register(ReconciliationField)
class ReconciliationFieldAdmin(admin.ModelAdmin):
    list_display = ['id', 'field_name', 'data_type', 'config', 'sequence']
    list_filter = ['data_type', 'config']
    search_fields = ['field_name']
    list_select_related = ['config']


@admin.register(FieldMapping)
class FieldMappingAdmin(admin.ModelAdmin):
    list_display = ['id', 'config', 'field', 'file_type', 'excel_column']
    list_filter = ['file_type', 'config']
    search_fields = ['excel_column']
    list_select_related = ['config', 'field']


@admin.register(ReconciliationRule)
class ReconciliationRuleAdmin(admin.ModelAdmin):
    list_display = ['id', 'config', 'left_field', 'right_field', 'operator', 'sequence']
    list_filter = ['config', 'operator']
    search_fields = ['left_field__excel_column', 'right_field__excel_column']
    list_select_related = ['config', 'left_field', 'right_field']


@admin.register(ReconciliationSession)
class ReconciliationSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'config', 'status_badge', 'total_a', 'total_b', 
                    'matched', 'only_a', 'only_b', 'match_rate_display', 'created_at', 'session_actions']
    list_filter = ['status', 'created_at', 'config']
    search_fields = ['file_a_name', 'file_b_name']
    readonly_fields = ['created_at', 'finished_at', 'total_a', 'total_b', 
                       'matched', 'only_a', 'only_b', 'error_message']
    list_select_related = ['config']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Session Info', {
            'fields': ('config', 'status', 'created_at', 'finished_at')
        }),
        ('Files', {
            'fields': ('file_a_name', 'file_a_path', 'file_b_name', 'file_b_path')
        }),
        ('Results Summary', {
            'fields': ('total_a', 'total_b', 'matched', 'only_a', 'only_b')
        }),
        ('Error', {
            'fields': ('error_message',),
            'classes': ('collapse',),
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending': 'warning',
            'processing': 'info',
            'completed': 'success',
            'failed': 'danger',
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'

    def match_rate_display(self, obj):
        if obj.total_a > 0:
            rate = (obj.matched / obj.total_a) * 100
            color = 'green' if rate >= 80 else ('orange' if rate >= 50 else 'red')
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color, rate
            )
        return '-'
    match_rate_display.short_description = 'Match Rate'
    match_rate_display.admin_order_field = 'matched'

    def session_actions(self, obj):
        if obj.status != 'completed':
            return '-'
        return format_html(
            '<a class="btn btn-xs btn-success mr-1" href="{}" title="Download Matched">'
            '<i class="fas fa-check"></i></a>'
            '<a class="btn btn-xs btn-warning mr-1" href="{}" title="Download Unmatched">'
            '<i class="fas fa-times"></i></a>'
            '<a class="btn btn-xs btn-info" href="{}" title="Download Summary">'
            '<i class="fas fa-file-excel"></i></a>',
            reverse('reconcile:download_matched', args=[obj.id]),
            reverse('reconcile:download_unmatched', args=[obj.id]),
            reverse('reconcile:download_summary', args=[obj.id]),
        )
    session_actions.short_description = 'Actions'


@admin.register(ReconciliationResult)
class ReconciliationResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'session_link', 'status_badge', 'match_key_short', 'data_preview', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['match_key']
    readonly_fields = ['created_at']
    list_select_related = ['session']

    def session_link(self, obj):
        url = reverse('admin:reconcile_reconciliationsession_change', args=[obj.session_id])
        return format_html('<a href="{}">Session #{}</a>', url, obj.session_id)
    session_link.short_description = 'Session'
    session_link.admin_order_field = 'session'

    def status_badge(self, obj):
        colors = {'MATCH': 'success', 'ONLY_A': 'warning', 'ONLY_B': 'danger'}
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge badge-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def match_key_short(self, obj):
        if len(obj.match_key) > 16:
            return f'{obj.match_key[:16]}...'
        return obj.match_key
    match_key_short.short_description = 'Match Key'

    def data_preview(self, obj):
        preview = {}
        if obj.file_a_data:
            preview['File A'] = dict(list(obj.file_a_data.items())[:3])
        if obj.file_b_data:
            preview['File B'] = dict(list(obj.file_b_data.items())[:3])
        if not preview:
            return '-'
        return format_html(
            '<pre style="max-height:80px;overflow:auto;font-size:10px;">{}</pre>',
            json.dumps(preview, indent=2)[:200]
        )
    data_preview.short_description = 'Data Preview'