import pandas as pd
from io import BytesIO
from django.http import HttpResponse
from typing import List, Dict, Any
from datetime import datetime


class ExcelExporter:
    """Service for exporting reconciliation results to Excel"""
    
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