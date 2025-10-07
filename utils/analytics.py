"""
Analytics and Statistics Module
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd


class Analytics:
    """Track and analyze steganography operations"""
    
    ANALYTICS_FILE = Path("analytics.json")
    
    @staticmethod
    def log_operation(operation_type: str, details: Dict):
        """Log an operation"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': operation_type,
            'details': details
        }
        
        # Load existing logs
        logs = Analytics.load_logs()
        logs.append(log_entry)
        
        # Save
        with open(Analytics.ANALYTICS_FILE, 'w') as f:
            json.dump(logs, f, indent=2)
    
    @staticmethod
    def load_logs() -> List[Dict]:
        """Load all logs"""
        if Analytics.ANALYTICS_FILE.exists():
            with open(Analytics.ANALYTICS_FILE, 'r') as f:
                return json.load(f)
        return []
    
    @staticmethod
    def get_statistics() -> Dict:
        """Calculate statistics from logs"""
        logs = Analytics.load_logs()
        
        if not logs:
            return {
                'total_operations': 0,
                'hide_operations': 0,
                'reveal_operations': 0,
                'total_data_hidden_mb': 0,
                'avg_payload_size_kb': 0,
                'recent_operations': []
            }
        
        df = pd.DataFrame(logs)
        
        hide_ops = df[df['type'] == 'hide']
        reveal_ops = df[df['type'] == 'reveal']
        
        total_data_mb = 0
        if len(hide_ops) > 0:
            total_data_mb = sum([op.get('payload_kb', 0) for op in hide_ops['details']]) / 1024
        
        avg_payload_kb = 0
        if len(hide_ops) > 0:
            avg_payload_kb = sum([op.get('payload_kb', 0) for op in hide_ops['details']]) / len(hide_ops)
        
        return {
            'total_operations': len(logs),
            'hide_operations': len(hide_ops),
            'reveal_operations': len(reveal_ops),
            'total_data_hidden_mb': round(total_data_mb, 2),
            'avg_payload_size_kb': round(avg_payload_kb, 2),
            'recent_operations': logs[-10:][::-1]
        }
