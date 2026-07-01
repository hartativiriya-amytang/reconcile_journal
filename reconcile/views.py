from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import datetime
import pandas as pd
import json
import os

from .models import (
    ReconciliationConfig, ReconciliationField, FieldMapping, 
    ReconciliationRule, ReconciliationSession, ReconciliationResult
)
from .services.reconciliation import ReconciliationService
from .services.export_excel import ExcelExporter
from .services.excel_parser import ExcelParser


def index(request):
    """Home page with list of reconciliation sessions"""
    try:
        sessions = ReconciliationSession.objects.all().order_by('-created_at')[:20]
        return render(request, 'reconcile/index.html', {'sessions': sessions})
    except Exception as e:
        messages.error(request, f'Error loading sessions: {str(e)}')
        return render(request, 'reconcile/index.html', {'sessions': []})


def configure_fields(request):
    """Configure reconciliation fields and matching criteria"""
    config = None
    
    if request.method == 'POST':
        try:
            # Get or create config
            config_id = request.POST.get('config_id')
            if config_id:
                config = get_object_or_404(ReconciliationConfig, id=config_id)
            else:
                config = ReconciliationConfig.objects.create(
                    name=request.POST.get('config_name', f"Config_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                    description=request.POST.get('description', '')
                )
            
            # Clear existing data
            config.fields.all().delete()
            config.mappings.all().delete()
            config.rules.all().delete()
            
            # Process fields
            field_names = request.POST.getlist('field_name[]')
            data_types = request.POST.getlist('data_type[]')
            excel_columns_a = request.POST.getlist('excel_column_a[]')
            excel_columns_b = request.POST.getlist('excel_column_b[]')
            is_matching = request.POST.getlist('is_matching[]')
            
            # Validate
            if len(field_names) > 12:
                messages.error(request, 'Maximum 12 fields allowed')
                return redirect('configure_fields')
            
            if len(field_names) < 1:
                messages.error(request, 'Minimum 1 field required')
                return redirect('configure_fields')
            
            # Check for duplicate field names
            if len(set(field_names)) != len(field_names):
                messages.error(request, 'Duplicate field names are not allowed')
                return redirect('configure_fields')
            
            # Create fields and mappings
            field_objects = []
            matching_fields = []
            
            for i, field_name in enumerate(field_names):
                if not field_name:  # Skip empty
                    continue
                    
                # Create field
                field = ReconciliationField.objects.create(
                    config=config,
                    field_name=field_name,
                    data_type=data_types[i] if i < len(data_types) else 'string',
                    sequence=i + 1
                )
                field_objects.append(field)
                
                # Create mapping for File A
                if i < len(excel_columns_a) and excel_columns_a[i]:
                    mapping_a = FieldMapping.objects.create(
                        config=config,
                        field=field,
                        file_type='A',
                        excel_column=excel_columns_a[i]
                    )
                
                # Create mapping for File B
                if i < len(excel_columns_b) and excel_columns_b[i]:
                    mapping_b = FieldMapping.objects.create(
                        config=config,
                        field=field,
                        file_type='B',
                        excel_column=excel_columns_b[i]
                    )
                
                # Check if this field is a matching criteria
                if str(i) in is_matching:
                    matching_fields.append(field_name)
            
            # Create matching rules
            if matching_fields:
                for field_name in matching_fields:
                    field = ReconciliationField.objects.filter(
                        config=config, 
                        field_name=field_name
                    ).first()
                    
                    if field:
                        mapping_a = FieldMapping.objects.filter(
                            config=config,
                            field=field,
                            file_type='A'
                        ).first()
                        
                        mapping_b = FieldMapping.objects.filter(
                            config=config,
                            field=field,
                            file_type='B'
                        ).first()
                        
                        if mapping_a and mapping_b:
                            ReconciliationRule.objects.create(
                                config=config,
                                left_field=mapping_a,
                                right_field=mapping_b,
                                operator='=',
                                sequence=len(matching_fields) + 1
                            )
            
            # Store in session
            request.session['config_id'] = config.id
            request.session['matching_fields'] = matching_fields
            
            messages.success(request, 'Configuration saved successfully!')
            return redirect('upload_files')
            
        except Exception as e:
            messages.error(request, f'Error saving configuration: {str(e)}')
            return redirect('configure_fields')
    
    # GET request
    data_type_options = [
        ('string', 'String'),
        ('number', 'Number'),
        ('date', 'Date'),
    ]
    
    return render(request, 'reconcile/configure_fields.html', {
        'data_type_options': data_type_options,
        'config': config
    })


def upload_files(request):
    """Upload Excel files for reconciliation"""
    config_id = request.session.get('config_id')
    if not config_id:
        messages.error(request, 'Please configure fields first')
        return redirect('configure_fields')
    
    config = get_object_or_404(ReconciliationConfig, id=config_id)
    matching_fields = request.session.get('matching_fields', [])
    
    if not matching_fields:
        messages.error(request, 'Please select matching criteria')
        return redirect('configure_fields')
    
    if request.method == 'POST':
        try:
            file_a = request.FILES.get('file_a')
            file_b = request.FILES.get('file_b')
            
            if not file_a or not file_b:
                messages.error(request, 'Please upload both files')
                return redirect('upload_files')
            
            # Validate files
            parser = ExcelParser()
            if not parser.validate_excel_file(file_a):
                messages.error(request, 'File A is not a valid Excel file')
                return redirect('upload_files')
            if not parser.validate_excel_file(file_b):
                messages.error(request, 'File B is not a valid Excel file')
                return redirect('upload_files')
            
            # Save uploaded files
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_a_path = default_storage.save(
                f'reconcile/file_a_{timestamp}_{file_a.name}',
                ContentFile(file_a.read())
            )
            file_b_path = default_storage.save(
                f'reconcile/file_b_{timestamp}_{file_b.name}',
                ContentFile(file_b.read())
            )
            
            # Create session
            session = ReconciliationSession.objects.create(
                config=config,
                file_a_path=file_a_path,
                file_b_path=file_b_path,
                file_a_name=file_a.name,
                file_b_name=file_b.name,
                status='processing'
            )
            
            # Get field mappings
            mappings_a = FieldMapping.objects.filter(config=config, file_type='A')
            mappings_b = FieldMapping.objects.filter(config=config, file_type='B')
            
            # Build mapping dictionaries
            mapping_a_dict = {m.excel_column: m.field.field_name for m in mappings_a}
            mapping_b_dict = {m.excel_column: m.field.field_name for m in mappings_b}
            
            # Get all field names
            fields = config.fields.all()
            all_field_names = [f.field_name for f in fields]
            
            # Process reconciliation
            service = ReconciliationService(
                config_id=config.id,
                matching_fields=matching_fields,
                field_mapping_a=mapping_a_dict,
                field_mapping_b=mapping_b_dict,
                all_fields=all_field_names
            )
            
            # Re-read files for processing
            with default_storage.open(file_a_path, 'rb') as f_a, default_storage.open(file_b_path, 'rb') as f_b:
                temp_file_a = SimpleUploadedFile(
                    file_a.name, 
                    f_a.read(), 
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                temp_file_b = SimpleUploadedFile(
                    file_b.name, 
                    f_b.read(), 
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                results = service.process_files(temp_file_a, temp_file_b)
            
            if results.get('status') == 'failed':
                session.status = 'failed'
                session.error_message = results.get('error_message')
                session.save()
                messages.error(request, f'Reconciliation failed: {results.get("error_message")}')
                return redirect('upload_files')
            
            # Update session with results
            session.status = 'completed'
            session.total_a = results.get('total_records_a', 0)
            session.total_b = results.get('total_records_b', 0)
            session.matched = results.get('matched_count', 0)
            session.only_a = results.get('only_a_count', 0)
            session.only_b = results.get('only_b_count', 0)
            session.finished_at = datetime.now()
            session.save()
            
            # Save detailed results
            service.save_results(session.id, results)
            
            # Store session_id for downloading
            request.session['session_id'] = session.id
            
            messages.success(request, 'Reconciliation completed successfully!')
            return redirect('view_results', session_id=session.id)
            
        except Exception as e:
            messages.error(request, f'Error processing files: {str(e)}')
            return redirect('upload_files')
    
    # GET request
    fields = config.fields.all()
    mappings = FieldMapping.objects.filter(config=config)
    
    return render(request, 'reconcile/upload_files.html', {
        'config': config,
        'fields': fields,
        'mappings': mappings,
        'matching_fields': matching_fields
    })


def view_results(request, session_id):
    """View reconciliation results"""
    session = get_object_or_404(ReconciliationSession, id=session_id)
    results = session.results.all()
    
    # Get field names from config
    fields = session.config.fields.all()
    field_names = [f.field_name for f in fields]
    
    # Calculate match rate
    match_rate = 0
    if session.total_a > 0:
        match_rate = (session.matched / session.total_a) * 100
    
    return render(request, 'reconcile/view_results.html', {
        'session': session,
        'results': results,
        'field_names': field_names,
        'stats': {
            'total_records_a': session.total_a,
            'total_records_b': session.total_b,
            'matched': session.matched,
            'only_a': session.only_a,
            'only_b': session.only_b,
            'match_rate': match_rate
        }
    })


def download_matched(request, session_id):
    """Download matched data as Excel"""
    session = get_object_or_404(ReconciliationSession, id=session_id)
    results = session.results.filter(status='MATCH')
    
    if not results.exists():
        messages.error(request, 'No matched data found')
        return redirect('view_results', session_id=session_id)
    
    # Get field names
    fields = session.config.fields.all()
    field_names = [f.field_name for f in fields]
    
    # Convert to list of dicts
    data = []
    for result in results:
        row = {
            'Status': 'MATCH',
        }
        for field in field_names:
            row[f'File_A_{field}'] = result.file_a_data.get(field, '')
            row[f'File_B_{field}'] = result.file_b_data.get(field, '')
        data.append(row)
    
    # Export to Excel
    df = pd.DataFrame(data)
    return ExcelExporter._create_excel_response(df, f'matched_data_{session_id}.xlsx')


def download_unmatched(request, session_id):
    """Download unmatched data as Excel"""
    session = get_object_or_404(ReconciliationSession, id=session_id)
    only_a_results = session.results.filter(status='ONLY_A')
    only_b_results = session.results.filter(status='ONLY_B')
    
    if not only_a_results.exists() and not only_b_results.exists():
        messages.error(request, 'No unmatched data found')
        return redirect('view_results', session_id=session_id)
    
    # Get field names
    fields = session.config.fields.all()
    field_names = [f.field_name for f in fields]
    
    # Prepare data
    data_a = []
    for result in only_a_results:
        row = {
            'Status': 'ONLY_FILE_A',
        }
        for field in field_names:
            row[field] = result.file_a_data.get(field, '')
        data_a.append(row)
    
    data_b = []
    for result in only_b_results:
        row = {
            'Status': 'ONLY_FILE_B',
        }
        for field in field_names:
            row[field] = result.file_b_data.get(field, '')
        data_b.append(row)
    
    # Create Excel with multiple sheets
    from io import BytesIO
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if data_a:
            df_a = pd.DataFrame(data_a)
            df_a.to_excel(writer, sheet_name='Only_File_A', index=False)
        if data_b:
            df_b = pd.DataFrame(data_b)
            df_b.to_excel(writer, sheet_name='Only_File_B', index=False)
        
        # Summary
        summary_data = {
            'Metric': ['Only in File A', 'Only in File B'],
            'Count': [len(data_a), len(data_b)]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
    
    output.seek(0)
    response = HttpResponse(
        output.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename=unmatched_data_{session_id}.xlsx'
    return response


def download_summary(request, session_id):
    """Download summary report"""
    session = get_object_or_404(ReconciliationSession, id=session_id)
    
    data = {
        'Metric': [
            'Session ID',
            'Configuration',
            'File A',
            'File B',
            'Total Records A',
            'Total Records B',
            'Matched Records',
            'Only in File A',
            'Only in File B',
            'Match Rate (%)',
            'Processing Date',
            'Status'
        ],
        'Value': [
            session.id,
            session.config.name,
            session.file_a_name if session.file_a_name else 'N/A',
            session.file_b_name if session.file_b_name else 'N/A',
            session.total_a,
            session.total_b,
            session.matched,
            session.only_a,
            session.only_b,
            f"{(session.matched / max(session.total_a, 1) * 100):.2f}%",
            session.finished_at.strftime('%Y-%m-%d %H:%M:%S') if session.finished_at else 'N/A',
            session.get_status_display()
        ]
    }
    
    df = pd.DataFrame(data)
    return ExcelExporter._create_excel_response(df, f'summary_session_{session_id}.xlsx')


def get_config_status(request):
    """API endpoint to get configuration status"""
    config_id = request.session.get('config_id')
    matching_fields = request.session.get('matching_fields', [])
    
    return JsonResponse({
        'has_config': bool(config_id),
        'has_matching_fields': bool(matching_fields),
        'matching_fields_count': len(matching_fields)
    })