import pandas as pd
from django.core.files.uploadedfile import UploadedFile
from typing import Dict, List, Any, Optional
import re


class ExcelParser:
    """Service for parsing Excel files"""
    
    @staticmethod
    def validate_excel_file(file: UploadedFile) -> bool:
        """Validate if the file is a valid Excel file"""
        if not file:
            return False
        allowed_extensions = ['.xlsx', '.xls']
        file_name = file.name.lower()
        return any(file_name.endswith(ext) for ext in allowed_extensions)
    
    @staticmethod
    def read_excel_file(file: UploadedFile, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """Read Excel file and return DataFrame"""
        try:
            if sheet_name:
                df = pd.read_excel(file, sheet_name=sheet_name, dtype=str)
            else:
                df = pd.read_excel(file, dtype=str)
            
            # Clean data: trim whitespace, remove empty rows
            df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
            df = df.dropna(how='all')
            
            return df
        except Exception as e:
            raise ValueError(f"Failed to read Excel file: {str(e)}")
    
    @staticmethod
    def get_sheet_names(file: UploadedFile) -> List[str]:
        """Get all sheet names from Excel file"""
        try:
            excel_file = pd.ExcelFile(file)
            return excel_file.sheet_names
        except Exception as e:
            raise ValueError(f"Failed to read sheet names: {str(e)}")
    
    @staticmethod
    def map_columns(df: pd.DataFrame, field_mapping: Dict[str, str]) -> pd.DataFrame:
        """Map Excel columns to system fields"""
        # field_mapping: {'Excel Column': 'System Field'}
        mapped_df = pd.DataFrame()
        
        for excel_col, system_field in field_mapping.items():
            if excel_col in df.columns:
                mapped_df[system_field] = df[excel_col]
        
        return mapped_df
    
    @staticmethod
    def convert_data_types(df: pd.DataFrame, field_types: Dict[str, str]) -> pd.DataFrame:
        """Convert data types based on field configuration"""
        for field, data_type in field_types.items():
            if field in df.columns:
                try:
                    if data_type == 'number':
                        df[field] = pd.to_numeric(df[field], errors='coerce')
                    elif data_type == 'date':
                        df[field] = pd.to_datetime(df[field], errors='coerce')
                    elif data_type == 'datetime':
                        df[field] = pd.to_datetime(df[field], errors='coerce')
                    # string type stays as is
                except:
                    pass  # Keep original if conversion fails
        return df
    
    @staticmethod
    def clean_headers(headers: List[str]) -> List[str]:
        """Clean and normalize headers"""
        cleaned = []
        for header in headers:
            if pd.isna(header):
                continue
            header = str(header).strip()
            if header:
                cleaned.append(header)
        return cleaned