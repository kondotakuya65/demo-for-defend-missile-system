"""
Metrics Export Utility
"""

import json
import csv
import os
import numpy as np
from datetime import datetime
from typing import Dict, List, Any


class MetricsExporter:
    """Export simulation metrics to CSV/JSON"""
    
    @staticmethod
    def _convert_to_serializable(obj: Any) -> Any:
        """Convert numpy types and other non-serializable types to native Python types"""
        if isinstance(obj, (np.integer, np.floating)):
            return float(obj) if isinstance(obj, np.floating) else int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: MetricsExporter._convert_to_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [MetricsExporter._convert_to_serializable(item) for item in obj]
        elif isinstance(obj, set):
            return list(obj)
        else:
            return obj
    
    @staticmethod
    def export_json(metrics: Dict, filepath: str = None):
        """Export metrics to JSON file"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"metrics_export_{timestamp}.json"
        
        # Convert numpy types to native Python types
        serializable_metrics = MetricsExporter._convert_to_serializable(metrics)
        
        # Prepare export data
        export_data = {
            "export_time": datetime.now().isoformat(),
            "metrics": serializable_metrics
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    @staticmethod
    def export_csv(metrics: Dict, filepath: str = None):
        """Export metrics to CSV file"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"metrics_export_{timestamp}.csv"
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(["Metric", "Old Algorithm", "New Algorithm"])
            
            # Write CPU usage
            writer.writerow(["CPU Usage (%)", 
                           metrics.get('old', {}).get('cpu_usage', 0),
                           metrics.get('new', {}).get('cpu_usage', 0)])
            
            # Write success rate
            writer.writerow(["Success Rate (%)",
                           metrics.get('old', {}).get('success_rate', 0),
                           metrics.get('new', {}).get('success_rate', 0)])
            
            # Write interceptors launched
            writer.writerow(["Interceptors Launched",
                           metrics.get('old', {}).get('interceptors_launched', 0),
                           metrics.get('new', {}).get('interceptors_launched', 0)])
            
            # Write total response time
            writer.writerow(["Total Response Time (ms)",
                           metrics.get('old', {}).get('total_response_time', 0),
                           metrics.get('new', {}).get('total_response_time', 0)])
            
            # Write phase-specific response times
            writer.writerow([])  # Empty row
            writer.writerow(["Phase Response Times (ms)", "Old Algorithm", "New Algorithm"])
            
            for phase in ["Tracing", "Warning", "Destroy"]:
                old_times = metrics.get('old', {}).get('response_times', {}).get(phase, 0)
                new_times = metrics.get('new', {}).get('response_times', {}).get(phase, 0)
                writer.writerow([f"{phase} Phase", old_times, new_times])
            
            # Write phase statistics
            writer.writerow([])  # Empty row
            writer.writerow(["Phase Statistics", "Old Algorithm", "New Algorithm"])
            
            for phase in ["Tracing", "Warning", "Destroy"]:
                old_active = metrics.get('old', {}).get('phase_stats', {}).get(phase, {}).get('active', 0)
                new_active = metrics.get('new', {}).get('phase_stats', {}).get(phase, {}).get('active', 0)
                writer.writerow([f"{phase} Active", old_active, new_active])
        
        return filepath

