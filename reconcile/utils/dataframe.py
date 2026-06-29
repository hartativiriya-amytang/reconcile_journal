import pandas as pd
from typing import Dict, List, Any, Optional
import json


class DataFrameUtils:
    """Utility class for DataFrame operations"""
    
    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Clean DataFrame by removing empty rows and trimming whitespace"""
        # Remove rows where all values are NaN/empty
        df = df.dropna(how='all')
        
        # Trim whitespace from string columns
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.strip()
        
        # Replace empty strings with NaN
        df = df.replace(r'^\s*$', pd.NA, regex=True)
        
        return df
    
    @staticmethod
    def validate_headers(df: pd.DataFrame, expected_headers: List[str]) -> bool:
        """Validate that DataFrame has expected headers"""
        actual_headers = df.columns.tolist()
        return all(header in actual_headers for header in expected_headers)
    
    @staticmethod
    def get_missing_headers(df: pd.DataFrame, expected_headers: List[str]) -> List[str]:
        """Get missing headers from DataFrame"""
        actual_headers = df.columns.tolist()
        return [header for header in expected_headers if header not in actual_headers]
    
    @staticmethod
    def convert_to_serializable(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert DataFrame to JSON-serializable list of dictionaries"""
        # Handle NaN values
        df = df.fillna('')
        
        # Convert to list of dictionaries
        records = df.to_dict('records')
        
        # Ensure all values are JSON serializable
        for record in records:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = ''
                elif isinstance(value, (pd.Timestamp, pd.DatetimeIndex)):
                    record[key] = value.isoformat()
                elif isinstance(value, (pd.Series, pd.DataFrame)):
                    record[key] = value.tolist()
        
        return records
    
    @staticmethod
    def merge_dataframes(df_a: pd.DataFrame, df_b: pd.DataFrame, on: List[str]) -> pd.DataFrame:
        """Merge two DataFrames for reconciliation"""
        # Add suffixes to distinguish source
        merged = pd.merge(
            df_a, df_b,
            on=on,
            how='outer',
            suffixes=('_A', '_B'),
            indicator=True
        )
        
        # Add match status
        merged['_match_status'] = merged['_merge'].map({
            'both': 'MATCH',
            'left_only': 'ONLY_FILE_A',
            'right_only': 'ONLY_FILE_B'
        })
        
        return merged
    
    @staticmethod
    def get_match_summary(df: pd.DataFrame) -> Dict[str, int]:
        """Get summary of match status"""
        if '_match_status' not in df.columns:
            return {'matched': 0, 'only_a': 0, 'only_b': 0}
        
        summary = df['_match_status'].value_counts().to_dict()
        return {
            'matched': summary.get('MATCH', 0),
            'only_a': summary.get('ONLY_FILE_A', 0),
            'only_b': summary.get('ONLY_FILE_B', 0)
        }