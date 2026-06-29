from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import os
from datetime import datetime

from .models import ReconciliationConfig, ReconciliationField, ReconciliationSession
from .services.reconciliation import ReconciliationService
from .services.export_excel import ExcelExporter
from .services.excel_parser import ExcelParser


from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import os
from datetime import datetime
import pandas as pd

from .models import ReconciliationConfig, ReconciliationField, ReconciliationSession
from .services.reconciliation import ReconciliationService
from .services.export_excel import ExcelExporter
from .services.excel_parser import ExcelParser


def index(request):
    """Home page with list of reconciliation sessions"""
    try:
        sessions = ReconciliationSession.objects.all()[:20]
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
                    name=request.POST.get('config_name', f"Config_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                )
            
            # Clear existing fields
            config.fields.all().delete()
            
            # Process fields
            field_codes = request.POST.getlist('field_code[]')
            field_names = request.POST.getlist('field_name[]')
            display_names = request.POST.getlist('display_name[]')
            data_types = request.POST.getlist('data_type[]')
            is_matching = request.POST.getlist('is_matching[]')
            
            if len(field_codes) > 12:
                messages.error(request, 'Maximum 12 fields allowed')
                return redirect('configure_fields')
            
            if len(field_codes) < 1:
                messages.error(request, 'Minimum 1 field required')
                return redirect('configure_fields')
            
            # Check for duplicate field names
            if len(set(field_names)) != len(field_names):
                messages.error(request, 'Duplicate field names are not allowed')
                return redirect('configure_fields')
            
            # Create fields
            matching_fields = []
            for i, field_code in enumerate(field_codes):
                if field_code:  # Skip empty
                    is_match = field_code in is_matching
                    field = ReconciliationField.objects.create(
                        config=config,
                        field_code=field_code,
                        field_name=field_names[i],
                        display_name=display_names[i],
                        data_type=data_types[i] if i < len(data_types) else 'string',
                        is_matching_criteria=is_match,
                        order=i
                    )
                    if is_match:
                        matching_fields.append(field.field_name)
            
            # Store matching fields in session for later use
            request.session['matching_fields'] = matching_fields
            request.session['config_id'] = config.id
            
            messages.success(request, 'Configuration saved successfully')
            return redirect('upload_files')
            
        except Exception as e:
            messages.error(request, f'Error saving configuration: {str(e)}')
            return redirect('configure_fields')
    
    # GET request - show configuration form
    field_options = [(chr(65+i), f"Field {chr(65+i)}") for i in range(12)]  # A to L
    data_type_options = [
        ('string', 'String'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('datetime', 'DateTime'),
    ]
    
    return render(request, 'reconcile/configure_fields.html', {
        'field_options': field_options,
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
            file_a_path = default_storage.save(
                f'reconcile/file_a_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{file_a.name}',
                ContentFile(file_a.read())
            )
            file_b_path = default_storage.save(
                f'reconcile/file_b_{datetime.now().strftime("%Y%m%d_%H%M%S")}_{file_b.name}',
                ContentFile(file_b.read())
            )
            
            # Create session
            session = ReconciliationSession.objects.create(
                config=config,
                file_a_name=file_a.name,
                file_b_name=file_b.name,
                file_a_path=file_a_path,
                file_b_path=file_b_path,
                status='processing'
            )
            
            # Get field mapping (for now, assume column headers match field names)
            fields = config.fields.all()
            field_mapping = {field.field_name: field.field_name for field in fields}
            
            # Process reconciliation
            service = ReconciliationService(
                config_id=config.id,
                matching_fields=matching_fields,
                field_mapping=field_mapping
            )
            
            # Need to re-read files since we saved them
            from django.core.files import File
            with default_storage.open(file_a_path, 'rb') as f_a, default_storage.open(file_b_path, 'rb') as f_b:
                # Create temporary UploadedFile objects
                from django.core.files.uploadedfile import SimpleUploadedFile
                
                # Read file content
                f_a.seek(0)
                f_b.seek(0)
                
                temp_file_a = SimpleUploadedFile(file_a.name, f_a.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                temp_file_b = SimpleUploadedFile(file_b.name, f_b.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                
                results = service.process_files(temp_file_a, temp_file_b)
            
            if results.get('status') == 'failed':
                session.status = 'failed'
                session.error_message = results.get('error_message')
                session.save()
                messages.error(request, f'Reconciliation failed: {results.get("error_message")}')
                return redirect('upload_files')
            
            # Update session with results
            session.status = 'completed'
            session.total_records_a = results.get('total_records_a', 0)
            session.total_records_b = results.get('total_records_b', 0)
            session.matched_count = results.get('matched_count', 0)
            session.only_a_count = results.get('only_a_count', 0)
            session.only_b_count = results.get('only_b_count', 0)
            session.completed_at = datetime.now()
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
    # Get field mapping for display
    fields = config.fields.all()
    
    return render(request, 'reconcile/upload_files.html', {
        'config': config,
        'fields': fields,
        'matching_fields': matching_fields
    })


def view_results(request, session_id):
    """View reconciliation results"""
    session = get_object_or_404(ReconciliationSession, id=session_id)
    results = session.results.all()
    
    # Get distinct field names from results
    field_names = []
    if results.exists():
        # Try to get fields from first result
        first_result = results.first()
        if first_result.file_a_data:
            field_names = list(first_result.file_a_data.keys())
        elif first_result.file_b_data:
            field_names = list(first_result.file_b_data.keys())
    
    return render(request, 'reconcile/view_results.html', {
        'session': session,
        'results': results,
        'field_names': field_names,
        'stats': {
            'total_records_a': session.total_records_a,
            'total_records_b': session.total_records_b,
            'matched': session.matched_count,
            'only_a': session.only_a_count,
            'only_b': session.only_b_count,
        }
    })


def download_matched(request, session_id):
    """Download matched data as Excel"""
    session = get_object_or_404(ReconciliationSession, id=session_id)
    results = session.results.filter(status='match')
    
    if not results.exists():
        messages.error(request, 'No matched data found')
        return redirect('view_results', session_id=session_id)
    
    # Get field names from results
    fields = []
    for result in results:
        if result.file_a_data:
            fields = list(result.file_a_data.keys())
            break
    
    # Convert to list of dicts
    data = []
    for result in results:
        row = {
            'Status': 'MATCH',
            **{f'File_A_{field}': result.file_a_data.get(field, '') for field in fields},
            **{f'File_B_{field}': result.file_b_data.get(field, '') for field in fields}
        }
        data.append(row)
    
    # Export to Excel
    return ExcelExporter._create_excel_response(pd.DataFrame(data), f'matched_data_{session_id}.xlsx')


def download_unmatched(request, session_id):
    """Download unmatched data as Excel"""
    session = get_object_or_404(ReconciliationSession, id=session_id)
    only_a_results = session.results.filter(status='only_a')
    only_b_results = session.results.filter(status='only_b')
    
    if not only_a_results.exists() and not only_b_results.exists():
        messages.error(request, 'No unmatched data found')
        return redirect('view_results', session_id=session_id)
    
    # Get field names
    fields = []
    if only_a_results.exists():
        fields = list(only_a_results.first().file_a_data.keys())
    elif only_b_results.exists():
        fields = list(only_b_results.first().file_b_data.keys())
    
    # Prepare data
    data_a = []
    for result in only_a_results:
        row = {
            'Status': 'ONLY_FILE_A',
            **{field: result.file_a_data.get(field, '') for field in fields}
        }
        data_a.append(row)
    
    data_b = []
    for result in only_b_results:
        row = {
            'Status': 'ONLY_FILE_B',
            **{field: result.file_b_data.get(field, '') for field in fields}
        }
        data_b.append(row)
    
    # Create Excel with multiple sheets
    import pandas as pd
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
            session.file_a_name,
            session.file_b_name,
            session.total_records_a,
            session.total_records_b,
            session.matched_count,
            session.only_a_count,
            session.only_b_count,
            f"{(session.matched_count / max(session.total_records_a, 1) * 100):.2f}%",
            session.completed_at.strftime('%Y-%m-%d %H:%M:%S') if session.completed_at else 'N/A',
            session.get_status_display()
        ]
    }
    
    import pandas as pd
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