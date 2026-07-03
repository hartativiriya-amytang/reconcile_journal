from django.contrib.admin import AdminSite
from django.contrib import admin
from django.contrib.auth.models import Group, User
from django.contrib.auth.admin import GroupAdmin, UserAdmin
from .models import (
    ReconciliationConfig, ReconciliationField, FieldMapping,
    ReconciliationRule, ReconciliationSession, ReconciliationResult
)

ADMIN_FINANCE_GROUP = 'Admin Finance'


class FinanceAdminSite(AdminSite):
    site_header = 'Admin Finance'
    site_title = 'Admin Finance'
    index_title = 'Panel Administrasi Finance'

    def has_permission(self, request):
        return (
            request.user.is_active and request.user.is_staff and
            (request.user.is_superuser or
             request.user.groups.filter(name=ADMIN_FINANCE_GROUP).exists())
        )


admin_site = FinanceAdminSite(name='finance_admin')


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


class ReconciliationConfigAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    inlines = [ReconciliationFieldInline, FieldMappingInline, ReconciliationRuleInline]


class ReconciliationFieldAdmin(admin.ModelAdmin):
    list_display = ['id', 'field_name', 'data_type', 'config', 'sequence']
    list_filter = ['data_type', 'config']
    search_fields = ['field_name']


class FieldMappingAdmin(admin.ModelAdmin):
    list_display = ['id', 'config', 'field', 'file_type', 'excel_column']
    list_filter = ['file_type', 'config']
    search_fields = ['excel_column']


class ReconciliationRuleAdmin(admin.ModelAdmin):
    list_display = ['id', 'config', 'left_field', 'right_field', 'operator', 'sequence']
    list_filter = ['config', 'operator']


class ReconciliationSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'config', 'status', 'total_a', 'total_b',
                    'matched', 'only_a', 'only_b', 'created_at']
    list_filter = ['status', 'created_at', 'config']
    search_fields = ['file_a_name', 'file_b_name']
    readonly_fields = ['created_at', 'finished_at', 'total_a', 'total_b',
                       'matched', 'only_a', 'only_b', 'error_message']

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


class ReconciliationResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'session', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['match_key']
    readonly_fields = ['created_at']


admin_site.register(ReconciliationConfig, ReconciliationConfigAdmin)
admin_site.register(ReconciliationField, ReconciliationFieldAdmin)
admin_site.register(FieldMapping, FieldMappingAdmin)
admin_site.register(ReconciliationRule, ReconciliationRuleAdmin)
admin_site.register(ReconciliationSession, ReconciliationSessionAdmin)
admin_site.register(ReconciliationResult, ReconciliationResultAdmin)
admin_site.register(Group, GroupAdmin)
admin_site.register(User, UserAdmin)
