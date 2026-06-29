import pandas as pd
from io import BytesIO
from django.http import HttpResponse
from typing import List, Dict, Any
from datetime import datetime


class ExcelExporter:
    """Service for exporting reconciliation results to Excel"""
    
    @staticmethod
    def export_matched_data(results: List[Dict[str, Any]], fields: List[str]) -> HttpResponse:
        """Export matched data to Excel"""
        data = []
        for item in results:
            row = {
                'Status': 'MATCH',
                **{f'File_A_{field}': item.get('file_a_data', {}).get(field, '') for field in fields},
                **{f'File_B_{field}': item.get('file_b_data', {}).get(field, '') for field in fields}
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        return ExcelExporter._create_excel_response(df, 'matched_data.xlsx')
    
    @staticmethod
    def export_unmatched_data(only_a: List[Dict[str, Any]], only_b: List[Dict[str, Any]], fields: List[str]) -> HttpResponse:
        """Export unmatched data to Excel (separate sheets or separate files)"""
        # For simplicity, we'll export to separate sheets in one file
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Only File A data
            if only_a:
                data_a = []
                for item in only_a:
                    row = {
                        'Status': 'ONLY_FILE_A',
                        **{field: item.get('file_a_data', {}).get(field, '') for field in fields}
                    }
                    data_a.append(row)
                df_a = pd.DataFrame(data_a)
                df_a.to_excel(writer, sheet_name='Only_File_A', index=False)
            
            # Only File B data
            if only_b:
                data_b = []
                for item in only_b:
                    row = {
                        'Status': 'ONLY_FILE_B',
                        **{field: item.get('file_b_data', {}).get(field, '') for field in fields}
                    }
                    data_b.append(row)
                df_b = pd.DataFrame(data_b)
                df_b.to_excel(writer, sheet_name='Only_File_B', index=False)
            
            # Summary sheet
            summary_data = {
                'Metric': ['Total Records A', 'Total Records B', 'Matched', 'Only A', 'Only B'],
                'Count': [
                    len(only_a) + len([item for item in only_a if item.get('file_a_data')]),  # This needs to be calculated properly
                    len(only_b) + len([item for item in only_b if item.get('file_b_data')]),
                    len([item for item in only_a if item.get('matched')]),  # This needs proper calculation
                    len(only_a),
                    len(only_b)
                ]
            }
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=unmatched_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        return response
    
    @staticmethod
    def _create_excel_response(df: pd.DataFrame, filename: str) -> HttpResponse:
        """Create HTTP response with Excel file"""
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Data', index=False)
        
        output.seek(0)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    
    @staticmethod
    def export_summary(session_data: Dict) -> HttpResponse:
        """Export summary report"""
        data = {
            'Metric': [
                'Total Records in File A',
                'Total Records in File B',
                'Matched Records',
                'Only in File A',
                'Only in File B',
                'Match Rate (%)',
                'Processing Date'
            ],
            'Value': [
                session_data.get('total_records_a', 0),
                session_data.get('total_records_b', 0),
                session_data.get('matched_count', 0),
                session_data.get('only_a_count', 0),
                session_data.get('only_b_count', 0),
                f"{(session_data.get('matched_count', 0) / max(session_data.get('total_records_a', 1), 1) * 100):.2f}%",
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ]
        }
        
        df = pd.DataFrame(data)
        return ExcelExporter._create_excel_response(df, f'summary_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')