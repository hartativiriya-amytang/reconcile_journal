from typing import List, Dict, Any, Tuple
import hashlib
import json
import pandas as pd


class RuleEngine:
    """Engine for evaluating reconciliation rules"""
    
    def __init__(self, matching_fields: List[str]):
        """
        Initialize rule engine with matching fields
        
        Args:
            matching_fields: List of field names to use for matching
        """
        self.matching_fields = matching_fields
        
    def generate_match_key(self, record: Dict[str, Any]) -> str:
        """Generate a unique key for matching based on matching fields"""
        key_parts = []
        for field in self.matching_fields:
            value = record.get(field, '')
            # Handle NaN values
            if pd.isna(value):
                value = 'NULL'
            else:
                value = str(value).strip().lower()
            key_parts.append(f"{field}:{value}")
        
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def is_match(self, record_a: Dict[str, Any], record_b: Dict[str, Any]) -> bool:
        """
        Check if two records match based on all matching criteria
        
        All fields must match (AND operator)
        """
        for field in self.matching_fields:
            val_a = record_a.get(field)
            val_b = record_b.get(field)
            
            # Handle None/NaN values
            if pd.isna(val_a) or pd.isna(val_b):
                if pd.isna(val_a) != pd.isna(val_b):
                    return False
            else:
                # Convert to string for comparison
                str_a = str(val_a).strip().lower()
                str_b = str(val_b).strip().lower()
                if str_a != str_b:
                    return False
        
        return True
    
    def reconcile_data(self, data_a: List[Dict[str, Any]], data_b: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Perform reconciliation between two datasets
        
        Returns:
            Tuple of (matched, only_a, only_b)
        """
        matched = []
        only_a = []
        only_b = []
        
        # Generate match keys for both datasets
        data_a_with_keys = []
        for record in data_a:
            key = self.generate_match_key(record)
            data_a_with_keys.append({**record, '_match_key': key})
        
        data_b_with_keys = []
        for record in data_b:
            key = self.generate_match_key(record)
            data_b_with_keys.append({**record, '_match_key': key})
        
        # Create lookup dictionaries
        b_lookup = {record['_match_key']: record for record in data_b_with_keys}
        a_lookup = {record['_match_key']: record for record in data_a_with_keys}
        
        # Find matches
        a_keys = set(a_lookup.keys())
        b_keys = set(b_lookup.keys())
        
        matched_keys = a_keys.intersection(b_keys)
        only_a_keys = a_keys - b_keys
        only_b_keys = b_keys - a_keys
        
        # Build result lists
        for key in matched_keys:
            matched.append({
                'file_a_data': {k: v for k, v in a_lookup[key].items() if k != '_match_key'},
                'file_b_data': {k: v for k, v in b_lookup[key].items() if k != '_match_key'},
                'status': 'match'
            })
        
        for key in only_a_keys:
            only_a.append({
                'file_a_data': {k: v for k, v in a_lookup[key].items() if k != '_match_key'},
                'file_b_data': {},
                'status': 'only_a'
            })
        
        for key in only_b_keys:
            only_b.append({
                'file_b_data': {k: v for k, v in b_lookup[key].items() if k != '_match_key'},
                'file_a_data': {},
                'status': 'only_b'
            })
        
        return matched, only_a, only_b