import json
from datetime import datetime

from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.db import transaction
import pandas as pd

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .models import (
    ReconciliationConfig, ReconciliationField, FieldMapping,
    ReconciliationRule, ReconciliationSession, ReconciliationResult
)
from .serializers import (
    ReconciliationConfigSerializer, ReconciliationConfigWriteSerializer,
    ReconciliationFieldSerializer, FieldMappingSerializer,
    ReconciliationRuleSerializer, ReconciliationSessionSerializer,
    ReconciliationResultSerializer, BulkConfigSerializer, ReconcileSerializer
)
from .services.reconciliation import ReconciliationService
from .services.excel_parser import ExcelParser
from .services.export_excel import ExcelExporter


class ReconciliationConfigViewSet(viewsets.ModelViewSet):
    queryset = ReconciliationConfig.objects.all()
    search_fields = ['name', 'description']
    filterset_fields = ['is_active']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ReconciliationConfigWriteSerializer
        return ReconciliationConfigSerializer


class ReconciliationFieldViewSet(viewsets.ModelViewSet):
    queryset = ReconciliationField.objects.all()
    serializer_class = ReconciliationFieldSerializer
    search_fields = ['field_name']
    filterset_fields = ['config', 'data_type']
    ordering = ['sequence']


class FieldMappingViewSet(viewsets.ModelViewSet):
    queryset = FieldMapping.objects.all()
    serializer_class = FieldMappingSerializer
    search_fields = ['excel_column']
    filterset_fields = ['config', 'file_type', 'field']
    ordering = ['id']


class ReconciliationRuleViewSet(viewsets.ModelViewSet):
    queryset = ReconciliationRule.objects.all()
    serializer_class = ReconciliationRuleSerializer
    filterset_fields = ['config', 'operator']
    ordering = ['sequence']


