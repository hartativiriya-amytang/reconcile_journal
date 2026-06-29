from typing import Dict, List, Any, Tuple
import pandas as pd
from django.core.files.uploadedfile import UploadedFile
from .excel_parser import ExcelParser
from .rule_engine import RuleEngine
import json


class ReconciliationService:
    """Main reconciliation service"""
    
    def __init__(self, config_id: int, matching_fields: List[str], field_mapping: Dict[str, str]):
        """
        Initialize reconciliation service
        
        Args:
            config_id: Configuration ID
            matching_fields: List of field names to use for matching
            field_mapping: Mapping of Excel columns to system fields
        """
        self.config_id = config_id
        self.matching_fields = matching_fields
        self.field_mapping = field_mapping
        self.parser = ExcelParser()
        self.rule_engine = RuleEngine(matching_fields)
        
    def process_files(self, file_a: UploadedFile, file_b: UploadedFile) -> Dict:
        """Process two Excel files and perform reconciliation"""
        import pandas as pd
        
        try:
            # Validate files
            if not self.parser.validate_excel_file(file_a):
                raise ValueError("File A is not a valid Excel file")
            if not self.parser.validate_excel_file(file_b):
                raise ValueError("File B is not a valid Excel file")
            
            # Read Excel files
            df_a = self.parser.read_excel_file(file_a)
            df_b = self.parser.read_excel_file(file_b)
            
            # Map columns
            mapped_df_a = self.parser.map_columns(df_a, self.field_mapping)
            mapped_df_b = self.parser.map_columns(df_b, self.field_mapping)
            
            # Clean data: remove rows with empty matching fields
            for field in self.matching_fields:
                if field in mapped_df_a.columns:
                    mapped_df_a = mapped_df_a[mapped_df_a[field].notna()]
                if field in mapped_df_b.columns:
                    mapped_df_b = mapped_df_b[mapped_df_b[field].notna()]
            
            # Convert to dictionaries
            data_a = mapped_df_a.to_dict('records')
            data_b = mapped_df_b.to_dict('records')
            
            # Perform reconciliation
            matched, only_a, only_b = self.rule_engine.reconcile_data(data_a, data_b)
            
            # Prepare results
            results = {
                'config_id': self.config_id,
                'total_records_a': len(data_a),
                'total_records_b': len(data_b),
                'matched_count': len(matched),
                'only_a_count': len(only_a),
                'only_b_count': len(only_b),
                'matched_data': matched,
                'only_a_data': only_a,
                'only_b_data': only_b,
                'status': 'completed'
            }
            
            return results
            
        except Exception as e:
            return {
                'status': 'failed',
                'error_message': str(e)
            }
    
    def save_results(self, session_id: int, results: Dict) -> None:
        """Save reconciliation results to database"""
        from reconcile.models import ReconciliationResult
        
        # Save matched results
        for item in results.get('matched_data', []):
            ReconciliationResult.objects.create(
                session_id=session_id,
                status='match',
                file_a_data=item.get('file_a_data', {}),
                file_b_data=item.get('file_b_data', {}),
                match_key=self.rule_engine.generate_match_key(item.get('file_a_data', {}))
            )
        
        # Save only_a results
        for item in results.get('only_a_data', []):
            ReconciliationResult.objects.create(
                session_id=session_id,
                status='only_a',
                file_a_data=item.get('file_a_data', {}),
                file_b_data={},
                match_key=self.rule_engine.generate_match_key(item.get('file_a_data', {}))
            )
        
        # Save only_b results
        for item in results.get('only_b_data', []):
            ReconciliationResult.objects.create(
                session_id=session_id,
                status='only_b',
                file_a_data={},
                file_b_data=item.get('file_b_data', {}),
                match_key=self.rule_engine.generate_match_key(item.get('file_b_data', {}))
            )