class ReconciliationSessionViewSet(viewsets.ModelViewSet):
    queryset = ReconciliationSession.objects.all()
    serializer_class = ReconciliationSessionSerializer
    search_fields = ['file_a_name', 'file_b_name']
    filterset_fields = ['config', 'status']
    ordering_fields = ['created_at', 'matched', 'total_a']
    ordering = ['-created_at']

    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        session = self.get_object()
        results = session.results.all()
        status_filter = request.query_params.get('status')
        if status_filter:
            results = results.filter(status=status_filter.upper())
        page = self.paginate_queryset(results)
        if page is not None:
            serializer = ReconciliationResultSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ReconciliationResultSerializer(results, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def download_matched(self, request, pk=None):
        session = self.get_object()
        results = session.results.filter(status='MATCH')
        if not results.exists():
            return Response({'error': 'No matched data found'}, status=404)
        fields = session.config.fields.all()
        field_names = [f.field_name for f in fields]
        data = []
        for result in results:
            row = {'Status': 'MATCH'}
            for field in field_names:
                row[f'File_A_{field}'] = result.file_a_data.get(field, '')
                row[f'File_B_{field}'] = result.file_b_data.get(field, '')
            data.append(row)
        df = pd.DataFrame(data)
        return ExcelExporter._create_excel_response(df, f'matched_data_{session.id}.xlsx')

    @action(detail=True, methods=['get'])
    def download_unmatched(self, request, pk=None):
        session = self.get_object()
        only_a = session.results.filter(status='ONLY_A')
        only_b = session.results.filter(status='ONLY_B')
        if not only_a.exists() and not only_b.exists():
            return Response({'error': 'No unmatched data found'}, status=404)
        fields = session.config.fields.all()
        field_names = [f.field_name for f in fields]
        data_a = []
        for result in only_a:
            row = {'Status': 'ONLY_FILE_A'}
            for field in field_names:
                row[field] = result.file_a_data.get(field, '')
            data_a.append(row)
        data_b = []
        for result in only_b:
            row = {'Status': 'ONLY_FILE_B'}
            for field in field_names:
                row[field] = result.file_b_data.get(field, '')
            data_b.append(row)
        from io import BytesIO
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if data_a:
                pd.DataFrame(data_a).to_excel(writer, sheet_name='Only_File_A', index=False)
            if data_b:
                pd.DataFrame(data_b).to_excel(writer, sheet_name='Only_File_B', index=False)
            summary = pd.DataFrame({
                'Metric': ['Only in File A', 'Only in File B'],
                'Count': [len(data_a), len(data_b)]
            })
            summary.to_excel(writer, sheet_name='Summary', index=False)
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=unmatched_data_{session.id}.xlsx'
        return response

    @action(detail=True, methods=['get'])
    def download_summary(self, request, pk=None):
        session = self.get_object()
        data = {
            'Metric': [
                'Session ID', 'Configuration', 'File A', 'File B',
                'Total Records A', 'Total Records B', 'Matched Records',
                'Only in File A', 'Only in File B', 'Match Rate (%)',
                'Processing Date', 'Status'
            ],
            'Value': [
                session.id, session.config.name,
                session.file_a_name or 'N/A', session.file_b_name or 'N/A',
                session.total_a, session.total_b, session.matched,
                session.only_a, session.only_b,
                f"{(session.matched / max(session.total_a, 1) * 100):.2f}%",
                session.finished_at.strftime('%Y-%m-%d %H:%M:%S') if session.finished_at else 'N/A',
                session.get_status_display()
            ]
        }
        df = pd.DataFrame(data)
        return ExcelExporter._create_excel_response(df, f'summary_session_{session.id}.xlsx')


class ReconciliationResultViewSet(viewsets.ModelViewSet):
    queryset = ReconciliationResult.objects.all()
    serializer_class = ReconciliationResultSerializer
    filterset_fields = ['session', 'status']
    search_fields = ['match_key']
    ordering = ['-created_at']


@extend_schema(request=BulkConfigSerializer, responses={201: ReconciliationConfigSerializer})
@api_view(['POST'])
def bulk_configure(request):
    serializer = BulkConfigSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    with transaction.atomic():
        config = ReconciliationConfig.objects.create(
            name=data['config_name'],
            description=data.get('description', '')
        )

        field_objects = []
        for i, field_data in enumerate(data['fields']):
            field = ReconciliationField.objects.create(
                config=config,
                field_name=field_data['field_name'],
                data_type=field_data.get('data_type', 'string'),
                sequence=i + 1
            )
            field_objects.append(field)

            if field_data.get('excel_column_a'):
                FieldMapping.objects.create(
                    config=config, field=field,
                    file_type='A', excel_column=field_data['excel_column_a']
                )
            if field_data.get('excel_column_b'):
                FieldMapping.objects.create(
                    config=config, field=field,
                    file_type='B', excel_column=field_data['excel_column_b']
                )

        matching_fields = data.get('matching_fields', [])
        for field_name in matching_fields:
            field = ReconciliationField.objects.filter(
                config=config, field_name=field_name
            ).first()
            if field:
                mapping_a = FieldMapping.objects.filter(
                    config=config, field=field, file_type='A'
                ).first()
                mapping_b = FieldMapping.objects.filter(
                    config=config, field=field, file_type='B'
                ).first()
                if mapping_a and mapping_b:
                    ReconciliationRule.objects.create(
                        config=config,
                        left_field=mapping_a, right_field=mapping_b,
                        operator='=', sequence=1
                    )

    return Response(
        ReconciliationConfigSerializer(config).data,
        status=status.HTTP_201_CREATED
    )


@extend_schema(request=ReconcileSerializer, responses={201: ReconciliationSessionSerializer})
@api_view(['POST'])
def run_reconciliation(request):
    serializer = ReconcileSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    config = get_object_or_404(ReconciliationConfig, id=data['config_id'])
    file_a = data['file_a']
    file_b = data['file_b']

    parser = ExcelParser()
    if not parser.validate_excel_file(file_a):
        return Response({'error': 'File A is not a valid Excel file'}, status=400)
    if not parser.validate_excel_file(file_b):
        return Response({'error': 'File B is not a valid Excel file'}, status=400)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_a_path = default_storage.save(
        f'reconcile/file_a_{timestamp}_{file_a.name}', ContentFile(file_a.read())
    )
    file_b_path = default_storage.save(
        f'reconcile/file_b_{timestamp}_{file_b.name}', ContentFile(file_b.read())
    )

    mappings_a = FieldMapping.objects.filter(config=config, file_type='A')
    mappings_b = FieldMapping.objects.filter(config=config, file_type='B')
    mapping_a_dict = {m.excel_column: m.field.field_name for m in mappings_a}
    mapping_b_dict = {m.excel_column: m.field.field_name for m in mappings_b}
    all_fields = [f.field_name for f in config.fields.all()]

    rules = config.rules.all()
    matching_fields = []
    for rule in rules:
        if rule.left_field.field.field_name == rule.right_field.field.field_name:
            matching_fields.append(rule.left_field.field.field_name)

    if not matching_fields:
        return Response({'error': 'No matching rules configured'}, status=400)

    session = ReconciliationSession.objects.create(
        config=config,
        file_a_path=file_a_path, file_b_path=file_b_path,
        file_a_name=data['file_a'].name, file_b_name=data['file_b'].name,
        status='processing'
    )

    service = ReconciliationService(
        config_id=config.id, matching_fields=matching_fields,
        field_mapping_a=mapping_a_dict, field_mapping_b=mapping_b_dict,
        all_fields=all_fields
    )

    try:
        with default_storage.open(file_a_path, 'rb') as f_a, \
             default_storage.open(file_b_path, 'rb') as f_b:
            temp_file_a = SimpleUploadedFile(
                data['file_a'].name, f_a.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            temp_file_b = SimpleUploadedFile(
                data['file_b'].name, f_b.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            results = service.process_files(temp_file_a, temp_file_b)

        if results.get('status') == 'failed':
            session.status = 'failed'
            session.error_message = results.get('error_message')
            session.save()
            return Response(
                {'error': results.get('error_message')},
                status=status.HTTP_400_BAD_REQUEST
            )

        session.status = 'completed'
        session.total_a = results.get('total_records_a', 0)
        session.total_b = results.get('total_records_b', 0)
        session.matched = results.get('matched_count', 0)
        session.only_a = results.get('only_a_count', 0)
        session.only_b = results.get('only_b_count', 0)
        session.finished_at = datetime.now()
        session.save()

        service.save_results(session.id, results)

        return Response(
            ReconciliationSessionSerializer(session).data,
            status=status.HTTP_201_CREATED
        )
    except Exception as e:
        session.status = 'failed'
        session.error_message = str(e)
        session.save()
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(request=None, responses={200: dict})
@api_view(['GET'])
def api_overview(request):
    return Response({
        'recon_system_api': 'Reconciliation System REST API',
        'version': '1.0.0',
        'endpoints': {
            'configs': '/api/configs/',
            'fields': '/api/fields/',
            'mappings': '/api/mappings/',
            'rules': '/api/rules/',
            'sessions': '/api/sessions/',
            'results': '/api/results/',
            'reconcile': '/api/reconcile/',
            'bulk_configure': '/api/bulk-configure/',
            'schema': '/api/schema/',
            'docs': '/api/docs/',
        }
    })
